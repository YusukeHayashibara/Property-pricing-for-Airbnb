import io

import pandas as pd
import pytest
from PIL import Image

from src.airbnb_photos import baixar_capa, baixar_capas, selecionar_anuncios


def jpeg(w, h):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), "red").save(buf, "JPEG")
    return buf.getvalue()


class Resposta:
    def __init__(self, status=200, content=b""):
        self.status_code, self.content = status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class Sessao:
    """Sessao falsa: url -> lista de respostas, consumidas em ordem. Sem rede."""

    def __init__(self, respostas):
        self.respostas = {u: list(r) for u, r in respostas.items()}
        self.chamadas = []

    def get(self, url, **kw):
        self.chamadas.append(url)
        fila = self.respostas[url]
        return fila.pop(0) if len(fila) > 1 else fila[0]


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr("src.airbnb_photos.time.sleep", lambda s: None)


@pytest.fixture
def listings():
    return pd.DataFrame(
        {
            "id": [30, 10, 20, 40, 50],
            "picture_url": ["u30", "u10", "u20", None, "u50"],
            "number_of_reviews": [25, 100, 5, 50, 30],
            "review_scores_rating": [4.5, 4.9, 4.8, 4.7, 3.9],
        }
    )


def test_selecao_primeiros_aplica_filtros_e_ordena_por_id(listings):
    # 20: poucas reviews | 40: sem foto | 50: nota baixa
    assert selecionar_anuncios(listings, n=10) == [10, 30]
    assert selecionar_anuncios(listings, n=1) == [10]


def test_selecao_aleatoria_reprodutivel(listings):
    a = selecionar_anuncios(listings, min_reviews=0, min_rating=0, n=2, amostra="aleatoria", seed=1)
    b = selecionar_anuncios(listings, min_reviews=0, min_rating=0, n=2, amostra="aleatoria", seed=1)
    assert a == b and len(a) == 2


def test_selecao_amostra_invalida(listings):
    with pytest.raises(ValueError):
        selecionar_anuncios(listings, n=1, amostra="outra")


@pytest.mark.parametrize("tam, esperado", [((1024, 682), (512, 341)), ((600, 800), (384, 512))])
def test_redimensiona_para_caber_em_512(tmp_path, tam, esperado):
    s = Sessao({"u": [Resposta(content=jpeg(*tam))]})
    r = baixar_capa(7, "u", tmp_path, sessao=s)
    assert r["status"] == "ok"
    assert Image.open(tmp_path / "7.jpg").size == esperado
    assert not list(tmp_path.glob("*.part"))


def test_nao_baixa_de_novo(tmp_path):
    (tmp_path / "7.jpg").write_bytes(jpeg(10, 10))
    s = Sessao({"u": [Resposta(content=jpeg(100, 100))]})
    assert baixar_capa(7, "u", tmp_path, sessao=s)["status"] == "existente"
    assert s.chamadas == []
    assert baixar_capa(7, "u", tmp_path, sobrescrever=True, sessao=s)["status"] == "ok"


def test_404_nao_repete(tmp_path):
    s = Sessao({"u": [Resposta(404)]})
    r = baixar_capa(7, "u", tmp_path, sessao=s)
    assert (r["status"], r["erro"]) == ("falhou", "HTTP 404")
    assert len(s.chamadas) == 1 and not (tmp_path / "7.jpg").exists()


def test_erro_transitorio_tenta_de_novo(tmp_path):
    s = Sessao({"u": [Resposta(503), Resposta(content=jpeg(50, 50))]})
    assert baixar_capa(7, "u", tmp_path, sessao=s)["status"] == "ok"
    assert len(s.chamadas) == 2


def test_imagem_invalida_falha_sem_arquivo(tmp_path):
    s = Sessao({"u": [Resposta(content=b"<html>nao e imagem</html>")]})
    r = baixar_capa(7, "u", tmp_path, sessao=s)
    assert r["status"] == "falhou"
    assert not list(tmp_path.iterdir())


def test_lote_por_lista_de_ids(tmp_path, listings):
    s = Sessao({"u10": [Resposta(content=jpeg(20, 20))], "u30": [Resposta(404)]})
    rel = baixar_capas([10, 30, 999, 10], listings, tmp_path, workers=2, sessao=s)
    assert rel.set_index("id")["status"].to_dict() == {10: "ok", 30: "falhou", 999: "sem_url"}

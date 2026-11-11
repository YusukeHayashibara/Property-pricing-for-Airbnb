import pandas as pd
import pytest
import requests

from src.streetview import (
    AcessoNegado,
    ChaveAusente,
    baixar_streetview,
    carregar_chave,
    coordenadas,
    distancia_m,
    imagens_hoje,
)

CHAVE = "chave-secreta-123"
META_OK = {
    "status": "OK",
    "pano_id": "P1",
    "location": {"lat": -23.5741, "lng": -46.6398},
    "date": "2024-05",
    "copyright": "© Google",
}


class Resposta:
    def __init__(self, status=200, json=None, content=b"jpg", tipo="image/jpeg"):
        self.status_code, self._json, self.content = status, json, content
        self.headers = {"content-type": tipo}

    def json(self):
        return self._json


class Sessao:
    """Sessao falsa: metadata devolve `meta`, imagem devolve `imagem`. Sem rede."""

    def __init__(self, meta=META_OK, imagem=None, erro=None):
        self.meta, self.imagem, self.erro = meta, imagem or Resposta(), erro
        self.chamadas = []

    def get(self, url, params=None, **kw):
        self.chamadas.append((url, params))
        if self.erro:
            raise self.erro
        return Resposta(json=self.meta) if url.endswith("/metadata") else self.imagem


def imagens(s):
    return [p for u, p in s.chamadas if not u.endswith("/metadata")]


def test_sem_chave_explica_como_criar(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    with pytest.raises(ChaveAusente, match="Street View Static API"):
        carregar_chave(tmp_path / ".env")


def test_chave_lida_do_env(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    (tmp_path / ".env").write_text(f"GOOGLE_MAPS_API_KEY={CHAVE}\n")
    assert carregar_chave(tmp_path / ".env") == CHAVE


def test_coordenadas_ignora_id_desconhecido():
    L = pd.DataFrame({"id": [1, 2], "latitude": [-23.5, -23.6], "longitude": [-46.6, -46.7]})
    assert coordenadas([2, 99], L) == {2: (-23.6, -46.7)}


def test_distancia():
    # 0,001 grau de latitude ~ 111 m
    assert distancia_m(-23.574, -46.64, -23.575, -46.64) == pytest.approx(111.2, abs=0.5)


def test_ok_usa_mesmo_panorama_em_todos_os_headings(tmp_path):
    s = Sessao()
    r = baixar_streetview(4917, -23.5742, -46.6397, CHAVE, tmp_path, headings=(0, 180), sessao=s)
    assert r["status"] == "ok" and r["pano_id"] == "P1" and r["data_captura"] == "2024-05"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["4917_0.jpg", "4917_180.jpg"]
    assert [(p["pano"], p["heading"]) for p in imagens(s)] == [("P1", 0), ("P1", 180)]


def test_sem_panorama_nao_pede_imagem(tmp_path):
    s = Sessao(meta={"status": "ZERO_RESULTS"})
    assert baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s)["status"] == "sem_panorama"
    assert imagens(s) == [] and not list(tmp_path.iterdir())


def test_existente_nao_chama_api(tmp_path):
    for h in (0, 90):
        (tmp_path / f"1_{h}.jpg").write_bytes(b"x")
    s = Sessao()
    r = baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, headings=(0, 90), sessao=s)
    assert r["status"] == "existente" and s.chamadas == []


def test_chave_recusada_aborta(tmp_path):
    s = Sessao(meta={"status": "REQUEST_DENIED", "error_message": "API not enabled"})
    with pytest.raises(AcessoNegado, match="API not enabled"):
        baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s)


def test_resposta_que_nao_e_imagem_falha_sem_arquivo(tmp_path):
    s = Sessao(imagem=Resposta(status=404, tipo="text/html"))
    r = baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s)
    assert r["status"] == "falhou" and not list(tmp_path.glob("*.jpg"))


def test_erro_de_rede_nao_vaza_a_chave(tmp_path):
    url = f"https://maps.googleapis.com/maps/api/streetview/metadata?key={CHAVE}"
    s = Sessao(erro=requests.ConnectionError(f"Max retries exceeded with url: {url}"))
    with pytest.raises(RuntimeError) as e:
        baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s)
    assert CHAVE not in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__


def test_registra_cada_imagem_pedida(tmp_path):
    uso = tmp_path / "uso.csv"
    baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, headings=(0, 90), sessao=Sessao(), uso=uso)
    assert imagens_hoje(uso) == 2
    assert uso.read_text().splitlines()[0] == "momento,id,heading"


def test_erro_tambem_conta_como_uso(tmp_path):
    uso = tmp_path / "uso.csv"
    s = Sessao(imagem=Resposta(status=500, tipo="text/html"))
    baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s, uso=uso)
    assert imagens_hoje(uso) == 1


def test_para_no_limite_e_retoma_depois(tmp_path):
    uso = tmp_path / "uso.csv"
    s = Sessao()
    r = baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s, uso=uso, max_imagens=3)
    assert r["status"] == "limite" and len(r["arquivos"]) == 3
    assert len(imagens(s)) == 3

    # com o limite maior, so a direcao que faltou e pedida
    s = Sessao()
    r = baixar_streetview(1, -23.5, -46.6, CHAVE, tmp_path, sessao=s, uso=uso, max_imagens=10)
    assert r["status"] == "ok" and [p["heading"] for p in imagens(s)] == [270]


def test_uso_de_outro_dia_nao_conta(tmp_path):
    uso = tmp_path / "uso.csv"
    uso.write_text("momento,id,heading\n2020-01-01T10:00:00,1,0\n2020-01-01T10:00:01,1,90\n")
    assert imagens_hoje(uso) == 0


class SessaoGeo(Sessao):
    """Metadata depende do ponto consultado: `panos(lat, lng)` devolve o JSON."""

    def __init__(self, panos):
        super().__init__()
        self.panos = panos

    def get(self, url, params=None, **kw):
        self.chamadas.append((url, params))
        if url.endswith("/metadata"):
            lat, lng = map(float, params["location"].split(","))
            return Resposta(json=self.panos(lat, lng))
        return self.imagem


LAT, LNG = -23.5742, -46.6397


def pano(pid, autor, lat=LAT, lng=LNG):
    return {
        "status": "OK",
        "pano_id": pid,
        "copyright": f"© {autor}",
        "location": {"lat": lat, "lng": lng},
        "date": "2024-05",
    }


def terceiro_no_centro(lat, lng):
    # no ponto exato so ha a foto 360 de uma loja; nas sondas, o carro do Google
    if abs(lat - LAT) < 1e-6 and abs(lng - LNG) < 1e-6:
        return pano("LOJA", "Rudolfo")
    return pano("RUA", "Google", lat + 0.0001, lng)


def test_panorama_do_google_usado_direto(tmp_path):
    s = SessaoGeo(lambda la, ln: pano("RUA", "Google"))
    r = baixar_streetview(1, LAT, LNG, CHAVE, tmp_path, headings=(0,), sessao=s)
    assert (r["status"], r["pano_id"], r["copyright"]) == ("ok", "RUA", "© Google")
    assert sum(u.endswith("/metadata") for u, _ in s.chamadas) == 1


def test_terceiro_e_trocado_pelo_google_em_volta(tmp_path):
    s = SessaoGeo(terceiro_no_centro)
    r = baixar_streetview(1, LAT, LNG, CHAVE, tmp_path, headings=(0, 90), sessao=s)
    assert r["status"] == "ok" and r["pano_id"] == "RUA"
    assert {p["pano"] for p in imagens(s)} == {"RUA"}


def test_so_terceiros_nao_baixa_nada(tmp_path):
    s = SessaoGeo(lambda la, ln: pano("LOJA", "Rudolfo"))
    r = baixar_streetview(1, LAT, LNG, CHAVE, tmp_path, sessao=s)
    assert r["status"] == "sem_panorama_google" and imagens(s) == []


def test_google_longe_demais_nao_vale(tmp_path):
    def longe(la, ln):
        # o do Google so aparece ~1 km ao norte de cada sonda: fora do raio de 150 m
        if (la, ln) == (LAT, LNG):
            return pano("LOJA", "X")
        return pano("RUA", "Google", la + 0.01, ln)

    r = baixar_streetview(1, LAT, LNG, CHAVE, tmp_path, raio=150, sessao=SessaoGeo(longe))
    assert r["status"] == "sem_panorama_google"


def test_revisar_mesmo_panorama_nao_baixa(tmp_path):
    for h in (0, 90):
        (tmp_path / f"1_{h}.jpg").write_bytes(b"x")
    s = SessaoGeo(lambda la, ln: pano("RUA", "Google"))
    r = baixar_streetview(
        1, LAT, LNG, CHAVE, tmp_path, headings=(0, 90), sessao=s, revisar=True, pano_atual="RUA"
    )
    assert r["status"] == "existente" and r["copyright"] == "© Google" and imagens(s) == []


def test_revisar_troca_imagens_de_terceiro(tmp_path):
    for h in (0, 90):
        (tmp_path / f"1_{h}.jpg").write_bytes(b"antiga")
    s = SessaoGeo(terceiro_no_centro)
    r = baixar_streetview(
        1, LAT, LNG, CHAVE, tmp_path, headings=(0, 90), sessao=s, revisar=True, pano_atual="LOJA"
    )
    assert r["status"] == "ok" and len(imagens(s)) == 2
    assert (tmp_path / "1_0.jpg").read_bytes() == b"jpg"


def test_revisar_sem_google_apaga_as_de_terceiro(tmp_path):
    for h in (0, 90):
        (tmp_path / f"1_{h}.jpg").write_bytes(b"antiga")
    s = SessaoGeo(lambda la, ln: pano("LOJA", "Rudolfo"))
    r = baixar_streetview(
        1, LAT, LNG, CHAVE, tmp_path, headings=(0, 90), sessao=s, revisar=True, pano_atual="LOJA"
    )
    assert r["status"] == "sem_panorama_google" and not list(tmp_path.glob("*.jpg"))


def test_sem_revisar_existente_nem_consulta(tmp_path):
    for h in (0, 90):
        (tmp_path / f"1_{h}.jpg").write_bytes(b"x")
    s = SessaoGeo(lambda la, ln: pano("LOJA", "Rudolfo"))
    baixar_streetview(1, LAT, LNG, CHAVE, tmp_path, headings=(0, 90), sessao=s)
    assert s.chamadas == []

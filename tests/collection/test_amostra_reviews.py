import pandas as pd
import pytest

from src.amostra_reviews import classificar, selecionar_amostra


def anuncios(grupos):
    """grupos: lista de (nota, accuracy, room_type, quantos)."""
    linhas, i = [], 1
    for nota, acc, tipo, k in grupos:
        for _ in range(k):
            linhas.append(
                {
                    "id": i,
                    "room_type": tipo,
                    "picture_url": f"u{i}",
                    "number_of_reviews": 30,
                    "last_review": "2026-03-01",
                    "review_scores_rating": nota,
                    "review_scores_accuracy": acc,
                }
            )
            i += 1
    return pd.DataFrame(linhas)


INT, QTO = "Entire home/apt", "Private room"


@pytest.mark.parametrize(
    "nota, acc, esperado",
    [
        (4.97, 4.9, "nota_alta"),
        (4.80, 4.9, "nota_media"),
        (4.30, 4.9, "nota_baixa"),
        (4.90, 4.2, "accuracy_baixa"),  # accuracy baixa vence a nota
        (4.60, 4.9, None),  # entre as faixas: fora
    ],
)
def test_classificar(nota, acc, esperado):
    g = classificar(anuncios([(nota, acc, INT, 1)]))
    assert (g.iloc[0] if esperado else pd.isna(g.iloc[0])) == (esperado or True)


def test_n_por_grupo_e_tipo():
    df = anuncios(
        [(4.97, 4.9, INT, 10), (4.97, 4.9, QTO, 10), (4.3, 4.9, INT, 10), (4.3, 4.9, QTO, 10)]
    )
    a = selecionar_amostra(df, n=3)
    assert a.groupby(["grupo", "tipo"], observed=True).size().tolist() == [3, 3, 3, 3]


def test_tipo_com_pouco_completa_com_o_outro():
    df = anuncios([(4.3, 4.9, INT, 10), (4.3, 4.9, QTO, 1)])
    a = selecionar_amostra(df, n=3)
    assert a["tipo"].value_counts().to_dict() == {"inteiro": 5, "quarto": 1}


def test_filtros():
    df = anuncios([(4.97, 4.9, INT, 4)])
    df.loc[0, "number_of_reviews"] = 5
    df.loc[1, "last_review"] = "2023-01-01"
    df.loc[2, "picture_url"] = None
    assert selecionar_amostra(df, n=5)["id"].tolist() == [4]


def test_reprodutivel_e_sem_repeticao():
    df = anuncios([(4.97, 4.9, INT, 50), (4.97, 4.9, QTO, 50)])
    a, b = selecionar_amostra(df, n=10, seed=1), selecionar_amostra(df, n=10, seed=1)
    assert a["id"].tolist() == b["id"].tolist()
    assert a["id"].is_unique


def test_excluir_repoe_sem_mexer_no_resto():
    df = anuncios([(4.97, 4.9, INT, 30), (4.97, 4.9, QTO, 30)])
    a = selecionar_amostra(df, n=5)
    fora = a["id"].iloc[0]
    b = selecionar_amostra(df, n=5, excluir=[fora])
    assert len(b) == len(a) and fora not in set(b["id"])
    assert len(set(a["id"]) - set(b["id"])) == 1  # so o excluido saiu, o resto ficou
    assert b.loc[b["id"].isin(set(b["id"]) - set(a["id"])), "tipo"].item() == a["tipo"].iloc[0]

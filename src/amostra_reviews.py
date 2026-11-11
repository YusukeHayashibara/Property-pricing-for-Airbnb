import numpy as np
import pandas as pd

from src.airbnb_photos import FOTOS, LISTINGS

FOTOS_AMOSTRA = FOTOS.parent / "photos_amostra"  # separado de photos/, que define o piloto

COLS = [
    "id",
    "listing_url",
    "name",
    "room_type",
    "neighbourhood_cleansed",
    "price",
    "picture_url",
    "number_of_reviews",
    "last_review",
    "review_scores_rating",
    "review_scores_accuracy",
    "review_scores_cleanliness",
]

# as notas sao relativas: com >= 20 reviews a mediana de SP e 4,88 e o 5% pior comeca em ~4,54,
# entao "baixa" e < 4,5 (os ~3% piores), nao uma nota baixa em termos absolutos
FAIXAS = {"nota_baixa": (0, 4.5), "nota_media": (4.7, 4.85), "nota_alta": (4.95, 5.01)}
CORTE_ACCURACY = 4.5  # review_scores_accuracy: "o lugar corresponde as fotos e a descricao?"
GRUPOS = ["accuracy_baixa", "nota_baixa", "nota_media", "nota_alta"]
TIPOS = {"Entire home/apt": "inteiro", "Private room": "quarto"}


def carregar(path=LISTINGS):
    return pd.read_csv(path, usecols=COLS, low_memory=False)


def classificar(listings, corte_accuracy=CORTE_ACCURACY):
    """Grupo de cada anuncio (NaN = fora de todos). Accuracy baixa tem prioridade sobre a nota."""
    r = listings["review_scores_rating"]
    g = pd.Series(pd.NA, index=listings.index, dtype="object")
    for nome, (lo, hi) in FAIXAS.items():
        g[(r >= lo) & (r < hi)] = nome
    g[listings["review_scores_accuracy"] < corte_accuracy] = "accuracy_baixa"
    return g


def selecionar_amostra(
    listings=None,
    n=25,
    min_reviews=20,
    desde="2025-01-01",
    corte_accuracy=CORTE_ACCURACY,
    seed=42,
    excluir=(),
):
    """n anuncios por grupo x tipo (inteiro / quarto), sorteados com `seed`.

    Entram so anuncios com >= `min_reviews`, nota, accuracy, foto e review desde `desde`
    (a capa e de hoje; review antigo descreveria outro estado do imovel). Se um tipo tem
    menos de n anuncios num grupo, entram todos e o que falta sai do outro tipo do mesmo
    grupo, para cada grupo fechar 2n.

    `excluir`: ids a pular (ex.: capa que deu 404). O sorteio e uma ordem fixa calculada antes
    da exclusao, entao tirar um id so faz entrar o proximo da fila do mesmo grupo e tipo; os
    demais anuncios da amostra nao mudam.
    """
    df = carregar() if listings is None else listings.copy()
    df["tipo"] = df["room_type"].map(TIPOS)
    ok = (
        (df["number_of_reviews"] >= min_reviews)
        & df["review_scores_rating"].notna()
        & df["review_scores_accuracy"].notna()
        & df["picture_url"].notna()
        & df["tipo"].notna()
        & (pd.to_datetime(df["last_review"]) >= desde)
    )
    df = df[ok].sort_values("id")
    df = df.assign(
        grupo=classificar(df, corte_accuracy),
        _ordem=np.random.default_rng(seed).permutation(len(df)),
    ).dropna(subset=["grupo"])
    df = df[~df["id"].isin(set(excluir))]

    partes = []
    for _, g in df.groupby("grupo"):
        disp = g["tipo"].value_counts()
        tam = {t: min(n, int(disp.get(t, 0))) for t in TIPOS.values()}
        falta = 2 * n - sum(tam.values())
        for t in TIPOS.values():
            extra = min(falta, int(disp.get(t, 0)) - tam[t])
            tam[t] += extra
            falta -= extra
        for t, k in tam.items():
            partes.append(g[g["tipo"] == t].nsmallest(k, "_ordem"))

    out = pd.concat(partes).drop(columns="_ordem")
    out["grupo"] = pd.Categorical(out["grupo"], GRUPOS, ordered=True)
    return out.sort_values(["grupo", "tipo", "id"]).reset_index(drop=True)

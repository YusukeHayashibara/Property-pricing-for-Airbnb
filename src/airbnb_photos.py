import io
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
LISTINGS = RAIZ / "data" / "raw" / "Airbnb" / "listings.csv"
FOTOS = RAIZ / "data" / "raw" / "Airbnb" / "photos"

MAX_LADO = 512  # mesmo tamanho das fotos do piloto; o CLIP usa 224 de qualquer jeito
TIMEOUT = 20
TENTATIVAS = 3
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


def carregar_listings(path=LISTINGS):
    cols = ["id", "picture_url", "number_of_reviews", "review_scores_rating"]
    return pd.read_csv(path, usecols=cols, low_memory=False)


def selecionar_anuncios(
    listings, min_reviews=20, min_rating=4.0, n=300, amostra="primeiros", seed=None
):
    """Regra de amostragem -> lista de ids. Os defaults reproduzem o piloto (294 fotos).

    amostra="primeiros": os n de menor id (enviesa para anuncios antigos).
    amostra="aleatoria": n sorteados com `seed`.
    """
    pool = listings[
        (listings["number_of_reviews"] >= min_reviews)
        & (listings["review_scores_rating"] >= min_rating)
        & listings["picture_url"].notna()
    ].sort_values("id")
    if n is None or n >= len(pool):
        return pool["id"].tolist()
    if amostra == "primeiros":
        return pool["id"].head(n).tolist()
    if amostra == "aleatoria":
        return pool["id"].sample(n, random_state=seed).sort_values().tolist()
    raise ValueError(f"amostra desconhecida: {amostra!r}")


def _redimensionar(conteudo, max_lado):
    im = Image.open(io.BytesIO(conteudo)).convert("RGB")
    im.thumbnail((max_lado, max_lado))
    return im


def baixar_capa(listing_id, url, destino=FOTOS, max_lado=MAX_LADO, sobrescrever=False, sessao=None):
    """Baixa uma capa para `destino/{id}.jpg`. Nao levanta excecao: o erro volta no dict."""
    destino = Path(destino)
    alvo = destino / f"{int(listing_id)}.jpg"
    linha = {"id": int(listing_id), "url": url, "path": str(alvo), "status": None, "erro": None}

    if alvo.exists() and not sobrescrever:
        return {**linha, "status": "existente"}
    if not isinstance(url, str) or not url:
        return {**linha, "path": None, "status": "sem_url"}

    sessao = sessao or requests
    erro = None
    for tentativa in range(TENTATIVAS):
        try:
            r = sessao.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
            # 4xx (exceto 429) e definitivo: foto removida, nao adianta repetir
            if 400 <= r.status_code < 500 and r.status_code != 429:
                erro = f"HTTP {r.status_code}"
                break
            r.raise_for_status()
            im = _redimensionar(r.content, max_lado)
            destino.mkdir(parents=True, exist_ok=True)
            tmp = alvo.with_suffix(".jpg.part")
            im.save(tmp, "JPEG", quality=90)
            os.replace(tmp, alvo)  # atomico: nunca fica .jpg pela metade
            return {**linha, "status": "ok"}
        except Exception as e:  # rede, HTTP 5xx/429 ou imagem invalida
            erro = f"{type(e).__name__}: {e}"
            if tentativa < TENTATIVAS - 1:
                time.sleep(0.5 * 2**tentativa)
    return {**linha, "path": None, "status": "falhou", "erro": erro}


def baixar_capas(
    ids,
    listings=None,
    destino=FOTOS,
    max_lado=MAX_LADO,
    workers=8,
    sobrescrever=False,
    sessao=None,
):
    """Baixa as capas de uma lista de ids. Retorna o relatorio: id | url | path | status | erro.

    `listings` e um DataFrame com id e picture_url; se None, le o listings.csv bruto.
    Status: ok, existente (ja estava na pasta), sem_url (id fora do listings ou sem foto), falhou.
    """
    listings = carregar_listings() if listings is None else listings
    urls = listings.drop_duplicates("id").set_index("id")["picture_url"]
    ids = list(dict.fromkeys(int(i) for i in ids))

    sessao = sessao or requests.Session()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        linhas = list(
            ex.map(
                lambda i: baixar_capa(i, urls.get(i), destino, max_lado, sobrescrever, sessao),
                ids,
            )
        )
    return pd.DataFrame(linhas, columns=["id", "url", "path", "status", "erro"])

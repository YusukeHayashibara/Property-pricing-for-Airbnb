"""[B] Fotos de capa: download reduzido, embedding CLIP e conceitos visuais.

Reaproveita src/airbnb_photos.py para o download. A diferença: a URL vai pelo redimensionador do
CDN do Airbnb (`/im/pictures/...?im_w=480`), ~25 KB por foto em vez de ~2 MB no original.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.airbnb_photos import baixar_capas

RAIZ = Path(__file__).resolve().parents[1]
FOTOS_MODELO = RAIZ / "data" / "raw" / "Airbnb" / "photos_modelo"
CACHE_EMB = RAIZ / "data" / "processed" / "modelo" / "clip_capas_modelo.npz"
PROMPTS = RAIZ / "data" / "processed" / "Airbnb" / "clip_prompts.json"
CLIP_MODEL = "openai/clip-vit-base-patch32"   # mesmo modelo dos notebooks de imageAnalysis

_clip = {}


def url_reduzida(url, largura=480):
    """https://a0.muscache.com/pictures/X.jpg -> https://a0.muscache.com/im/pictures/X.jpg?im_w=480"""
    if not isinstance(url, str):
        return url
    return url.replace("muscache.com/pictures/", "muscache.com/im/pictures/").split("?")[0] + f"?im_w={largura}"


def baixar_amostra(anuncios, destino=FOTOS_MODELO, workers=16):
    """Baixa as capas dos anúncios (DataFrame com id e picture_url). Idempotente."""
    lst = anuncios[["id", "picture_url"]].assign(picture_url=lambda d: d["picture_url"].map(url_reduzida))
    return baixar_capas(lst["id"], listings=lst, destino=destino, workers=workers)


def _carregar_clip():
    if not _clip:
        import torch
        from transformers import CLIPModel, CLIPProcessor
        _clip["torch"] = torch
        _clip["model"] = CLIPModel.from_pretrained(CLIP_MODEL).eval()
        _clip["proc"] = CLIPProcessor.from_pretrained(CLIP_MODEL)
    return _clip


def _saida(e):
    # transformers 5 devolve um objeto de saída; o vetor projetado está em pooler_output
    e = getattr(e, "pooler_output", e)
    e = e.detach().cpu().numpy().astype(np.float32)
    return e / np.linalg.norm(e, axis=1, keepdims=True)


def embedding_clip(caminhos, lote=64):
    """Vetores CLIP (512, norma 1) de uma lista de imagens."""
    from PIL import Image
    c = _carregar_clip()
    out = []
    for i in range(0, len(caminhos), lote):
        ims = [Image.open(p).convert("RGB") for p in caminhos[i:i + lote]]
        with c["torch"].no_grad():
            out.append(_saida(c["model"].get_image_features(**c["proc"](images=ims, return_tensors="pt"))))
    return np.vstack(out)


def embedding_texto(frases):
    c = _carregar_clip()
    with c["torch"].no_grad():
        return _saida(c["model"].get_text_features(**c["proc"](text=frases, return_tensors="pt", padding=True)))


def embeddings_amostra(ids, pasta=FOTOS_MODELO, cache=CACHE_EMB):
    """Embeddings das capas baixadas, com cache em .npz (só calcula os ids novos)."""
    ids = [int(i) for i in ids if (Path(pasta) / f"{int(i)}.jpg").exists()]
    feitos = {}
    if Path(cache).exists():
        z = np.load(cache)
        feitos = dict(zip(z["ids"].tolist(), z["emb"]))
    novos = [i for i in ids if i not in feitos]
    if novos:
        emb = embedding_clip([str(Path(pasta) / f"{i}.jpg") for i in novos])
        feitos.update(zip(novos, emb))
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, ids=np.array(list(feitos)), emb=np.vstack(list(feitos.values())))
    return np.array(ids), np.vstack([feitos[i] for i in ids])


def eixos_conceitos(prompts=PROMPTS):
    """Um eixo por aspecto de clip_prompts.json: média dos protótipos positivos − média dos negativos.

    Os mesmos prompts dos notebooks de imageAnalysis (limpeza, espaço, luz, decoração, vista, lazer).
    """
    cfg = json.loads(Path(prompts).read_text())
    eixos = {}
    for nome, (pos, neg) in cfg["aspects"].items():
        p, n = embedding_texto(pos).mean(0), embedding_texto(neg).mean(0)
        eixos[nome] = p - n
    return pd.DataFrame(eixos).T   # aspecto × 512

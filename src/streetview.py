import math
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from src.airbnb_photos import LISTINGS

RAIZ = Path(__file__).resolve().parents[1]
ENV = RAIZ / ".env"
SAIDA = RAIZ / "data" / "raw" / "StreetView"
USO = SAIDA / "uso.csv"  # uma linha por imagem pedida a API (a metadata e gratis e nao entra)

ENV_VAR = "GOOGLE_MAPS_API_KEY"
URL_META = "https://maps.googleapis.com/maps/api/streetview/metadata"
URL_IMG = "https://maps.googleapis.com/maps/api/streetview"

# o Inside Airbnb desloca as coordenadas em ate ~150 m: nao da para mirar na fachada,
# entao o default olha para os 4 lados do panorama mais proximo
HEADINGS = (0, 90, 180, 270)
RAIO = 150
TAMANHO = "640x640"  # maximo da API sem plano premium
FOV = 90
PITCH = 0
TIMEOUT = 20

# o panorama mais proximo pode ser uma foto 360 de terceiro (interior de loja, hall de
# predio), mesmo com source=outdoor. So os do carro do Google tem copyright "(c) Google";
# quando o mais proximo nao e, sonda a metadata (gratis) em volta da coordenada
SONDAS_M = (30, 60)  # aneis de busca, em metros
SONDAS_ANG = range(0, 360, 45)  # 8 direcoes por anel
RAIO_SONDA = 50

# teto local de imagens por dia, porque a cota nao foi configurada no console do Google.
# So vale para chamadas feitas por este modulo; o dia e o do relogio local.
MAX_IMAGENS_DIA = 2000

MSG_CHAVE = f"""Chave da API do Google nao encontrada ({ENV_VAR}).

Como criar:
  1. https://console.cloud.google.com/ -> crie (ou escolha) um projeto
  2. Faturamento: vincule uma conta (a API exige, mesmo dentro da cota gratuita)
  3. APIs e servicos -> Biblioteca -> ative "Street View Static API"
  4. APIs e servicos -> Credenciais -> Criar credenciais -> Chave de API
  5. Recomendado: restrinja a chave a "Street View Static API"
  6. Na raiz do repositorio:  cp .env.example .env   e preencha
       {ENV_VAR}=sua_chave

O .env esta no .gitignore: a chave nao vai para o git."""


class ChaveAusente(RuntimeError):
    pass


class AcessoNegado(RuntimeError):
    """Chave invalida, API nao ativada ou faturamento ausente. Aborta o lote inteiro."""


def carregar_chave(env=ENV):
    load_dotenv(env)
    chave = os.getenv(ENV_VAR, "").strip()
    if not chave:
        raise ChaveAusente(MSG_CHAVE)
    return chave


def coordenadas(listing_ids, listings=None):
    """id -> (latitude, longitude). Ids fora do listings ficam de fora."""
    if listings is None:
        listings = pd.read_csv(LISTINGS, usecols=["id", "latitude", "longitude"])
    df = listings.drop_duplicates("id").set_index("id")
    ids = [int(i) for i in listing_ids if int(i) in df.index]
    return {i: (float(df.at[i, "latitude"]), float(df.at[i, "longitude"])) for i in ids}


def distancia_m(lat1, lng1, lat2, lng2):
    """Haversine, em metros."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(a))


def _get(sessao, url, params):
    # a chave vai na query string: excecoes do requests imprimem a URL inteira,
    # entao a mensagem e trocada por uma sem a URL
    try:
        return sessao.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise RuntimeError(f"{type(e).__name__} ao acessar {url}") from None


def metadata(lat, lng, chave, raio=RAIO, sessao=None):
    """Consulta gratuita: existe panorama ate `raio` m? Retorna o JSON da API."""
    sessao = sessao or requests
    r = _get(
        sessao,
        URL_META,
        {"location": f"{lat},{lng}", "radius": raio, "source": "outdoor", "key": chave},
    )
    meta = r.json()
    if meta.get("status") == "REQUEST_DENIED":
        raise AcessoNegado(meta.get("error_message", "REQUEST_DENIED"))
    return meta


def e_google(meta):
    return "google" in str(meta.get("copyright", "")).lower()


def _deslocar(lat, lng, metros, angulo):
    a = math.radians(angulo)
    dlat = metros * math.cos(a) / 111_320
    dlng = metros * math.sin(a) / (111_320 * math.cos(math.radians(lat)))
    return lat + dlat, lng + dlng


def escolher_panorama(lat, lng, chave, raio=RAIO, sessao=None):
    """Panorama do Google mais proximo do anuncio, ate `raio` m. So usa metadata (gratis).

    Retorna o JSON da metadata escolhida; status ZERO_RESULTS se nao ha panorama nenhum e
    SEM_GOOGLE se so ha panoramas de terceiros.
    """
    meta = metadata(lat, lng, chave, raio, sessao)
    if meta.get("status") != "OK" or e_google(meta):
        return meta

    achados = {}
    for d in SONDAS_M:
        for ang in SONDAS_ANG:
            m = metadata(*_deslocar(lat, lng, d, ang), chave, RAIO_SONDA, sessao)
            if m.get("status") == "OK" and e_google(m):
                loc = m["location"]
                dist = distancia_m(lat, lng, loc["lat"], loc["lng"])
                if dist <= raio:
                    achados[m["pano_id"]] = (dist, m)
    if not achados:
        return {"status": "SEM_GOOGLE", "copyright": meta.get("copyright")}
    return min(achados.values(), key=lambda t: t[0])[1]


def imagens_hoje(uso=USO):
    uso = Path(uso)
    if not uso.exists():
        return 0
    hoje = date.today().isoformat()
    return sum(1 for ln in uso.read_text().splitlines()[1:] if ln.startswith(hoje))


def _registrar_uso(uso, listing_id, heading):
    uso = Path(uso)
    novo = not uso.exists()
    uso.parent.mkdir(parents=True, exist_ok=True)
    with open(uso, "a") as f:
        if novo:
            f.write("momento,id,heading\n")
        f.write(f"{datetime.now().isoformat(timespec='seconds')},{int(listing_id)},{heading}\n")


def baixar_streetview(
    listing_id,
    lat,
    lng,
    chave,
    destino=SAIDA,
    headings=HEADINGS,
    raio=RAIO,
    sobrescrever=False,
    sessao=None,
    uso=None,
    max_imagens=None,
    revisar=False,
    pano_atual=None,
):
    """Salva `destino/{id}_{heading}.jpg` do panorama do Google mais proximo do anuncio.

    Status: ok, existente, sem_panorama (nada ate `raio` m), sem_panorama_google (so fotos de
    terceiros por perto), falhou, limite.
    Com `revisar`, anuncio que ja tem imagens tem o panorama escolhido de novo (so metadata):
    se for o mesmo `pano_atual`, nada e baixado; se mudou, as imagens sao trocadas; se nao ha
    panorama do Google, as imagens antigas (de terceiro) sao apagadas.
    Com `uso` (caminho do registro), cada imagem pedida e anotada; com `max_imagens`, para
    antes de passar desse total no dia e devolve "limite" com o que ja salvou.
    Levanta AcessoNegado se a chave for recusada.
    """
    destino = Path(destino)
    arquivos = [destino / f"{int(listing_id)}_{h}.jpg" for h in headings]
    linha = {"id": int(listing_id), "lat": lat, "lng": lng, "status": None, "erro": None}

    completo = all(a.exists() for a in arquivos)
    if completo and not sobrescrever and not revisar:
        return {**linha, "status": "existente", "arquivos": [str(a) for a in arquivos]}

    sessao = sessao or requests
    meta = escolher_panorama(lat, lng, chave, raio, sessao)
    if meta.get("status") in ("ZERO_RESULTS", "SEM_GOOGLE"):
        for a in arquivos:  # o que estava salvo era de terceiro (ou de outra execucao)
            a.unlink(missing_ok=True)
        status = "sem_panorama" if meta["status"] == "ZERO_RESULTS" else "sem_panorama_google"
        return {**linha, "status": status, "copyright": meta.get("copyright")}
    if meta.get("status") != "OK":
        return {**linha, "status": "falhou", "erro": meta.get("status")}

    pano = meta["pano_id"]
    plat, plng = meta["location"]["lat"], meta["location"]["lng"]
    linha.update(
        pano_id=pano,
        pano_lat=plat,
        pano_lng=plng,
        distancia_m=round(distancia_m(lat, lng, plat, plng), 1),
        data_captura=meta.get("date"),
        copyright=meta.get("copyright"),
    )
    if completo and not sobrescrever and pano == pano_atual:
        return {**linha, "status": "existente", "arquivos": [str(a) for a in arquivos]}
    # panorama novo: as imagens antigas, se houver, sao de outro panorama e sao trocadas
    trocar = sobrescrever or (revisar and pano != pano_atual)

    destino.mkdir(parents=True, exist_ok=True)
    salvos = []
    for h, alvo in zip(headings, arquivos):
        if alvo.exists() and not trocar:
            salvos.append(str(alvo))
            continue
        if max_imagens is not None and imagens_hoje(uso) >= max_imagens:
            return {**linha, "status": "limite", "arquivos": salvos}
        # pede pelo pano_id, nao pela coordenada: todos os headings saem do mesmo panorama
        params = {
            "pano": pano,
            "size": TAMANHO,
            "heading": h,
            "fov": FOV,
            "pitch": PITCH,
            "return_error_code": "true",
            "key": chave,
        }
        try:
            r = _get(sessao, URL_IMG, params)
        except RuntimeError as e:
            return {**linha, "status": "falhou", "erro": str(e), "arquivos": salvos}
        if uso is not None:
            # conta toda resposta, inclusive erro: na duvida, superestima o gasto
            _registrar_uso(uso, listing_id, h)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            return {
                **linha,
                "status": "falhou",
                "erro": f"HTTP {r.status_code} no heading {h}",
                "arquivos": salvos,
            }
        tmp = alvo.with_suffix(".jpg.part")
        tmp.write_bytes(r.content)
        os.replace(tmp, alvo)
        salvos.append(str(alvo))

    return {**linha, "status": "ok", "arquivos": salvos}

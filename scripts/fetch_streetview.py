"""Imagens do Google Street View na coordenada de anúncios do Airbnb.

Uso (na raiz do repositório):
  python scripts/fetch_streetview.py 4917
  python scripts/fetch_streetview.py 4917 54614 82935 --headings 0 180
  python scripts/fetch_streetview.py --ids-arquivo ids.txt      # um id por linha

Requer GOOGLE_MAPS_API_KEY no .env (o script explica como criar se não encontrar). Cada
heading é uma imagem cobrada pela Street View Static API; a consulta de metadata, que diz
se existe panorama, é gratuita e roda antes. Um anúncio sem panorama não gera cobrança.

Panoramas: só os do carro do Google ("© Google"). Quando o mais próximo é uma foto 360° de
terceiro (interior de loja, hall de prédio), o script procura em volta, só com metadata
(grátis); sem nenhum do Google a até --raio m, o anúncio fica como sem_panorama_google.

--revisar: para anúncios que já têm imagens, escolhe o panorama de novo e troca as imagens só
se ele mudou (ex.: imagens baixadas antes deste filtro, que podem ser de terceiros).

Limite diário: o script para ao chegar em --max-imagens imagens no dia (default 2000),
contadas em data/raw/StreetView/uso.csv. Os anúncios que ficarem para trás continuam de
onde pararam na próxima execução. Só vale para este script, não substitui a cota do Google.

As coordenadas do Inside Airbnb são deslocadas em até ~150 m: a imagem mostra o entorno
do anúncio, não a fachada. Por isso o default são 4 headings do panorama mais próximo.

Entrada:
  data/raw/Airbnb/listings.csv              (latitude, longitude)
  .env                                      (GOOGLE_MAPS_API_KEY)
Saída:
  data/raw/StreetView/{id}_{heading}.jpg    (640x640)
  data/raw/StreetView/manifest.csv          (panorama, data da captura, distância ao anúncio)
  data/raw/StreetView/uso.csv               (uma linha por imagem pedida: momento, id, heading)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # raiz, para importar `src`

from src.streetview import (  # noqa: E402
    HEADINGS,
    MAX_IMAGENS_DIA,
    RAIO,
    SAIDA,
    USO,
    AcessoNegado,
    ChaveAusente,
    baixar_streetview,
    carregar_chave,
    coordenadas,
    imagens_hoje,
)

MANIFEST = SAIDA / "manifest.csv"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("ids", type=int, nargs="*", help="ids de anúncios do Airbnb")
    p.add_argument("--ids-arquivo", type=Path, help="arquivo com um id por linha")
    p.add_argument("--headings", type=int, nargs="+", default=list(HEADINGS))
    p.add_argument("--raio", type=int, default=RAIO, help="metros até o panorama")
    p.add_argument("--sobrescrever", action="store_true")
    p.add_argument(
        "--revisar", action="store_true", help="reescolhe o panorama de quem já tem imagens"
    )
    p.add_argument(
        "--max-imagens", type=int, default=MAX_IMAGENS_DIA, help="teto de imagens por dia"
    )
    a = p.parse_args()

    ids = list(a.ids)
    if a.ids_arquivo:
        ids += [int(x) for x in a.ids_arquivo.read_text().split()]
    ids = list(dict.fromkeys(ids))
    if not ids:
        p.error("informe ao menos um id")

    try:
        chave = carregar_chave()
    except ChaveAusente as e:
        sys.exit(str(e))

    coords = coordenadas(ids)
    for i in ids:
        if i not in coords:
            print(f"{i}: não está no listings.csv, ignorado")
    usadas = imagens_hoje()
    restantes = max(a.max_imagens - usadas, 0)
    previstas = len(coords) * len(a.headings)
    print(f"{len(coords)} anúncios, até {previstas} imagens cobradas")
    print(f"hoje: {usadas} de {a.max_imagens} imagens já usadas, restam {restantes}\n")
    if restantes == 0:
        sys.exit("Limite diário atingido. Rode de novo amanhã ou aumente --max-imagens.")

    panos = {}
    if MANIFEST.exists():
        panos = pd.read_csv(MANIFEST).set_index("id")["pano_id"].dropna().to_dict()

    linhas = []
    try:
        for i, (lat, lng) in coords.items():
            r = baixar_streetview(
                i,
                lat,
                lng,
                chave,
                headings=a.headings,
                raio=a.raio,
                sobrescrever=a.sobrescrever,
                uso=USO,
                max_imagens=a.max_imagens,
                revisar=a.revisar,
                pano_atual=panos.get(i),
            )
            if r["status"] == "limite":
                faltam = len(coords) - len(linhas)
                print(f"\nLimite diário de {a.max_imagens} imagens atingido no anúncio {i}.")
                print(f"{faltam} anúncio(s) ficaram para a próxima execução.")
                break
            extra = (
                f" (panorama a {r['distancia_m']} m, {r['data_captura']})" if "pano_id" in r else ""
            )
            print(f"{i}: {r['status']}{extra}" + (f" -- {r['erro']}" if r["erro"] else ""))
            linhas.append(r)
    except AcessoNegado as e:
        print(f"\nA API recusou a chave: {e}")
        print("Confira se a Street View Static API está ativada e o faturamento vinculado.")
        sys.exit(1)
    finally:
        _gravar_manifest(linhas)


def _gravar_manifest(linhas):
    rel = pd.DataFrame(linhas)
    if len(rel):
        # "existente" só entra quando --revisar consultou a metadata (tem copyright)
        gravar = ["ok", "sem_panorama", "sem_panorama_google", "falhou"]
        revisado = (
            rel["status"].eq("existente") & rel.get("copyright", pd.Series(index=rel.index)).notna()
        )
        rel = rel[rel["status"].isin(gravar) | revisado]
    if rel.empty:
        return
    rel = rel.drop(columns="arquivos", errors="ignore").assign(
        baixado_em=datetime.now().isoformat(timespec="seconds")
    )
    if MANIFEST.exists():
        rel = pd.concat([pd.read_csv(MANIFEST), rel])
    rel = rel.drop_duplicates("id", keep="last").sort_values("id")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rel.to_csv(MANIFEST, index=False)
    print(f"\nmanifest: {MANIFEST} ({len(rel)} ids)")


if __name__ == "__main__":
    main()

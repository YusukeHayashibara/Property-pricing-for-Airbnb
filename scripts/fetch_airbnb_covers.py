"""Fotos de capa dos anúncios do Airbnb (coluna picture_url do Inside Airbnb).

Uso (na raiz do repositório):
  python scripts/fetch_airbnb_covers.py                         # reproduz o piloto
  python scripts/fetch_airbnb_covers.py --amostra aleatoria --n 500 --seed 42
  python scripts/fetch_airbnb_covers.py --ids 4917 54614 82935
  python scripts/fetch_airbnb_covers.py --ids-arquivo ids.txt   # um id por linha

Sem --ids, a amostra sai da regra de src.airbnb_photos.selecionar_anuncios. Os defaults
(menor id, >= 20 reviews, nota >= 4.0, n = 300) reproduzem as 294 fotos do piloto; 6 delas
não baixaram. Fotos que já estão na pasta não são baixadas de novo.

Entrada:
  data/raw/Airbnb/listings.csv
Saída:
  data/raw/Airbnb/photos/{id}.jpg          (lado maior = 512 px)
  data/raw/Airbnb/photos_manifest.csv      (id, url, status, erro, baixado_em; um registro por id)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # raiz, para importar `src`

from src.airbnb_photos import (  # noqa: E402
    FOTOS,
    baixar_capas,
    carregar_listings,
    selecionar_anuncios,
)

MANIFEST = FOTOS.parent / "photos_manifest.csv"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--ids", type=int, nargs="+", help="ids explícitos (ignora a regra de amostra)")
    p.add_argument("--ids-arquivo", type=Path, help="arquivo com um id por linha")
    p.add_argument("--min-reviews", type=int, default=20)
    p.add_argument("--min-rating", type=float, default=4.0)
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--amostra", choices=["primeiros", "aleatoria"], default="primeiros")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--sobrescrever", action="store_true")
    a = p.parse_args()

    listings = carregar_listings()
    if a.ids:
        ids = a.ids
    elif a.ids_arquivo:
        ids = [int(x) for x in a.ids_arquivo.read_text().split()]
    else:
        ids = selecionar_anuncios(listings, a.min_reviews, a.min_rating, a.n, a.amostra, a.seed)
    print(f"{len(ids)} anúncios")

    rel = baixar_capas(ids, listings, workers=a.workers, sobrescrever=a.sobrescrever)
    print(rel["status"].value_counts().to_string())
    falhas = rel[rel["status"].isin(["falhou", "sem_url"])]
    if len(falhas):
        print("\nnão baixados:")
        print(falhas[["id", "status", "erro"]].to_string(index=False))

    # manifest acumula execuções. Foto "existente" só entra se ainda não estiver registrada
    # (caso das fotos do piloto, baixadas antes do manifest), com baixado_em vazio.
    rel = rel.drop(columns="path")
    antigo = pd.read_csv(MANIFEST) if MANIFEST.exists() else pd.DataFrame(columns=rel.columns)
    existentes = rel[(rel["status"] == "existente") & ~rel["id"].isin(antigo["id"])]
    baixados = rel[rel["status"] != "existente"].assign(
        baixado_em=datetime.now().isoformat(timespec="seconds")
    )
    manifest = (
        pd.concat([antigo, existentes, baixados])
        .drop_duplicates("id", keep="last")
        .sort_values("id")
    )
    manifest.to_csv(MANIFEST, index=False)
    print(f"\nmanifest: {MANIFEST} ({len(manifest)} ids)")


if __name__ == "__main__":
    main()

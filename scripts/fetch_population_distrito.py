"""Population by distrito (IBGE Censo 2022, SIDRA table 9923).

Output: data/external/populacao_distrito_2022.csv.

Usage (from repo root):  python scripts/fetch_population_distrito.py
Keys are normalized (upper case, no accents) to match the `distrito` key used in the pipeline,
and are checked 96/96 against data/external/distrito_municipal.geojson.
"""

import json
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://apisidra.ibge.gov.br/values/t/9923/n10/in%20n6%203550308/p/2022?formato=json"
EXT = Path("data/external")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def main() -> None:
    raw = json.loads(urllib.request.urlopen(URL).read().decode("utf-8", errors="replace"))[1:]
    rows = [
        (r["D1C"], norm(r["D1N"].split(" - ")[0]), int(r["V"])) for r in raw if r["D4N"] == "Total"
    ]
    df = pd.DataFrame(rows, columns=["cd_ibge", "distrito", "populacao_2022"])
    geo = {
        norm(f["properties"]["nm_distrito_municipal"])
        for f in json.load(open(EXT / "distrito_municipal.geojson", encoding="utf-8"))["features"]
    }
    assert set(df.distrito) == geo, (geo - set(df.distrito), set(df.distrito) - geo)
    df.sort_values("distrito")[["distrito", "cd_ibge", "populacao_2022"]].to_csv(
        EXT / "populacao_distrito_2022.csv", index=False
    )
    print(f"{len(df)} distritos, {df.populacao_2022.sum():,} habitantes")


if __name__ == "__main__":
    main()

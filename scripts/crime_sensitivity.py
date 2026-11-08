"""Sensibilidade do risco de crime por distrito às decisões ainda em aberto.

Uso (na raiz do repositório):  python scripts/crime_sensitivity.py

Perguntas em aberto (obsidian-vault/02 - Data Sources/ISP.md): qual cesta de crimes e qual
janela de tempo? Além disso: dividir por habitante ou por área? tratar vários DPs no mesmo
distrito pela média (A) ou pela soma (B)? como preencher distritos sem DP?
Este script NÃO decide: mede quanto o ranking de distritos muda com cada escolha.

Entrada:
  data/processed/{ISP,SSP}/dados_criminais_sao_paulo_2025.csv   (2024 e 2025, por mês)
  data/reference/dp_distrito_crosswalk.csv                      (crosswalk revisado)
  data/external/populacao_distrito_2022.csv                     (IBGE Censo 2022)
  data/external/distrito_municipal.geojson
Saída:
  outputs/crime_sensitivity_ranking.csv   (taxa e posição por distrito em cada configuração)
  outputs/crime_sensitivity_robustez.csv  (faixa de posição e robustez por distrito)
  outputs/crime_sensitivity.png
"""

import itertools
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

EXT, OUT = Path("data/external"), Path("outputs")

# Cestas (NATUREZA2). "Nº DE VÍTIMAS ..." é excluído sempre (dupla contagem das ocorrências).
BASKETS = {
    "total": None,  # tudo, como em aggregation.ipynb
    "patrimonial": [
        "FURTO - OUTROS",
        "FURTO DE VEÍCULO",
        "ROUBO - OUTROS",
        "ROUBO DE VEÍCULO",
        "ROUBO DE CARGA",
        "ROUBO A BANCO",
    ],
    "roubo": ["ROUBO - OUTROS", "ROUBO DE VEÍCULO", "ROUBO DE CARGA", "ROUBO A BANCO"],
    "pessoa": [
        "HOMICÍDIO DOLOSO",
        "LATROCÍNIO",
        "TENTATIVA DE HOMICÍDIO",
        "ESTUPRO",
        "ESTUPRO DE VULNERÁVEL",
        "LESÃO CORPORAL DOLOSA",
        "LESÃO CORPORAL SEGUIDA DE MORTE",
    ],
    # o que um hóspede a pé enfrenta: furto/roubo comum + agressão + violência sexual + homicídio
    "rua_hospede": [
        "FURTO - OUTROS",
        "ROUBO - OUTROS",
        "LESÃO CORPORAL DOLOSA",
        "ESTUPRO",
        "ESTUPRO DE VULNERÁVEL",
        "HOMICÍDIO DOLOSO",
        "TENTATIVA DE HOMICÍDIO",
        "LATROCÍNIO",
    ],
}
WINDOWS = {  # (coluna, meses)
    "2025": ("2025", range(1, 13)),
    "2024": ("2024", range(1, 13)),
    "media_24_25": (None, range(1, 13)),
    "2025_H1": ("2025", range(1, 7)),
    "2025_H2": ("2025", range(7, 13)),
}
BASELINE = ("total", "2025", "100k", "A", "nearest")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def first_existing(*paths):
    for p in paths:
        if Path(p).exists():
            return Path(p)
    raise FileNotFoundError("nenhum de: " + ", ".join(map(str, paths)))


def dp_counts(cr, basket, window):
    col, months = WINDOWS[window]
    d = cr[cr["MES"].isin(months)]
    if BASKETS[basket] is not None:
        d = d[d["NATUREZA2"].isin(BASKETS[basket])]
    val = d[["2024", "2025"]].mean(axis=1) if col is None else d[col]
    return val.groupby(d["bairro"]).sum()


def to_distrito(counts, xw, geo, treatment, fill, denom=None):
    """Contagem por DP -> valor por distrito.

    A: média dos DPs do distrito; B: soma. denom: série alinhada a `geo` (população/100k ou
    área); None = contagem bruta. Distritos sem DP herdam a TAXA do vizinho (nearest) ou a
    média da subprefeitura: copiar a contagem e dividir pela população do próprio distrito
    infla distritos pequenos (ex.: Marsilac, 11 mil habitantes)."""
    x = xw.assign(t=xw["bairro"].map(counts).fillna(0))
    g = x.groupby("distrito")["t"]
    direct = g.mean() if treatment == "A" else g.sum()
    if denom is not None:
        direct = direct / denom.loc[direct.index]
    out = direct.reindex(geo.index)
    cen = geo.loc[direct.index, "cen"]
    for d in [d for d in geo.index if d not in direct.index]:
        if fill == "subpref":
            same = geo[(geo["sub"] == geo.loc[d, "sub"]) & geo.index.isin(direct.index)].index
            if len(same):
                out[d] = direct[same].mean()
                continue
        out[d] = direct[cen.distance(geo.loc[d, "cen"]).idxmin()]
    return out


def main():
    cr = pd.read_csv(
        first_existing(
            "data/processed/ISP/dados_criminais_sao_paulo_2025.csv",
            "data/processed/SSP/dados_criminais_sao_paulo_2025.csv",
        )
    )
    cr[["2024", "2025"]] = cr[["2024", "2025"]].fillna(0)
    cr["bairro"] = cr["DP"].str.split(" - ").str[-1].str.strip()
    cr = cr[~cr["NATUREZA2"].str.startswith("Nº DE VÍTIMAS")]
    xw = pd.read_csv("data/reference/dp_distrito_crosswalk.csv")
    pop = pd.read_csv(EXT / "populacao_distrito_2022.csv").set_index("distrito")["populacao_2022"]
    geo = gpd.read_file(EXT / "distrito_municipal.geojson")
    geo["distrito"] = geo["nm_distrito_municipal"].map(norm)
    geo = geo.set_index("distrito").to_crs(31983)
    geo["cen"] = geo.geometry.centroid
    geo["sub"] = geo["cd_identificador_subprefeitura"]
    area_km2 = geo.geometry.area / 1e6
    assert set(pop.index) == set(geo.index)

    configs = list(
        itertools.product(
            BASKETS, WINDOWS, ["100k", "km2", "n"], ["A", "B"], ["nearest", "subpref"]
        )
    )
    cols = {}
    for basket, window, denom, treat, fill in configs:
        den = {"100k": pop / 1e5, "km2": area_km2, "n": None}[denom]
        cols["|".join((basket, window, denom, treat, fill))] = to_distrito(
            dp_counts(cr, basket, window), xw, geo, treat, fill, den
        )
    val = pd.DataFrame(cols)
    rank = val.rank(ascending=False)
    base = "|".join(BASELINE)
    # robustez: só configurações que são taxas (contagem bruta não compara distritos de tamanhos
    # diferentes; ela entra apenas na tabela de efeitos)
    rate_rank = rank[[k for k in rank.columns if "|n|" not in k]]

    # --- robustez por distrito -------------------------------------------------------------
    top = rate_rank <= 24  # quartil mais perigoso
    rob = pd.DataFrame(
        {
            "pop_2022": pop,
            "posicao_base": rank[base].astype(int),
            "posicao_mediana": rate_rank.median(axis=1),
            "posicao_min": rate_rank.min(axis=1).astype(int),
            "posicao_max": rate_rank.max(axis=1).astype(int),
            "pct_configs_no_top_quartil": (top.mean(axis=1) * 100).round(0),
        }
    )
    rob["faixa"] = rob["posicao_max"] - rob["posicao_min"]
    rob["classe"] = np.select(
        [rob.pct_configs_no_top_quartil >= 90, rob.pct_configs_no_top_quartil <= 10],
        ["risco alto robusto", "risco baixo robusto"],
        "sensivel as escolhas",
    )
    OUT.mkdir(exist_ok=True)
    rob.sort_values("posicao_mediana").to_csv(
        OUT / "crime_sensitivity_robustez.csv", index_label="distrito"
    )
    pd.concat({"valor": val, "posicao": rank}, axis=1).round(2).to_csv(
        OUT / "crime_sensitivity_ranking.csv", index_label="distrito"
    )

    # --- efeito de cada escolha isolada (vs. baseline) -------------------------------------
    b = dict(zip(("basket", "window", "denom", "treat", "fill"), BASELINE))
    rows = []
    for dim, options in (
        ("basket", BASKETS),
        ("window", WINDOWS),
        ("denom", ["100k", "km2", "n"]),
        ("treat", ["A", "B"]),
        ("fill", ["nearest", "subpref"]),
    ):
        for o in options:
            if o == b[dim]:
                continue
            key = "|".join(o if k == dim else b[k] for k in b)
            top_b, top_o = set(rank[base].nsmallest(10).index), set(rank[key].nsmallest(10).index)
            rows.append((dim, o, spearmanr(val[base], val[key])[0], len(top_b & top_o)))
    eff = pd.DataFrame(rows, columns=["escolha", "alternativa", "spearman_vs_base", "top10_comum"])
    eff.to_csv(OUT / "crime_sensitivity_efeitos.csv", index=False)

    # --- figura ----------------------------------------------------------------------------
    fig, ax = plt.subplots(1, 2, figsize=(17, 7), gridspec_kw={"width_ratios": [1, 1.15]})
    e = eff.assign(rotulo=eff.escolha + " = " + eff.alternativa).sort_values("spearman_vs_base")
    sns.barplot(data=e, y="rotulo", x="spearman_vs_base", color="#4c72b0", ax=ax[0])
    ax[0].set_xlim(min(0.4, e.spearman_vs_base.min() - 0.05), 1)
    ax[0].axvline(1, color="gray", lw=0.5)
    ax[0].set_title("Uma escolha por vez vs. base\n(" + " / ".join(BASELINE) + ")")
    ax[0].set_xlabel("Spearman do ranking de distritos (1 = idêntico)")
    ax[0].set_ylabel("")
    r = rob.sort_values("posicao_mediana")
    pick = pd.concat([r.head(12), r.tail(8)])
    y = np.arange(len(pick))[::-1]
    ax[1].hlines(y, pick.posicao_min, pick.posicao_max, color="#999999", lw=3)
    ax[1].scatter(pick.posicao_mediana, y, color="#c44e52", zorder=3, label="mediana")
    ax[1].set_yticks(y)
    ax[1].set_yticklabels([d.title() for d in pick.index], fontsize=8)
    ax[1].invert_xaxis()
    ax[1].set_xlabel(
        f"posição no ranking de crime (1 = mais crime), {rate_rank.shape[1]} configurações (taxas)"
    )
    ax[1].set_title(
        "12 distritos de maior e 8 de menor risco mediano:\nfaixa de posição entre as configurações"
    )
    ax[1].legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "crime_sensitivity.png", dpi=140)

    print(f"{len(configs)} configuracoes | baseline: {base}")
    print(eff.sort_values("spearman_vs_base").to_string(index=False, float_format="%.2f"))
    print(rob.classe.value_counts().to_string())


if __name__ == "__main__":
    main()

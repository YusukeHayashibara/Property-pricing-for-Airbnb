"""Crime por distrito: crosswalk rascunho vs revisado (figura para os slides).

Uso (na raiz do repositório):  python scripts/plot_crime_before_after.py

Entrada:
  data/reference/dp_distrito_crosswalk.csv  (colunas distrito e distrito_rascunho)
  data/processed/{ISP,SSP}/dados_criminais_sao_paulo_2025.csv
  data/external/distrito_municipal.geojson
Saída:
  outputs/crime_crosswalk_antes_depois.png
  outputs/crime_crosswalk_ranking.csv   (ranking e mudança por distrito)

Metodologia idêntica à de notebooks/aggregation.ipynb: ocorrências 2025 (sem as linhas
"Nº DE VÍTIMAS"), média por DP dentro do distrito, e distritos sem DP herdam o valor do
distrito mais próximo (centroides em EPSG:31983).
"""
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

EXT = Path("data/external")
OUT = Path("outputs")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def first_existing(*paths):
    for p in paths:
        if Path(p).exists():
            return Path(p)
    raise FileNotFoundError("nenhum de: " + ", ".join(map(str, paths)))


def crime_by_distrito(xw, col, total_by_dp, centroids):
    """Média de ocorrências por DP dentro do distrito; sem DP => vizinho mais próximo."""
    x = xw.assign(t=xw["bairro"].map(total_by_dp))
    direct = x.groupby(col)["t"].sum() / x.groupby(col)["bairro"].nunique()
    have = centroids[centroids.index.isin(direct.index)]
    miss = centroids[~centroids.index.isin(direct.index)]
    nearest = {
        d: have.distance(c).idxmin() for d, c in miss.items()
    }
    value = pd.concat([direct, direct.loc[list(nearest.values())].set_axis(list(nearest))])
    imputed = pd.Series(False, index=centroids.index)
    imputed.loc[list(nearest)] = True
    return value.reindex(centroids.index), imputed


def main():
    cr = pd.read_csv(
        first_existing(
            "data/processed/ISP/dados_criminais_sao_paulo_2025.csv",
            "data/processed/SSP/dados_criminais_sao_paulo_2025.csv",
        )
    )
    cr["2025"] = cr["2025"].fillna(0)
    cr["bairro"] = cr["DP"].str.split(" - ").str[-1].str.strip()
    occ = cr[~cr["NATUREZA2"].str.startswith("Nº DE VÍTIMAS")]
    total_by_dp = occ.groupby("bairro")["2025"].sum()

    xw = pd.read_csv("data/reference/dp_distrito_crosswalk.csv")
    dist = gpd.read_file(EXT / "distrito_municipal.geojson")
    dist["distrito"] = dist["nm_distrito_municipal"].map(norm)
    dist = dist.set_index("distrito")
    centroids = dist.to_crs(31983).geometry.centroid

    old, old_imp = crime_by_distrito(xw, "distrito_rascunho", total_by_dp, centroids)
    new, new_imp = crime_by_distrito(xw, "distrito", total_by_dp, centroids)

    rk_old = old.rank(ascending=False)
    rk_new = new.rank(ascending=False)
    delta = rk_old - rk_new  # >0: sobe no ranking de crime (mais crime que antes)
    rho = spearmanr(old, new)[0]

    table = pd.DataFrame(
        {
            "crime_rascunho": old.round(1),
            "crime_revisado": new.round(1),
            "posicao_rascunho": rk_old.astype(int),
            "posicao_revisado": rk_new.astype(int),
            "mudanca_posicoes": delta.astype(int),
            "imputado_rascunho": old_imp,
            "imputado_revisado": new_imp,
        }
    ).sort_values("mudanca_posicoes", key=abs, ascending=False)
    OUT.mkdir(exist_ok=True)
    table.to_csv(OUT / "crime_crosswalk_ranking.csv", index_label="distrito")

    vmax = max(old.max(), new.max())
    fig, axes = plt.subplots(1, 3, figsize=(19, 7.2))
    for ax, ser, imp, title in (
        (axes[0], old, old_imp, "Rascunho (geocodificação do nome)"),
        (axes[1], new, new_imp, "Crosswalk revisado (endereço do DP)"),
    ):
        g = dist.assign(v=ser)
        g.plot(column="v", cmap="YlOrRd", vmin=0, vmax=vmax, ax=ax, edgecolor="white",
               linewidth=0.3)
        g[imp].plot(ax=ax, facecolor="none", edgecolor="#555555", hatch="///", linewidth=0.2)
        ax.set_title(f"{title}\n{int((~imp).sum())} distritos com DP, {int(imp.sum())} imputados")
        ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(0, vmax))
    fig.colorbar(sm, ax=axes[:2], fraction=0.025, pad=0.01,
                 label="ocorrências 2025 por DP (média no distrito)")

    lim = float(delta.abs().max())
    g = dist.assign(d=delta)
    g.plot(column="d", cmap="RdBu_r", vmin=-lim, vmax=lim, ax=axes[2], edgecolor="white",
           linewidth=0.3)
    axes[2].set_title("Mudança no ranking de crime\n(vermelho: sobe, azul: desce)")
    axes[2].set_axis_off()
    sm2 = plt.cm.ScalarMappable(cmap="RdBu_r", norm=plt.Normalize(-lim, lim))
    fig.colorbar(sm2, ax=axes[2], fraction=0.04, pad=0.01, label="posições")
    fig.suptitle(
        f"Crime por distrito: efeito de corrigir o crosswalk DP → distrito "
        f"(Spearman {rho:.2f}; {int((delta.abs() >= 10).sum())} distritos mudam ≥10 posições)",
        fontsize=13,
    )
    fig.savefig(OUT / "crime_crosswalk_antes_depois.png", dpi=150, bbox_inches="tight")
    print(f"Spearman {rho:.3f} | >=10 posicoes: {int((delta.abs() >= 10).sum())} | "
          f">=20: {int((delta.abs() >= 20).sum())}")
    print(table.head(8).to_string())


if __name__ == "__main__":
    main()

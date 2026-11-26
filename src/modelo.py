"""Modelo "quanto a sua casa renderia no Airbnb" (passos A a E).

    [A] diária        modelo hedônico por anúncio (gradient boosting quantílico, log-preço)
    [B] foto          ajuste do resíduo de [A] pelo embedding CLIP da capa
    [C] ocupação      distribuição por distrito × perfil, encolhida para tipologia × perfil e perfil
    [D] receita       diária × ocupação por Monte Carlo
    [E] investimento  custo pelo IPTU (venal/m² do distrito e do tipo) → yield e score por distrito

O treino e a avaliação estão em notebooks/modelagem.ipynb; aqui ficam as funções reutilizáveis
e o simulador (`avaliar_casa`). Só entram como features coisas que o dono da casa sabe informar:
nada de reviews, notas, histórico do anfitrião ou mínimo de noites.
"""
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neighbors import BallTree

RAIZ = Path(__file__).resolve().parents[1]
PROC, EXT, RAW = RAIZ / "data" / "processed", RAIZ / "data" / "external", RAIZ / "data" / "raw"
DIR_MODELO = PROC / "modelo"

SEED = 42
CENTRO = (-23.5505, -46.6333)       # Praça da Sé (mesmo marco do eda_agregado)
MAX_QUOTE_NIGHTS, OUTLIER_K = 3, 3.0  # mesmo recorte de preço comparável do eda_agregado (price_ok)
K_VIZINHOS = 15                       # vizinhos para a feature espacial de preço
QUANTIS = (0.1, 0.5, 0.9)
RAIO_TERRA_KM = 6371.0


def chave(s):
    """Nome sem acento e em maiúsculas (o Airbnb escreve "Sao Rafael", o IPTU "SAO RAFAEL")."""
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()


def haversine_km(lat, lon, lat0, lon0):
    lat, lon, lat0, lon0 = map(np.radians, (lat, lon, lat0, lon0))
    a = np.sin((lat - lat0) / 2) ** 2 + np.cos(lat) * np.cos(lat0) * np.sin((lon - lon0) / 2) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------------------------
COLS_LISTINGS = ["id", "host_id", "listing_url", "picture_url", "latitude", "longitude", "distrito", "regiao5",
                 "property_type", "room_type", "accommodates", "bathrooms", "bathrooms_text", "bedrooms",
                 "beds", "price_num", "price_quote_checkin_date", "price_quote_checkout_date", "last_scraped",
                 "first_review", "number_of_reviews_ltm", "estimated_occupancy_l365d", "estimated_revenue_l365d"]


def carregar_anuncios():
    """listings_aggregated + amenities, com log-preço, `price_ok` e as features do imóvel."""
    d = pd.read_csv(PROC / "listings_aggregated.csv", usecols=COLS_LISTINGS, low_memory=False)
    for c in ["price_quote_checkin_date", "price_quote_checkout_date", "last_scraped", "first_review"]:
        d[c] = pd.to_datetime(d[c], errors="coerce")
    d["quote_nights"] = (d["price_quote_checkout_date"] - d["price_quote_checkin_date"]).dt.days
    d["log_price"] = np.log(d["price_num"])

    # price_ok: cotação curta e sem outlier extremo (cerca de Tukey no log, k = 3), igual ao eda_agregado
    curto = d["log_price"].where(d["quote_nights"] <= MAX_QUOTE_NIGHTS).dropna()
    q1, q3 = curto.quantile([0.25, 0.75])
    lo, hi = q1 - OUTLIER_K * (q3 - q1), q3 + OUTLIER_K * (q3 - q1)
    d["price_ok"] = d["price_num"].notna() & (d["quote_nights"] <= MAX_QUOTE_NIGHTS) & d["log_price"].between(lo, hi)

    am = pd.read_csv(PROC / "Airbnb" / "amenities.csv")
    am = am[["id"] + [c for c in am.columns if c.startswith(("am_", "decl_")) and c != "am_count"]]
    d = d.merge(am, on="id", how="left")
    amen = [c for c in am.columns if c != "id"]
    d[amen] = d[amen].fillna(0).astype(int)
    return d


def amenity_cols(d):
    return [c for c in d.columns if c.startswith(("am_", "decl_"))]


def montar_features(d, categorias=None):
    """Features do imóvel a partir de colunas que o usuário consegue informar.

    `categorias` (dict) fixa os níveis de room_type/property_type vistos no treino; passe o mesmo dict
    na previsão para que os códigos batam.
    """
    X = pd.DataFrame(index=d.index)
    if categorias is None:
        top = d["property_type"].value_counts().index[:20].tolist()
        categorias = {"room_type": sorted(d["room_type"].dropna().unique()), "property_type": top + ["Outros"]}
    pt = d["property_type"].where(d["property_type"].isin(categorias["property_type"]), "Outros")
    X["room_type"] = pd.Categorical(d["room_type"], categories=categorias["room_type"]).codes.astype(float)
    X["property_type"] = pd.Categorical(pt, categories=categorias["property_type"]).codes.astype(float)
    X.loc[X["room_type"] < 0, "room_type"] = np.nan
    X.loc[X["property_type"] < 0, "property_type"] = np.nan
    for c in ["accommodates", "bedrooms", "beds", "bathrooms"]:
        X[c] = pd.to_numeric(d[c], errors="coerce")
    bt = d.get("bathrooms_text", pd.Series("", index=d.index)).fillna("")
    X["bath_shared"] = bt.str.contains("shared", case=False).astype(int)
    amen = amenity_cols(d)
    X[amen] = d[amen]
    X["n_amenities_top"] = d[[c for c in amen if c.startswith("am_")]].sum(axis=1)
    X["latitude"], X["longitude"] = d["latitude"], d["longitude"]
    X["dist_centro_km"] = haversine_km(d["latitude"], d["longitude"], *CENTRO)
    return X, categorias


CATEGORICAS = ["room_type", "property_type"]


# ---------------------------------------------------------------------------------------------
# [A] Feature espacial: log-preço médio dos vizinhos
# ---------------------------------------------------------------------------------------------
class VizinhancaPreco:
    """Média do log-preço (ajustado por capacidade) dos K anúncios mais próximos do treino.

    No treino, os vizinhos de um anúncio excluem o próprio anfitrião: anfitriões com várias unidades
    no mesmo prédio passariam o próprio preço para a feature (vazamento). Na previsão, todos os
    anúncios do treino valem (na validação cruzada por anfitrião, o anfitrião do teste não está lá).
    """

    def __init__(self, k=K_VIZINHOS):
        self.k = k

    def fit(self, lat, lon, y, host, acc):
        self.coords = np.radians(np.c_[lat, lon])
        # tira o efeito da capacidade antes de fazer a média: a feature mede "quão cara é a vizinhança"
        # e não "quão grandes são os imóveis vizinhos"
        self.b = np.polyfit(np.log(acc), y, 1)
        self.r = y - np.polyval(self.b, np.log(acc))
        self.host = np.asarray(host)
        self.tree = BallTree(self.coords, metric="haversine")
        return self

    def _media(self, idx, dist, excluir_host=None):
        out = np.empty(len(idx))
        dmed = np.empty(len(idx))
        for i, (ii, dd) in enumerate(zip(idx, dist)):
            if excluir_host is not None:
                m = self.host[ii] != excluir_host[i]
                ii, dd = ii[m], dd[m]
            ii, dd = ii[: self.k], dd[: self.k]
            out[i] = self.r[ii].mean()
            dmed[i] = np.median(dd) * RAIO_TERRA_KM
        return out, dmed

    def transform_treino(self):
        # pede vizinhos a mais para sobrar K depois de tirar o mesmo anfitrião
        dist, idx = self.tree.query(self.coords, k=min(self.k * 6, len(self.coords)))
        return self._media(idx, dist, excluir_host=self.host)

    def transform(self, lat, lon):
        dist, idx = self.tree.query(np.radians(np.c_[lat, lon]), k=self.k)
        return self._media(idx, dist)


def _gbm(loss="squared_error", quantile=None, cat_mask=None):
    kw = dict(max_iter=500, learning_rate=0.05, min_samples_leaf=30, l2_regularization=1.0,
              random_state=SEED, categorical_features=cat_mask)
    if loss == "quantile":
        kw.update(loss="quantile", quantile=quantile)
    return HistGradientBoostingRegressor(**kw)


class ModeloDiaria:
    """[A] Três modelos quantílicos (q10, q50, q90) do log-preço + calibração conformal do intervalo."""

    def __init__(self, cols, usar_vizinhanca=True):
        self.cols, self.usar_vizinhanca = list(cols), usar_vizinhanca

    def _matriz(self, X, viz=None):
        M = X[self.cols].copy()
        if self.usar_vizinhanca:
            M["viz_logp"], M["viz_dist_km"] = viz
        return M

    def fit(self, X, y, host):
        if self.usar_vizinhanca:
            self.viz = VizinhancaPreco().fit(X["latitude"].values, X["longitude"].values, y, host,
                                             X["accommodates"].clip(lower=1).values)
            v = self.viz.transform_treino()
        else:
            v = None
        M = self._matriz(X, v)
        self.feature_names = list(M.columns)
        mask = np.array([c in CATEGORICAS for c in M.columns])
        self.modelos = {q: _gbm("quantile", q, mask).fit(M.values, y) for q in QUANTIS}
        self.correcao = 0.0  # preenchida por `calibrar`
        return self

    def predict(self, X):
        v = self.viz.transform(X["latitude"].values, X["longitude"].values) if self.usar_vizinhanca else None
        M = self._matriz(X, v).values
        p = pd.DataFrame({f"q{int(q * 100)}": m.predict(M) for q, m in self.modelos.items()}, index=X.index)
        # quantis não podem cruzar; a correção conformal alarga (ou estreita) o intervalo de 80%
        p["q10"], p["q90"] = np.minimum(p["q10"], p["q50"]) - self.correcao, np.maximum(p["q90"], p["q50"]) + self.correcao
        return p

    def calibrar(self, y, pred_oof, cobertura=0.8):
        """Regressão quantílica conformal (CQR): escolhe a folga que dá `cobertura` nas previsões fora da amostra."""
        e = np.maximum(pred_oof["q10"] - y, y - pred_oof["q90"])
        n = len(e)
        self.correcao = float(np.quantile(e, min(1, np.ceil((n + 1) * cobertura) / n)))
        return self.correcao


def prever_oof(X, y, host, cols, n_splits=5, usar_vizinhanca=True):
    """Previsões fora da amostra com GroupKFold por anfitrião (nenhum anfitrião em treino e teste)."""
    from sklearn.model_selection import GroupKFold
    out = []
    for tr, te in GroupKFold(n_splits).split(X, y, host):
        m = ModeloDiaria(cols, usar_vizinhanca).fit(X.iloc[tr], y[tr], host[tr])
        out.append(m.predict(X.iloc[te]))
    return pd.concat(out).loc[X.index]


def metricas(y, pred):
    from sklearn.metrics import r2_score
    erro = np.abs(np.expm1(pred["q50"] - y))
    return {"R² (log)": r2_score(y, pred["q50"]), "erro % mediano": 100 * np.median(erro),
            "cobertura 80%": 100 * np.mean((y >= pred["q10"]) & (y <= pred["q90"])),
            "largura mediana (×)": float(np.median(np.exp(pred["q90"] - pred["q10"])))}


# ---------------------------------------------------------------------------------------------
# Moran's I (pesos KNN, padronizados por linha) — sem depender do PySAL
# ---------------------------------------------------------------------------------------------
def moran_knn(valores, lat, lon, k=8, n_perm=199, seed=SEED):
    from scipy import sparse
    z = np.asarray(valores, float) - np.mean(valores)
    tree = BallTree(np.radians(np.c_[lat, lon]), metric="haversine")
    _, idx = tree.query(np.radians(np.c_[lat, lon]), k=k + 1)
    n = len(z)
    W = sparse.csr_matrix((np.full(n * k, 1 / k), (np.repeat(np.arange(n), k), idx[:, 1:].ravel())), shape=(n, n))
    I = float(z @ (W @ z) / (z @ z))
    rng = np.random.default_rng(seed)
    perm = np.array([(lambda zp: zp @ (W @ zp) / (zp @ zp))(rng.permutation(z)) for _ in range(n_perm)])
    return {"I": I, "p_sim": (1 + np.sum(perm >= I)) / (n_perm + 1), "E[I]": -1 / (n - 1)}


# ---------------------------------------------------------------------------------------------
# [C] Ocupação
# ---------------------------------------------------------------------------------------------
Q_OCUP = (0.1, 0.25, 0.5, 0.75, 0.9)


def perfil(room_type, accommodates):
    """Perfil = (inteiro | quarto) × faixa de capacidade."""
    tipo = np.where(pd.Series(room_type).eq("Entire home/apt"), "inteiro", "quarto")
    cap = pd.cut(pd.Series(accommodates).astype(float), [0, 2, 4, np.inf], labels=["1-2", "3-4", "5+"]).astype(str)
    return pd.Series(tipo, index=cap.index) + " " + cap


def tabela_ocupacao(d, tipologia, m=15):
    """Quantis da ocupação estimada por distrito × perfil, encolhidos em cascata.

    Base: anúncios **maduros** (1ª avaliação há ≥ 12 meses, senão a janela de 365 dias está truncada)
    e **em operação** (≥ 1 avaliação em 12 meses). `p_inativo` é a fração dos maduros sem avaliação
    em 12 meses — o risco de o anúncio não "pegar" — encolhida do mesmo jeito.

    Encolhimento (bayes empírico simples): q = (n·q_célula + m·q_pai) / (n + m), com
    distrito×perfil → tipologia×perfil → perfil. Com n pequeno o distrito herda o grupo.
    """
    maduro = d["first_review"] <= d["last_scraped"] - pd.Timedelta(days=365)
    base = d[maduro].copy()
    base["perfil"] = perfil(base["room_type"], base["accommodates"]).values
    base["tipologia"] = base["distrito"].map(tipologia)
    base["inativo"] = base["number_of_reviews_ltm"].eq(0).astype(float)
    ativos = base[~base["inativo"].astype(bool)]

    def resumo(g, keys):
        q = g.groupby(keys)["estimated_occupancy_l365d"].quantile(list(Q_OCUP)).unstack()
        q.columns = [f"p{int(x * 100)}" for x in Q_OCUP]
        q["n"] = g.groupby(keys).size()
        return q

    nivel_perfil = resumo(ativos, ["perfil"])
    nivel_tip = resumo(ativos, ["tipologia", "perfil"])
    nivel_dist = resumo(ativos, ["distrito", "perfil"])
    inat = {k: base.groupby(list(k))["inativo"].agg(["mean", "size"])
            for k in (("perfil",), ("tipologia", "perfil"), ("distrito", "perfil"))}

    def encolher(valor, n, pai):
        return (n * valor + m * pai) / (n + m)

    qcols = [f"p{int(x * 100)}" for x in Q_OCUP]
    linhas = []
    for dist in sorted(tipologia.index):
        tip = tipologia[dist]
        for pf in nivel_perfil.index:
            # nível 1: perfil na cidade
            q = nivel_perfil.loc[pf, qcols].values.astype(float)
            pi = inat[("perfil",)].loc[pf, "mean"]
            # nível 2: tipologia × perfil
            n_tip = 0
            if (tip, pf) in nivel_tip.index:
                n_tip = int(nivel_tip.loc[(tip, pf), "n"])
                q = encolher(nivel_tip.loc[(tip, pf), qcols].values.astype(float), n_tip, q)
            if (tip, pf) in inat[("tipologia", "perfil")].index:
                r = inat[("tipologia", "perfil")].loc[(tip, pf)]
                pi = encolher(r["mean"], r["size"], pi)
            # nível 3: distrito × perfil
            n = 0
            if (dist, pf) in nivel_dist.index:
                n = int(nivel_dist.loc[(dist, pf), "n"])
                q = encolher(nivel_dist.loc[(dist, pf), qcols].values.astype(float), n, q)
            if (dist, pf) in inat[("distrito", "perfil")].index:
                r = inat[("distrito", "perfil")].loc[(dist, pf)]
                pi = encolher(r["mean"], r["size"], pi)
            q = np.maximum.accumulate(np.clip(q, 0, 365))   # quantis em ordem e dentro do ano
            linhas.append({"distrito": dist, "perfil": pf, "tipologia": tip, "n_distrito": n,
                           "n_tipologia": n_tip, **dict(zip(qcols, q)), "p_inativo": float(pi)})
    return pd.DataFrame(linhas).set_index(["distrito", "perfil"])


# ---------------------------------------------------------------------------------------------
# [D] Receita por Monte Carlo
# ---------------------------------------------------------------------------------------------
Z90 = 1.2816


def amostrar_log_preco(q10, q50, q90, n, rng):
    """Normal assimétrica (split normal) no log, com q10/q50/q90 do modelo [A] (+[B])."""
    s_lo, s_hi = max(q50 - q10, 1e-6) / Z90, max(q90 - q50, 1e-6) / Z90
    z = rng.standard_normal(n)
    return q50 + np.where(z < 0, z * s_lo, z * s_hi)


def amostrar_ocupacao(quantis, n, rng):
    """Inversa da CDF linear por partes entre p10…p90; caudas extrapoladas até 0 e 365 noites."""
    qs = np.r_[0.0, Q_OCUP, 1.0]
    q = np.asarray(quantis, float)
    lo = max(0.0, q[0] - (q[1] - q[0]) * 0.1 / 0.15)
    hi = min(365.0, q[-1] + (q[-1] - q[-2]) * 0.1 / 0.15)
    return np.interp(rng.uniform(size=n), qs, np.r_[lo, q, hi])


def simular_receita(q10, q50, q90, quantis_ocup, n=5000, seed=SEED):
    """Receita anual = diária × noites ocupadas. Diária e ocupação são sorteadas de forma independente:
    entre distritos, preço e ocupação têm ρ = +0,09 (eda_agregado §18)."""
    rng = np.random.default_rng(seed)
    preco = np.exp(amostrar_log_preco(q10, q50, q90, n, rng))
    noites = amostrar_ocupacao(quantis_ocup, n, rng)
    return preco * noites, preco, noites


# ---------------------------------------------------------------------------------------------
# [E] Investimento: IPTU por distrito × tipo
# ---------------------------------------------------------------------------------------------
RES = ["Residência", "Apartamento Em Condomínio",
       "Residência E Outro Uso (Predominância Residencial)",
       "Residência Coletiva, Exclusive Cortiço (Mais De Uma Residência No Lote)",
       "Prédio De Apartamento, Não Em Condomínio, De Uso Exclusivamente Residencial",
       "Flat Residencial Em Condomínio"]


def carregar_iptu():
    """Valor venal/m² dos imóveis residenciais com distrito e tipo (apartamento × casa).

    Mesmo cálculo de initialAnalysis/distribuicao_valor_m2_distrito.ipynb.
    """
    cols = ["numero_contribuinte", "finalidade_imovel", "valor_terreno", "valor_construcao",
            "area_terreno", "area_construida", "fracao_ideal", "fator_obsolescencia"]
    it = pd.read_csv(PROC / "IPTU" / "iptu_2025_clean.csv", usecols=cols, dtype={"numero_contribuinte": str})
    q2d = pd.read_csv(EXT / "quadra_to_distrito.csv", dtype={"sq": str}).set_index("sq")["distrito"]
    it["distrito"] = it["numero_contribuinte"].str.zfill(11).str[:6].map(q2d)
    r = it[it["finalidade_imovel"].isin(RES) & it["distrito"].notna() & (it["area_construida"] > 0)].copy()
    del it
    r["venal_m2"] = (r["area_terreno"] * r["fracao_ideal"] * r["valor_terreno"]
                     + r["area_construida"] * r["valor_construcao"] * r["fator_obsolescencia"]) / r["area_construida"]
    lo, hi = r["venal_m2"].quantile([0.001, 0.999])
    r = r[r["venal_m2"].between(lo, hi)]
    r["tipo"] = np.where(r["finalidade_imovel"].str.contains("Apartamento|Flat"), "apartamento", "casa")
    return r[["distrito", "tipo", "venal_m2", "area_construida"]]


def tipo_imovel(property_type):
    """Mapeia o property_type do Airbnb para o tipo do IPTU (apartamento × casa)."""
    s = pd.Series(property_type).fillna("").str.lower()
    casa = s.str.contains("home|house|casa|townhouse|villa|cottage|bungalow|chalet|farm|tiny")
    return pd.Series(np.where(casa, "casa", "apartamento"), index=s.index)


# ---------------------------------------------------------------------------------------------
# Simulador
# ---------------------------------------------------------------------------------------------
def carregar_bundle(path=DIR_MODELO / "modelo.joblib"):
    import joblib
    return joblib.load(path)


# amenity do checklist → coluna decl_* correspondente (text_processing.ipynb)
DECL = {"pool": "decl_pool", "gym": "decl_gym", "elevator": "decl_elevator", "air_conditioning": "decl_aircon",
        "washer": "decl_washer", "dedicated_workspace": "decl_workspace", "balcony": "decl_balcony",
        "parking": "decl_parking", "bbq": "decl_bbq", "city_view": "decl_cityview"}


def _casa_para_frame(casa, bundle):
    """dict do usuário → DataFrame de uma linha com as mesmas colunas do treino."""
    d = {k: [v] for k, v in casa.items() if k != "amenities"}
    row = pd.DataFrame(d)
    if "latitude" not in row or pd.isna(row.loc[0, "latitude"]):
        lat, lon = bundle["centro_distrito"].loc[chave(casa["distrito"])]
        row["latitude"], row["longitude"] = lat, lon
    for c in bundle["amenities"]:
        row[c] = 0
    for a in casa.get("amenities", []):
        nome = a if a.startswith(("am_", "decl_")) else f"am_{a}"
        if nome in row:
            row[nome] = 1
        # as colunas decl_* agrupam variações do mesmo item ("piscina", "piscina compartilhada"…)
        if DECL.get(a.removeprefix("am_")) in row:
            row[DECL[a.removeprefix("am_")]] = 1
    row["bathrooms_text"] = "shared" if casa.get("banheiro_compartilhado") else ""
    return row


def prever_diaria(row, bundle, emb_foto=None):
    """Quantis do log da diária por [A]. O ajuste da foto [B] vem à parte e **não** desloca a faixa:
    na validação ele não reduziu o erro mediano (ver modelagem.ipynb §3)."""
    X, _ = montar_features(row, bundle["categorias"])
    p = bundle["modelo_A"].predict(X).iloc[0].to_dict()
    p["ajuste_foto"] = 0.0
    if emb_foto is not None and bundle.get("modelo_B") is not None:
        p["ajuste_foto"] = float(bundle["modelo_B"].predict(emb_foto.reshape(1, -1))[0])
    return p


def avaliar_casa(casa, bundle, foto=None, n_sim=5000, distritos_alternativos=True):
    """Ponto de entrada do produto.

    casa: dict com room_type, property_type, accommodates, bedrooms, beds, bathrooms, amenities (lista),
          area_m2, e latitude/longitude **ou** distrito. `banheiro_compartilhado` opcional.
    foto: caminho de uma foto (opcional) → ajuste [B], conceitos visuais e comparáveis.
    """
    row = _casa_para_frame(casa, bundle)
    lat, lon = float(row.loc[0, "latitude"]), float(row.loc[0, "longitude"])
    dist = chave(casa["distrito"]) if casa.get("distrito") else localizar_distrito(lat, lon, bundle)

    emb = None
    if foto is not None and bundle.get("modelo_B") is not None:
        from src.imagens import embedding_clip
        emb = embedding_clip([foto])[0]
    p = prever_diaria(row, bundle, emb)

    pf = perfil([casa["room_type"]], [casa["accommodates"]]).iloc[0]
    oc = bundle["ocupacao"].loc[(dist, pf)]
    qocc = oc[[f"p{int(x * 100)}" for x in Q_OCUP]].values.astype(float)
    rec, _, _ = simular_receita(p["q10"], p["q50"], p["q90"], qocc, n_sim)

    tipo = tipo_imovel([casa.get("property_type", "")]).iloc[0]
    custo, custo_lo, custo_hi = custo_imovel(dist, tipo, casa.get("area_m2", np.nan), bundle)

    out = {
        "distrito": dist, "perfil": pf, "tipo_iptu": tipo,
        "diaria": {"p10": np.exp(p["q10"]), "p50": np.exp(p["q50"]), "p90": np.exp(p["q90"]),
                   "ajuste_foto_%": 100 * np.expm1(p["ajuste_foto"])},
        "ocupacao_noites": dict(zip([f"p{int(x * 100)}" for x in Q_OCUP], qocc)),
        "p_inativo": float(oc["p_inativo"]),
        "receita_anual": {k: float(np.percentile(rec, v)) for k, v in (("p10", 10), ("p50", 50), ("p90", 90))},
        "custo_estimado": custo,
        "custo_faixa_picos": (custo_lo, custo_hi),
        "yield_bruto_%": 100 * float(np.median(rec)) / custo if custo == custo else np.nan,
    }
    out["comparaveis"] = comparaveis(row, bundle, emb)
    if emb is not None and "eixos_conceitos" in bundle:
        out["foto_conceitos"] = conceitos_foto(emb, bundle)
    if distritos_alternativos:
        out["outros_distritos"] = e_se_outro_distrito(casa, bundle)
    return out


def localizar_distrito(lat, lon, bundle):
    """Distrito que contém o ponto (polígonos do GeoSampa); fora deles, o centro mais próximo."""
    from shapely.geometry import Point
    pol = bundle["poligonos"]
    dentro = pol[pol.contains(Point(lon, lat))]
    if len(dentro):
        return dentro.index[0]
    c = bundle["centro_distrito"]
    return c.index[np.argmin(haversine_km(c["lat"].values, c["lon"].values, lat, lon))]


def custo_imovel(dist, tipo, area_m2, bundle):
    """Custo ≈ venal/m² mediano (distrito × tipo) × fator venal→mercado × área.

    Em apartamentos de distritos com venal/m² bimodal, devolve também a faixa entre os dois picos
    (pico1, pico2): os dois picos são, em geral, dois padrões de prédio (ver notebook de modelagem).
    """
    venal = bundle["venal"].get((dist, tipo), bundle["venal"].get((dist, "apartamento"), np.nan))
    f = bundle["fator_mercado"] * area_m2
    lo = hi = np.nan
    if tipo == "apartamento" and dist in bundle["picos"]:
        lo, hi = (v * f for v in bundle["picos"][dist])
    return venal * f, lo, hi


def conceitos_foto(emb, bundle):
    """z de cada conceito (limpeza, luz, decoração…) da foto em relação às capas da amostra."""
    eixos = bundle["eixos_conceitos"]
    s = eixos.values @ emb
    return pd.Series((s - bundle["conceitos_media"]) / bundle["conceitos_dp"], index=eixos.index).round(2)


class AjusteFoto:
    """[B] Ridge no PCA do embedding CLIP prevendo o resíduo de [A], com encolhimento.

    O `fator` (≤ 1) é a inclinação de resíduo_real ~ previsão_fora_da_amostra: se a foto prevê o
    resíduo com ruído, o ajuste é encolhido na mesma proporção.
    """

    def __init__(self, n_comp=64, alpha=10.0):
        self.n_comp, self.alpha = n_comp, alpha

    def _pipe(self):
        from sklearn.decomposition import PCA
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        return make_pipeline(PCA(self.n_comp, random_state=SEED), Ridge(self.alpha))

    def oof(self, emb, resid, grupos, n_splits=5):
        from sklearn.model_selection import GroupKFold
        p = np.zeros(len(resid))
        for tr, te in GroupKFold(n_splits).split(emb, resid, grupos):
            p[te] = self._pipe().fit(emb[tr], resid[tr]).predict(emb[te])
        return p

    def fit(self, emb, resid, grupos):
        p = self.oof(emb, resid, grupos)
        self.fator = float(np.clip(np.polyfit(p, resid, 1)[0], 0, 1))
        self.pipe = self._pipe().fit(emb, resid)
        return self

    def predict(self, emb):
        return self.fator * self.pipe.predict(emb)


def comparaveis(row, bundle, emb=None, n=5, raio_km=3.0):
    """Anúncios reais mais parecidos: mesmo room_type, perto, capacidade/quartos/banheiros parecidos;
    com foto, reordena pela similaridade da capa."""
    base = bundle["base_comparaveis"]
    lat, lon = float(row.loc[0, "latitude"]), float(row.loc[0, "longitude"])
    c = base[base["room_type"] == row.loc[0, "room_type"]].copy()
    c["km"] = haversine_km(c["latitude"], c["longitude"], lat, lon)
    perto = c[c["km"] <= raio_km]
    if len(perto) < 20:
        perto = c.nsmallest(50, "km")
    dif = (np.abs(np.log(perto["accommodates"].clip(lower=1)) - np.log(max(row.loc[0, "accommodates"], 1)))
           + 0.5 * np.abs(perto["bedrooms"].fillna(1) - row.loc[0, "bedrooms"])
           + 0.5 * np.abs(perto["bathrooms"].fillna(1) - row.loc[0, "bathrooms"])
           + perto["km"] / raio_km)
    perto = perto.assign(dissimilaridade=dif)
    if emb is not None and "emb_ids" in bundle:
        pos = pd.Series(np.arange(len(bundle["emb_ids"])), index=bundle["emb_ids"])
        tem = perto["id"].isin(pos.index)
        sim = pd.Series(np.nan, index=perto.index)
        sim[tem] = bundle["emb"][pos[perto.loc[tem, "id"]].values] @ emb
        perto["sim_foto"] = sim
        perto["dissimilaridade"] = perto["dissimilaridade"] + (1 - perto["sim_foto"].fillna(perto["sim_foto"].min() if tem.any() else 0.7)) * 3
    cols = ["id", "listing_url", "distrito", "km", "accommodates", "bedrooms", "bathrooms", "price_num",
            "estimated_occupancy_l365d", "estimated_revenue_l365d"] + (["sim_foto"] if "sim_foto" in perto else [])
    return perto.nsmallest(n, "dissimilaridade")[cols].reset_index(drop=True)


def e_se_outro_distrito(casa, bundle, n_sim=2000):
    """A mesma casa em cada distrito: diária, receita mediana, custo e yield. Base do mapa [E]."""
    linhas = []
    pf = perfil([casa["room_type"]], [casa["accommodates"]]).iloc[0]
    tipo = tipo_imovel([casa.get("property_type", "")]).iloc[0]
    for dist, (lat, lon) in bundle["centro_distrito"].iterrows():
        c = {**casa, "latitude": lat, "longitude": lon, "distrito": dist}
        row = _casa_para_frame(c, bundle)
        p = prever_diaria(row, bundle)
        if (dist, pf) not in bundle["ocupacao"].index:
            continue
        oc = bundle["ocupacao"].loc[(dist, pf)]
        qocc = oc[[f"p{int(x * 100)}" for x in Q_OCUP]].values.astype(float)
        rec, _, _ = simular_receita(p["q10"], p["q50"], p["q90"], qocc, n_sim)
        custo = custo_imovel(dist, tipo, casa.get("area_m2", np.nan), bundle)[0]
        linhas.append({"distrito": dist, "diaria_p50": np.exp(p["q50"]), "ocupacao_p50": qocc[2],
                       "receita_p50": float(np.median(rec)), "p_inativo": float(oc["p_inativo"]),
                       "custo": custo, "yield_%": 100 * float(np.median(rec)) / custo,
                       "crime_violento_mil": bundle["crime"].get(dist, np.nan)})
    return pd.DataFrame(linhas).set_index("distrito").sort_values("yield_%", ascending=False)

import re
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

REF = Path(__file__).resolve().parents[1] / "data" / "reference"

ABREVIACOES = {
    "JD": "JARDIM", "JDIM": "JARDIM", "JRD": "JARDIM",
    "VL": "VILA", "V": "VILA",
    "PQ": "PARQUE", "PRQ": "PARQUE", "PQE": "PARQUE",
    "CJ": "CONJUNTO", "CONJ": "CONJUNTO",
    "HAB": "HABITACIONAL", "HABT": "HABITACIONAL", "HABIT": "HABITACIONAL", "HABITAC": "HABITACIONAL",
    "CID": "CIDADE",
    "STA": "SANTA", "STO": "SANTO",
    "CH": "CHACARA", "CHAC": "CHACARA",
    "CERQ": "CERQUEIRA",
    "SRA": "SENHORA",
    "PRES": "PRESIDENTE", "PRESID": "PRESIDENTE",
    "BRIG": "BRIGADEIRO", "PREF": "PREFEITO", "CEL": "CORONEL",
}

# trechos com mais de um token, aplicados antes da expansao token a token
EXPRESSOES = [
    (r"^C H ", "CONJUNTO HABITACIONAL "),
    (r"^N (S|SRA|SENHORA) ", "NOSSA SENHORA "),
]

# primeiro token que indica complemento do imovel, condominio ou endereco
PREFIXOS_NAO_BAIRRO = {
    "TORRE", "TORRES", "T", "BLOCO", "BLOCOS", "BL", "PREDIO", "TIPO", "ANTIGO",
    "ED", "EDIF", "EDIFICIO", "COND", "CONDOMINIO", "CD", "SUBCOND", "SUBCONDOMINIO",
    "RES", "RESID", "RESIDENCIAL", "LOTE", "LT", "QD", "QUADRA", "SETOR", "LADO",
    "DESDOBRO", "R", "RUA", "AV", "AVENIDA", "AL", "ALAMEDA", "PCA", "PRACA", "TRAV",
    "E", "VAGA", "VAGAS", "VG", "VGS", "DEP", "DEPOSITO", "APTO", "APARTAMENTO", "NUMERO",
}

# palavras que indicam condominio/unidade em qualquer posicao (ED fica so no prefixo
# por causa de BRIGADEIRO ED GOMES)
TOKENS_NAO_BAIRRO = {
    "TORRE", "TORRES", "BLOCO", "COND", "CONDOMINIO", "SUBCOND", "EDIFICIO", "LOTE",
    "RESIDENCE", "HOME", "HOTEL", "FLAT", "TOWER", "TOWERS", "APART", "CD",
    "CONDOMINIUM", "HOUSE", "DUPLEX", "PREMIUM", "DOWNTOWN", "DEPOSITO",
}

# bairros reais com nome curto (as demais strings de ate 4 letras sao fragmentos)
BAIRROS_CURTOS = {"SE", "LUZ", "IPE", "LAPA", "BRAS", "BRAZ", "PARI", "PERY", "MAIA"}

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())

def normalizar(s):
    if pd.isna(s):
        return ""
    s = norm(re.sub(r"[.,;:/\\\-_'\"()]", " ", norm(s)))
    for padrao, troca in EXPRESSOES:
        s = re.sub(padrao, troca, s)
    return " ".join(ABREVIACOES.get(t, t) for t in s.split())

def motivo_descarte(nome, blocklist=frozenset()):
    if not nome:
        return "vazio"
    if nome in blocklist:
        return "blocklist"
    tokens = nome.split()
    if (
        tokens[0] in PREFIXOS_NAO_BAIRRO
        or re.match(r"[A-Z] ?\d", nome)
        or TOKENS_NAO_BAIRRO.intersection(tokens)
    ):
        return "complemento"
    if tokens[0][0].isdigit() or re.search(r"\d{3,}", nome):
        return "endereco"
    if len(nome) <= 4 and nome not in BAIRROS_CURTOS:
        return "fragmento"
    if all(len(t) <= 2 for t in tokens) and nome not in BAIRROS_CURTOS:
        return "fragmento"
    return None

def carregar_sinonimos(path=REF / "bairros_sinonimos.csv"):
    path = Path(path)
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str, comment="#").dropna(subset=["variante", "canonico"])
    return dict(zip(df["variante"].map(normalizar), df["canonico"].map(normalizar)))

def carregar_blocklist(path=REF / "bairros_blocklist.csv"):
    path = Path(path)
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path, dtype=str, comment="#").dropna(subset=["bairro"])
    return frozenset(df["bairro"].map(normalizar))

def padronizar_bairro(bairro, sinonimos=None, blocklist=None):
    sinonimos = carregar_sinonimos() if sinonimos is None else sinonimos
    blocklist = carregar_blocklist() if blocklist is None else frozenset(blocklist)

    unicos = pd.Series(pd.unique(bairro))
    nomes = unicos.map(normalizar).map(lambda n: sinonimos.get(n, n))
    motivos = nomes.map(lambda n: motivo_descarte(n, blocklist))
    tabela = pd.DataFrame(
        {"bairro_limpo": nomes.where(motivos.isna(), np.nan), "motivo_descarte": motivos}
    )
    tabela.index = unicos

    out = tabela.reindex(bairro.to_numpy())
    out.index = bairro.index
    out.insert(0, "bairro_raw", bairro)
    return out

def _distancia_1(a, b):
    if abs(len(a) - len(b)) > 1 or a == b:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i + (len(a) == len(b)):] == b[i + 1:]

def propor_sinonimos(contagens, min_count=100, min_len_token=5):
    freq = contagens[contagens >= min_count].sort_values(ascending=False)
    por_forma = {}
    for nome in freq.index:
        por_forma.setdefault(len(nome.split()), []).append(nome)

    linhas = []
    for nomes in por_forma.values():
        for i, a in enumerate(nomes):
            ta = a.split()
            for b in nomes[i + 1:]:
                tb = b.split()
                difs = [(x, y) for x, y in zip(ta, tb) if x != y]
                if len(difs) == 1 and min(map(len, difs[0])) >= min_len_token and _distancia_1(*difs[0]):
                    linhas.append((b, a, freq[b], freq[a]))
    return pd.DataFrame(linhas, columns=["variante", "canonico", "n_variante", "n_canonico"])

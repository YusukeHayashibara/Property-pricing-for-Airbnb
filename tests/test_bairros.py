import numpy as np
import pandas as pd
import pytest

from src.bairros import (
    carregar_blocklist,
    carregar_sinonimos,
    motivo_descarte,
    normalizar,
    padronizar_bairro,
    propor_sinonimos,
)

def limpo(valor):
    return padronizar_bairro(pd.Series([valor]))["bairro_limpo"].iloc[0]

@pytest.mark.parametrize("variante", ["JD. PAULISTA", "JD PAULISTA ", "JARDIM PAULISTA", "jd paulista"])
def test_abreviacao_e_pontuacao(variante):
    assert limpo(variante) == "JARDIM PAULISTA"

@pytest.mark.parametrize(
    "variante", ["CERQ. CESAR", "CERQ CESAR", "CERQUEIRA CEZAR", "CERQUEIRA CÉSAR", "C CESAR"]
)
def test_sinonimos_curados(variante):
    assert limpo(variante) == "CERQUEIRA CESAR"

@pytest.mark.parametrize(
    "valor",
    [
        "TORRE A", "TORRE 1", "BLOCO B", "BL 2", "ED MASSIS FIVE STARS", "COND SETIN DOWNTOWN",
        "SUBCONDOMINIO HOTEL", "LADO A - SETOR RESID", "R VERGUEIRO 6360", "E VG", "E 1 DEP",
        "L C", "AGE", "NUMERO 63 E 65", "TORRE A-AL JURUPIS 700", "BROOKLIN BLOCO 3",
        "B 1 ED GREEN PARK", "T1 ED VERSAILLES", "MELIA CONFORT IGUATEMI", "", "   ",
    ],
)
def test_nao_bairro_descartado(valor):
    assert pd.isna(limpo(valor))

@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("CJ HAB JOSE BONIFACIO", "CONJUNTO HABITACIONAL JOSE BONIFACIO"),
        ("CJ HAB J BONIFACIO", "CONJUNTO HABITACIONAL JOSE BONIFACIO"),
        ("SE", "SE"),
        ("LUZ", "LUZ"),
        ("CASA VERDE", "CASA VERDE"),
        ("CH BRIG ED GOMES", "CHACARA BRIGADEIRO ED GOMES"),
        ("STA ETELVINA IIB-6", "SANTA ETELVINA IIB 6"),
        ("N SRA DO O", "NOSSA SENHORA DO O"),
        ("ITAIM PAULISTA", "ITAIM PAULISTA"),
        ("ITAIM", "ITAIM BIBI"),
    ],
)
def test_bairro_preservado(valor, esperado):
    assert limpo(valor) == esperado

def test_motivos():
    assert motivo_descarte("") == "vazio"
    assert motivo_descarte("TORRE A") == "complemento"
    assert motivo_descarte("1 DEP") == "endereco"
    assert motivo_descarte("AGE") == "fragmento"
    assert motivo_descarte("X Y", blocklist={"X Y"}) == "blocklist"
    assert motivo_descarte("TATUAPE") is None

def test_padronizar_preserva_indice_e_nan():
    s = pd.Series(["JD PAULISTA", np.nan, "TORRE B", "JD PAULISTA"], index=[10, 11, 12, 13])
    out = padronizar_bairro(s, sinonimos={}, blocklist=())
    assert list(out.index) == [10, 11, 12, 13]
    assert list(out.columns) == ["bairro_raw", "bairro_limpo", "motivo_descarte"]
    assert out.loc[10, "bairro_limpo"] == out.loc[13, "bairro_limpo"] == "JARDIM PAULISTA"
    assert out.loc[11, "motivo_descarte"] == "vazio"
    assert out.loc[12, "motivo_descarte"] == "complemento"

def test_propor_sinonimos_conservador():
    contagens = pd.Series(
        {
            "CERQUEIRA CESAR": 1000, "CERQUEIRA CEZAR": 400,
            "VILA MARIANA": 900, "VILA MARIA": 800,
            "JARDIM PAULISTA": 700, "JARDIM PAULISTANO": 600,
        }
    )
    pares = propor_sinonimos(contagens)
    assert pares[["variante", "canonico"]].values.tolist() == [["CERQUEIRA CEZAR", "CERQUEIRA CESAR"]]

def test_arquivos_de_referencia_normalizados():
    sinonimos = carregar_sinonimos()
    assert sinonimos, "data/reference/bairros_sinonimos.csv vazio ou ausente"
    assert all(v == normalizar(v) for v in sinonimos.values())
    # nenhum canonico pode ser ele proprio variante (evita cadeias nao resolvidas)
    assert not set(sinonimos.values()) & set(sinonimos)
    assert "MELIA CONFORT IGUATEMI" in carregar_blocklist()
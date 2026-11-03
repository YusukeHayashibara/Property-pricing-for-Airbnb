# Revisão do crosswalk DP → distrito e população por distrito

**Data:** 2026-11-03 · **Branch:** `feature/aggregation-open-items` · **Feito por:** Bruno
**Material para os slides de apresentação.** A seção 6 traz o roteiro sugerido.

---

## 1. Por que isso importa

O distrito é a unidade espacial do projeto (ver `obsidian-vault/09 - Spatial Aggregation.md`). Custo (IPTU) e receita (Airbnb) casam com o distrito de forma quase perfeita (99,94% e 100%). **Crime é o elo fraco**: a SSP-SP publica ocorrências por **Delegacia de Polícia (DP)**, e as áreas das DPs não coincidem com os distritos (94 DPs vs 96 distritos). Todo o score de risco depende de um **crosswalk DP → distrito**. Se ele estiver errado, o crime de um distrito é atribuído a outro.

O primeiro rascunho do crosswalk (set/2026) vinha da geocodificação automática (Nominatim) do **nome** do bairro de cada DP, mais 9 palpites manuais. Esta revisão verificou as 94 linhas.

## 2. Método

Para cada uma das 94 DPs da base de crime (`DP` = `NNN DP - Bairro`):

1. **Nó do DP no OpenStreetMap.** O OSM tem nós nomeados "NNº Distrito Policial". Quando existe, é a posição real da delegacia.
2. **Endereço oficial do DP.** O diretório de delegacias ([emsampa](https://www.emsampa.com.br/delpol/sp_565.htm)) traz rua e número de cada DP, casados pelo **número** da DP (o nome é ambíguo). Geocodificação estruturada (rua + número) no Nominatim.
3. **Ponto em polígono** contra os 96 polígonos de `distrito_municipal.geojson` (GeoSampa). Ponto fora de qualquer polígono: distrito mais próximo, aceito só até 150 m.
4. **Regra de decisão:**
   - os dois métodos apontam o mesmo distrito, diferente do atual → **corrige**;
   - algum método confirma o atual → **confirma**;
   - sem geocódigo utilizável (avenida longa, sem nó OSM) → mantém, justificando pelo **bairro** estar dentro do distrito;
   - dúvida real → **mantém e marca** `kept-ambiguous`.

Cada linha tem a evidência escrita em `data/reference/dp_distrito_crosswalk.csv` (colunas `bairro, distrito, review_status, evidence`). Esse é o arquivo versionado e a fonte de verdade; o notebook `aggregation.ipynb` o lê direto.

## 3. Resultado

| Status | Linhas |
|---|---|
| `reviewed-confirmed` (localização confirma o valor do rascunho) | 58 |
| `reviewed-corrected` (corrigida na 2ª passada) | 11 |
| `reviewed` (1ª passada, endereço do DP) | 10 |
| `reviewed-bairro` (sem geocódigo; bairro dentro do distrito) | 12 |
| `reviewed-street` (só a rua casou) | 2 |
| `kept-ambiguous` (mantida, precisa de conferência no mapa) | 1 |
| **Total** | **94** |

**22 das 94 linhas (23%) estavam erradas** no rascunho. Tabela completa das mudanças:

| DP (bairro) | Rascunho | Revisado | Base |
|---|---|---|---|
| Americanópolis | Cidade Ademar | **Cursino** | endereço / nó OSM do DP → polígono |
| Brás | Bras | **Mooca** | endereço / nó OSM do DP → polígono |
| Carandiru | Santana | **Vila Guilherme** | endereço / nó OSM do DP → polígono |
| Cidade A E Carvalho | Itaquera | **Artur Alvim** | endereço / nó OSM do DP → polígono |
| Cohab Itaquera | Artur Alvim | **Jose Bonifacio** | endereço / nó OSM do DP → polígono |
| Jaguaré | Jaguare | **Rio Pequeno** | endereço / nó OSM do DP → polígono |
| Jardim Mirna | Campo Grande | **Grajau** | endereço do DP → polígono |
| Jaçanã | Jacana | **Tremembe** | endereço / nó OSM do DP → polígono |
| Penha de França | Penha | **Tatuape** | endereço / nó OSM do DP → polígono |
| Pirituba | Pirituba | **Sao Domingos** | endereço / nó OSM do DP → polígono |
| Sacomã | Ipiranga | **Sacoma** | endereço do DP → polígono |
| Santo Amaro | Jardim Sao Luis | **Santo Amaro** | endereço do DP → polígono |
| Vale do Aricanduva | Aricanduva | **Cidade Lider** | endereço do DP → polígono |
| Vila Alpina | Sapopemba | **Vila Prudente** | bairro dentro do distrito |
| Vila Brasilândia | Freguesia Do O | **Brasilandia** | endereço do DP → polígono |
| Vila Diva | Aricanduva | **Agua Rasa** | endereço do DP → polígono |
| Vila Ema | Agua Rasa | **Sao Lucas** | endereço do DP → polígono |
| Vila Gustavo | Tucuruvi | **Vila Medeiros** | endereço / nó OSM do DP → polígono |
| Vila Pereira Barreto | Vila Guilherme | **Pirituba** | endereço do DP → polígono |
| Vila Rica | Jaragua | **Aricanduva** | endereço do DP → polígono |
| Vila Santa Maria | Tremembe | **Limao** | endereço do DP → polígono |
| Água Fria | Santana | **Tucuruvi** | endereço / nó OSM do DP → polígono |

### Impacto no dado de crime (ocorrências 2025, total por distrito)

| Métrica | Rascunho | Revisado |
|---|---|---|
| Distritos com DP direto | 71 | **76** |
| Distritos imputados pelo vizinho mais próximo | 25 | **20** |

Comparação dos dois rankings de crime por distrito:

- Correlação de Spearman: **0,86**.
- Distritos que mudam ≥10 posições: **22 de 96**. Mudam ≥20 posições: **13 de 96**.
- Maior mudança: Santo Amaro, **70 posições**.
- Top-10 em comum: **8 de 10**.

Leitura: um erro de 23% no mapeamento reordena o ranking de risco de forma material. Santo Amaro estava com o crime do Jardim São Luís, e Brás, Santana e Penha passam a ser lidos a partir dos vizinhos.

## 4. Limitações (importante dizer na apresentação)

- **Sede do DP ≠ área de atuação.** Usamos a localização da delegacia como proxy do distrito. O correto seria o polígono de circunscrição de cada DP, que a SSP-SP não publica de forma limpa. É o mesmo problema do tratamento A vs B da nota de agregação (Spearman ρ≈0,79 entre os dois).
- **Cinco distritos perderam o DP "próprio"** porque a sede fica no vizinho: Brás, Jaçanã, Jaguaré, Penha e Santana. Eles passam a herdar o valor do distrito mais próximo.
- **20 distritos seguem sem DP** e são imputados (lista no apêndice). A regra de imputação ainda é provisória (vizinho mais próximo).
- **Confiança por tipo de evidência:** `reviewed-confirmed` e `reviewed` são as mais fortes. `reviewed-bairro` (12 linhas) e `kept-ambiguous` (1 linha, Vila Clementino, na divisa Saúde/Vila Mariana) merecem conferência no mapa pelo time.
- Os geocódigos vêm do OpenStreetMap, que pode estar defasado ou impreciso para endereços individuais. As correções de `73 Jaçanã`, `93 Jaguaré` e `97 Americanópolis` têm o nó OSM do DP como única base.
- `aggregation.ipynb` foi reexecutado de ponta a ponta em 2026-11-03 (76 distritos diretos + 20 imputados, 188 colunas) e os CSVs de `data/processed/` foram regenerados com o crosswalk revisado. Os CSVs não são versionados: quem consome `distrito_features.csv` / `listings_aggregated.csv` precisa reexecutar o notebook.

## 5. População por distrito (Censo 2022)

- Arquivo: `data/external/populacao_distrito_2022.csv` (colunas `distrito`, `cd_ibge`, `populacao_2022`).
- Fonte: IBGE, Censo Demográfico 2022, SIDRA tabela 9923 (população residente), nível distrito, município 3550308. Script reprodutível: `scripts/fetch_population_distrito.py`.
- 96 distritos casam 1:1 com o geojson. Total: **11.451.999** habitantes. Menor: Marsilac (11.451). Maior: Grajaú (384.873).
- Uso: taxa de crime por 100 mil habitantes, `crime_total / populacao_2022 * 100000`. Ainda não aplicada nos CSVs processados.
- Cuidado ao interpretar: distritos centrais (República, Sé, Bela Vista) têm população residente pequena e população flutuante enorme, então a taxa por residente os infla. Vale discutir outra normalização para eles.

## 6. Roteiro sugerido para os slides

1. **Problema.** Crime é publicado por DP, o projeto trabalha por distrito. "94 ≠ 96, e as áreas não se encaixam."
2. **Rascunho automático.** Geocodificar o nome do bairro da DP. Dois exemplos errados: "Santo Amaro" caiu no Jardim São Luís; "Vila Rica" caiu em Jaraguá, do outro lado da cidade (o certo é Aricanduva).
3. **Método de verificação.** Diagrama: número da DP → endereço oficial + nó OSM → ponto em polígono → regra de decisão (seção 2).
4. **Resultado.** 22/94 (23%) erradas. Gráfico: barras por status (seção 3).
5. **Impacto.** Spearman 0,86; 22 distritos mudam ≥10 posições; Santo Amaro muda 70. Mapa antes/depois do crime por distrito (a gerar: o notebook já foi reexecutado).
6. **Limitações honestas.** Sede ≠ circunscrição; 20 distritos imputados; cinco distritos sem DP próprio.
7. **População e taxa por 100 mil.** Fonte IBGE 2022, 96/96, 11,45 milhões. Aviso sobre população flutuante no centro.
8. **Próximos passos.** Regra de imputação; cesta de crimes e janela de tempo; Google Places; deflator FipeZAP.

Números prontos para citar: **94** DPs · **96** distritos · **22 (23%)** linhas corrigidas · **71 → 76** distritos com DP direto · **25 → 20** imputados · **ρ = 0,86** · **11.451.999** habitantes.

## Apêndice — distritos sem DP (imputados pelo vizinho mais próximo)

ALTO DE PINHEIROS, ANHANGUERA, BARRA FUNDA, BELA VISTA, BRAS, CANGAIBA, IGUATEMI, JACANA, JAGUARA, JAGUARE, MANDAQUI, MARSILAC, MOEMA, MORUMBI, PEDREIRA, PENHA, REPUBLICA, SANTANA, SAUDE, VILA ANDRADE

# IPTU — Cadastro Predial (GeoSampa / São Paulo)

**Role:** Custo (atributos por imóvel)

> Adotado após a migração de escopo do projeto de Rio de Janeiro para São Paulo — ver entrada de 2026-08-20 em [[05 - Methodology]]. Substitui o candidato documentado em [[Alternative Property Value Sources - RJ]] (específico do Data.Rio / Prefeitura do Rio).

## What it provides

Cadastro fiscal do IPTU (Imposto Predial e Territorial Urbano) da cidade de São Paulo, fonte original GeoSampa/DECAD, cobertura 1995–2025 (~85M registros, ~21.5GB). Atributos por imóvel: valor de construção, valor de terreno, endereço/logradouro, bairro, ano.

## Access

Consulta via **Base dos Dados** (`basedosdados.br_sp_saopaulo_geosampa_iptu.iptu`), que hospeda o cadastro do GeoSampa limpo/tipado no BigQuery. A tabela completa excede o limite de 1GB de download direto do site — o acesso é via SQL/Python/R, não arquivo.

- Página do dataset: https://basedosdados.org/dataset/05f1b96d-883b-4202-a4bd-40379c5d326a?table=bdffc0f4-00da-4437-9ed9-0db7df11d3fa
- Pacote Python: `basedosdados` (`bd.read_sql(query, billing_project_id=...)`)
- Documentação: https://basedosdados.org/docs

**Custo:** gratuito. `billing_project_id` é um identificador de projeto Google Cloud, não implica cobrança — projeto criado em modo **BigQuery Sandbox** (sem cartão de crédito, sem conta de faturamento) em `console.cloud.google.com`. Limites do Sandbox: 1TB de processamento de consulta/mês, 10GB de armazenamento ativo, sem prazo de expiração do projeto. Ver https://docs.cloud.google.com/bigquery/docs/sandbox.

## Known limitations

- Schema completo não confirmado — apenas um subconjunto de colunas foi visto em exemplos da Base dos Dados (`valor_construcao`, `logradouro`, `bairro`, `cep`, `ano`, `centroide`).
- Campo único de "valor venal" não confirmado — pode precisar ser derivado de `valor_construcao + valor_terreno`.
- Valor venal (base fiscal) tende a ficar defasado em relação ao valor de mercado real.
- Dependência de setup nova em relação às demais fontes do projeto: exige conta Google Cloud e projeto BigQuery Sandbox por pessoa.
- Volume grande mesmo filtrando por ano (~85M linhas / 30 anos, alguns milhões de linhas por ano).

## How we use it

Ainda não integrado ao pipeline. Primeiro passo: notebook de discovery (`notebooks/iptu_analysis.ipynb`), que valida estrutura, qualidade e escopo geográfico antes de qualquer uso no modelo. Complementa [[ITBI - Data.Rio]] (a ser revisado/substituído por equivalente de SP) com atributos por imóvel para o modelo hedônico. Ver [[05 - Methodology]].

## Open questions

- #open-question Existe um campo de valor venal único, ou ele precisa ser derivado de `valor_construcao + valor_terreno`?
- #open-question Valor venal é um proxy razoável de preço de mercado em São Paulo?
- #open-question Qual granularidade geográfica os dados oferecem além de `bairro` (distrito? subprefeitura? lote/SQL?)?
- #open-question ITBI e a fonte de criminalidade (ISP-RJ) também precisam de equivalentes de São Paulo.

## Links

- [[ITBI - Data.Rio]] — a ser substituído por equivalente de São Paulo
- [[Alternative Property Value Sources - RJ]] — levantamento anterior, específico do Rio
- [[05 - Methodology]] — entrada de decisão sobre a migração de escopo

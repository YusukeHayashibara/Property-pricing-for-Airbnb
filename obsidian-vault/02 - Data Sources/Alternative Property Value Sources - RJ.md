# Fontes alternativas de valores de imóveis do RJ (sem scraping)

**Role:** Custo (levantamento de candidatos, específico do Rio de Janeiro — mantido como histórico após a migração de escopo para São Paulo, ver [[05 - Methodology]])

## O que é

Levantamento de bases que complementam ITBI/Data.Rio e FipeZAP com atributos por imóvel, sem os riscos de ToS do scraping de portal comercial (ver [[ZapImoveis - Scraping Assessment]]).

## 1. Cadastro Imobiliário / IPTU — DATA.RIO

- **Fonte:** [DADOS DO CADASTRO IMOBILIÁRIO - IPTU](https://www.data.rio/datasets/27b01e601c64479997be8e4223c40c3b_6/about), dataset aberto da Prefeitura do Rio, atualizado mensalmente.
- **Atributos:** área construída, tipo de uso, logradouro — por imóvel.
- **Vantagem sobre scraping:** dado público, sem risco de ToS, sem dependência de browser headless.
- **A validar:** cobertura temporal, granularidade dos campos, e se o valor venal é proxy razoável de preço de mercado (tende a ser defasado em relação ao valor de venda real).

## 2. ITBI por trecho de logradouro — Secretaria de Fazenda RJ

- **Fonte:** [Valores médios por m² de transações imobiliárias por trecho de logradouro](https://fazenda.prefeitura.rio/itbi-valores-medios-por-m2-de-transacoes-imobiliarias-por-trecho-de-logradouro/), mesma fonte ITBI já usada no projeto, em granularidade de trecho de rua.
- **Vantagem:** aumenta a resolução espacial do dado de custo já adotado, sem trocar de fonte.

## 3. SECOVI-Rio / CEPAI — Panorama do Mercado Imobiliário

- **Fonte:** [Pesquisa e Indicadores do CEPAI](https://www.secovirio.com.br/pesquisa-indicadores/), valores de m² de venda, locação e condomínio para mais de 50 bairros do Rio, publicado anualmente desde 2010.
- **Papel:** semelhante ao FipeZAP (índice agregado, não por imóvel), específico do Rio, granularidade por bairro.
- **Limitação:** acesso completo ao "Online Research" pode exigir contato direto (cepai@secovirio.com.br) e ser restrito a associados.

## 4. Datasets de terceiros já raspados do ZapImóveis

- **Fonte:** projetos que já coletaram dados de imóveis do Rio a partir do Zap — [BrunoRaphaell/previsao_precos_imoveis_zap](https://github.com/BrunoRaphaell/previsao_precos_imoveis_zap), [mvww11/zap-imoveis](https://github.com/mvww11/zap-imoveis).
- **Vantagem:** elimina o trabalho de construir e manter um scraper.
- **Limitação:** licença de reuso/redistribuição não confirmada por repositório; dados possivelmente desatualizados.

## Recomendação

Opção 1 (Cadastro IPTU/Data.Rio) resolve a lacuna de atributos por imóvel com menor risco — dado público, sem scraping, sem nova dependência de infraestrutura. Opções 2 e 3 aumentam a granularidade das fontes já adotadas. Opção 4 é um atalho para dados no estilo ZapImóveis, sujeito ao mesmo cuidado de licenciamento de [[ZapImoveis - Scraping Assessment]].

## Links

- [[ZapImoveis - Scraping Assessment]]
- [[IPTU - Cadastro Predial (GeoSampa - SP)]] — equivalente adotado para São Paulo
- [[05 - Methodology]]

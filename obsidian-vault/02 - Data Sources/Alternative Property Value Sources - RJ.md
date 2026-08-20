# Fontes alternativas de valores de imóveis do RJ (sem scraping)

> Levantamento de bases que poderiam complementar ITBI/Data.Rio e FipeZAP com atributos por imóvel — a mesma lacuna que motivou a avaliação de scraping do [[ZapImoveis - Scraping Assessment|ZapImóveis]] — mas via dado público/aberto, sem os riscos de ToS de raspar um portal comercial.

## 1. Cadastro Imobiliário / IPTU — DATA.RIO (candidato principal)

- **O quê:** [DADOS DO CADASTRO IMOBILIÁRIO - IPTU](https://www.data.rio/datasets/27b01e601c64479997be8e4223c40c3b_6/about) — dataset oficial e aberto da Prefeitura do Rio, atualizado mensalmente.
- **Por que interessa:** traz atributos **por imóvel** (área construída, tipo de uso, logradouro) — exatamente o que falta em ITBI e FipeZAP hoje.
- **Vantagem sobre o ZapImóveis:** dado público, sem scraping, sem risco de ToS de portal comercial, sem dependência de browser headless.
- **A validar:** cobertura temporal, granularidade exata dos campos, e se o valor venal do IPTU serve como proxy razoável de preço de mercado (costuma ser defasado em relação ao valor de venda real — precisa checagem antes de usar como variável de custo).

## 2. ITBI por trecho de logradouro — Secretaria de Fazenda RJ

- **O quê:** [Valores médios por m² de transações imobiliárias por trecho de logradouro](https://fazenda.prefeitura.rio/itbi-valores-medios-por-m2-de-transacoes-imobiliarias-por-trecho-de-logradouro/) — mesma fonte (ITBI) já usada no projeto, mas em granularidade de trecho de rua em vez de bairro/microrregião.
- **Por que interessa:** pode aumentar a resolução espacial do dado de custo já adotado sem trocar de fonte.

## 3. SECOVI-Rio / CEPAI — Panorama do Mercado Imobiliário

- **O quê:** [Pesquisa e Indicadores do CEPAI](https://www.secovirio.com.br/pesquisa-indicadores/) — valores de m² de venda, locação e condomínio para mais de 50 bairros do Rio, publicado anualmente desde 2010.
- **Por que interessa:** papel semelhante ao FipeZAP (índice agregado, não por imóvel), mas específico do Rio e com granularidade por bairro.
- **Ressalva:** não está claro se há bulk-download aberto; acesso completo ao "Online Research" do CEPAI pode exigir contato direto (cepai@secovirio.com.br) e possivelmente ser pago/restrito a associados.

## 4. Datasets de terceiros já raspados do ZapImóveis

- **O quê:** projetos que já coletaram e publicaram dados de imóveis do Rio a partir do Zap — ex.: [BrunoRaphaell/previsao_precos_imoveis_zap](https://github.com/BrunoRaphaell/previsao_precos_imoveis_zap) e [mvww11/zap-imoveis](https://github.com/mvww11/zap-imoveis).
- **Por que interessa:** elimina o trabalho de construir e manter um scraper.
- **Ressalva:** não elimina a questão de licença — é preciso checar se cada repositório permite reuso/redistribuição dos dados, e os dados podem estar desatualizados (sem data de coleta clara em alguns casos).

## Recomendação

Investigar primeiro a **opção 1 (Cadastro IPTU/Data.Rio)**: é a que resolve a lacuna real do projeto (atributos por imóvel) com o menor risco — dado público, sem scraping, sem nova dependência de infraestrutura. As opções 2 e 3 são enriquecimentos de granularidade das fontes já adotadas. A opção 4 é um atalho possível caso o time ainda queira dados no estilo ZapImóveis, mas com o mesmo cuidado de licenciamento discutido em [[ZapImoveis - Scraping Assessment]].

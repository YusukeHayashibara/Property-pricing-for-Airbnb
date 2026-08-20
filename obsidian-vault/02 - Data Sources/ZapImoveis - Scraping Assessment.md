# ZapImóveis — Avaliação de Web Scraping

**Role:** Custo (candidatos reais à venda, etapa final de scoring — não fonte de treino do modelo)

## O que é

Avaliação de viabilidade de coletar anúncios do ZapImóveis (ou alternativa: VivaReal, QuintoAndar) para complementar as 5 fontes já adotadas (ITBI/Data.Rio, FipeZAP, Inside Airbnb, Google Places/TripAdvisor, ISP-RJ). Uso previsto: etapa 4 da metodologia ("Final candidate scoring"), não coleta de treino. Ver [[05 - Methodology]].

## Repositórios de referência

| | [alexcamargos/ZapImoveisScraper](https://github.com/alexcamargos/ZapImoveisScraper) | [ziggy-data/Brazilian-Real-Estate-Intelligence](https://github.com/ziggy-data/Brazilian-Real-Estate-Intelligence) |
|---|---|---|
| Stack | Python + BeautifulSoup, saída CSV | BeautifulSoup + pandas/regex, Seaborn, Power BI, scikit-learn, Spark |
| Escopo | Scraper isolado | Pipeline completo: scraping → ETL → EDA → dashboard → modelo preditivo |
| Cobertura RJ | Não específica | Notebook dedicado a imóveis residenciais do Rio de Janeiro |
| Atividade | 12 commits, 0 stars | 51 commits, 38 stars; dados coletados em fev/2022 |
| Licença | MIT | Não especificada |

Nenhum dos dois é reutilizável diretamente: seletores de scraping ficam obsoletos com mudanças no HTML do site, e os dados do segundo repositório têm mais de 4 anos. Servem como referência de estrutura e de campos a extrair.

## Características técnicas

- Site dinâmico (React/Next.js) — scraping com `requests` + BeautifulSoup não captura conteúdo renderizado via JavaScript. Requer endpoint JSON interno (via inspeção de rede) ou browser headless (Playwright/Selenium).
- Proteção anti-bot conhecida (rate limiting, captcha). Exige throttling e tratamento de erros.
- Dependência de infraestrutura não presente no stack atual do projeto (`environment.yml`/`requirements.txt` não têm Playwright/Selenium).

## Características legais/ToS

- Termos de Uso do Grupo ZAP restringem coleta automatizada e redistribuição comercial de dados extraídos.
- É a única fonte do projeto via scraping não-oficial de portal comercial — as demais são dados públicos governamentais (ITBI, ISP-RJ), dado aberto com licença de pesquisa (Inside Airbnb) ou API oficial (Google Places/TripAdvisor).
- Uso acadêmico, não-comercial, sem redistribuição do dataset bruto e com volume pequeno reduz o risco prático, mas não o elimina.

## Recomendação

Necessário apenas para a etapa final de scoring de candidatos reais à venda (nenhuma das fontes de custo do projeto — ITBI, IPTU/Cadastro, FipeZAP, SECOVI, ver [[Alternative Property Value Sources - RJ]] — contém anúncios ativos).

1. Escopo pequeno e pontual: coleta não-recorrente, limitada às regiões/perfis mais bem pontuados pelo modelo (etapas 1–3 da metodologia). Dezenas de anúncios, não milhares.
2. Antes de implementar: revisar `robots.txt` e Termos de Uso (ZapImóveis e alternativas), registrar a decisão de seguir com justificativa de uso acadêmico não-comercial, verificar se existe endpoint JSON interno antes de adicionar Playwright/Selenium.
3. Não redistribuir os anúncios brutos coletados como dataset — usar apenas para gerar o score final. Não versionar HTML/dados brutos no git.
4. Implementação: módulo dedicado `src/collection/listings_snapshot.py`, separado dos módulos das 5 fontes já validadas, sinalizando o perfil de risco/ToS diferente.

## Links

- [[Alternative Property Value Sources - RJ]] — fontes alternativas sem risco de scraping
- [[05 - Methodology]] — seção "4. Final candidate scoring"

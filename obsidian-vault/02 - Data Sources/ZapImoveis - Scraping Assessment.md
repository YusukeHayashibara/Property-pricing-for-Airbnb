# ZapImóveis — Avaliação de Web Scraping

> Documento de avaliação, não uma fonte de dados ativa do projeto. Registra a análise de viabilidade de raspar anúncios do ZapImóveis como possível 6ª fonte, complementar às 5 já adotadas (ITBI/Data.Rio, FipeZAP, Inside Airbnb, Google Places/TripAdvisor, ISP-RJ).

## Contexto

O projeto modela a cadeia causal `custo → receita Airbnb → apelo turístico → risco de criminalidade → score de investimento`. Hoje a etapa de **custo** usa:

- **ITBI/Data.Rio** — preços reais de transação, geolocalizados, mas sem atributos do imóvel.
- **FipeZAP** — índice de preços agregado, também sem atributos por imóvel.

O README do projeto já documenta essa lacuna explicitamente:

> "ITBI and FipeZAP give price and location but not property attributes (bedrooms, area, etc.)."

Um scraper de anúncios do ZapImóveis preencheria exatamente esse buraco: preço pedido **por imóvel individual**, com quarto, área, vagas, condomínio e bairro — permitindo um modelo hedônico por imóvel em vez de apenas por microrregião. O repositório está em estágio de scaffolding (sem `src/`, `data/` ou `notebooks/` ainda, só documentação), então esta é uma decisão de arquitetura de coleta de dados, não uma refatoração.

O README já traz uma nota de cautela própria: *"Check the terms of use of any listing portal before automated collection."* — o time já havia sinalizado essa preocupação antes mesmo de cogitar o ZapImóveis nominalmente. A nota sobre o FipeZAP neste mesmo vault também levanta dúvida em aberto sobre licenciamento/termos de uso para redistribuição no relatório final — o mesmo tipo de risco se aplicaria aqui, de forma ainda mais direta.

## Repositórios de referência analisados

| | [alexcamargos/ZapImoveisScraper](https://github.com/alexcamargos/ZapImoveisScraper) | [ziggy-data/Brazilian-Real-Estate-Intelligence](https://github.com/ziggy-data/Brazilian-Real-Estate-Intelligence) |
|---|---|---|
| Stack | Python + BeautifulSoup, saída CSV | BeautifulSoup + pandas/regex, Seaborn, Power BI, scikit-learn, Spark |
| Escopo | Scraper simples e isolado (`scraper.py`) | Pipeline mais completo: scraping → ETL → EDA → dashboard → modelo preditivo |
| Cobertura RJ | Não específico | Notebook dedicado a imóveis residenciais do Rio de Janeiro |
| Atividade | Baixa (12 commits, 0 stars) | Moderada (51 commits, 38 stars), dados coletados em **fev/2022** — desatualizados |
| Licença | MIT | Não especificada claramente |

**Nota:** ao inspecionar os dois repositórios, o pipeline ETL + Power BI + modelagem está no `ziggy-data/Brazilian-Real-Estate-Intelligence`, e o `alexcamargos/ZapImoveisScraper` é o mais simples dos dois (só o scraper). Vale conferir os repositórios diretamente antes de adotar qualquer um como referência de arquitetura — conteúdo de README pode ter mudado desde esta análise.

Nenhum dos dois é reutilizável "as-is": seletores de scraping ficam obsoletos rapidamente (sites de listagem mudam HTML com frequência) e os dados do segundo repositório têm mais de 4 anos. Servem como **referência de estrutura e de quais campos extrair**, não como dependência a importar diretamente.

## Avaliação de viabilidade

### Técnica — viável, com ressalvas

- ZapImóveis é um site dinâmico (React/Next.js). Scraping simples com `requests` + BeautifulSoup tende a não capturar o conteúdo renderizado via JavaScript; normalmente é preciso (a) inspecionar se existe um endpoint JSON interno consumido pelo front (comum em portais de listagem) ou (b) usar um browser headless (Playwright/Selenium).
- Isso é mais pesado que o stack atual do projeto (`requests`, sem Selenium/Playwright em `environment.yml`) — adotar Zap implica uma nova dependência de infraestrutura de coleta.
- O site tem proteção anti-bot conhecida (rate limiting, captcha em alguns fluxos). Um scraper robusto exige throttling, tratamento de erros e possivelmente rotação de user-agent — manutenção não trivial para um projeto de curso com prazo de 4 meses.

### Legal/ToS — ponto crítico, exige decisão explícita do time

- Os Termos de Uso do Grupo ZAP tipicamente restringem coleta automatizada e redistribuição de dados extraídos para fins comerciais. O README do projeto já pede para checar isso, e a nota do FipeZAP levanta a mesma dúvida de licenciamento.
- Diferença em relação às outras 4 fontes: ITBI/Data.Rio e ISP-RJ são dados públicos governamentais; Inside Airbnb é dado aberto com licença explícita para pesquisa; Google Places/TripAdvisor são via API oficial com termos claros. ZapImóveis seria a **única fonte via scraping não-oficial de portal comercial** — categoria de risco diferente das demais, inclusive para uma eventual entrega/publicação acadêmica do projeto.
- Para uso acadêmico, não-comercial, sem redistribuição do dataset bruto e com volume pequeno, o risco prático tende a ser baixo — mas segue sendo um risco, não uma garantia, e merece registro explícito da decisão.

### Alinhamento com o desenho atual do projeto

- Não é essencial para a pergunta de pesquisa como formulada hoje: o projeto já assume trabalhar em nível de "região + perfil de imóvel" justamente para contornar a ausência de atributos por imóvel (README, seção "Data sources"). Adicionar ZapImóveis mudaria a granularidade do modelo — é uma mudança de escopo metodológico, não apenas "mais um dado".
- Dado o timeline apertado do curso e que as 5 fontes já cobrem a cadeia causal completa, ZapImóveis é um **enriquecimento opcional** (melhora a granularidade de "custo"), não um bloqueador.

## Recomendação

1. **Não é prioridade no momento.** As 5 fontes já documentadas cobrem a cadeia causal completa do projeto.
2. **Se o time decidir seguir**, tratar como uma 6ª fonte com processo próprio:
   - Definir objetivo claro (atributos por imóvel para complementar ITBI/FipeZAP), escopo de coleta restrito (só bairros/período relevantes ao estudo, volume pequeno) e política de não redistribuir o dataset bruto raspado.
   - Revisar `robots.txt` e os Termos de Uso do Grupo ZAP antes de escrever qualquer código, e registrar a decisão (seguir com justificativa de uso acadêmico não-comercial, ou descartar).
   - Prototipar primeiro se existe endpoint JSON interno (inspecionar aba Network do navegador) antes de ir para Playwright/Selenium — evita adicionar dependência pesada ao `environment.yml` sem necessidade.
   - Se implementado, seguir a convenção de módulo por fonte do projeto: `src/collection/zapimoveis.py`, com scraping desacoplado da limpeza (`src/cleaning/`).
   - Manter coleta pequena e throttled, nunca versionar HTML/dados brutos raspados no git (`data/` já está fora do versionamento).
3. Caso o time decida não usar ZapImóveis, este documento serve como registro da decisão e do porquê — evita reabrir a mesma pergunta mais adiante sem contexto.

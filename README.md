# Dashboard — Análise de Seleção de Fornecedor

Dashboard interativo construído com **Streamlit + Plotly**, Dockerizado para rodar na VPS.

## Estrutura do Projeto

```
ux/
├── app.py                      # Página inicial / visão geral
├── pages/
│   ├── 1_Metricas_Globais.py   # WAPE, FA, MAE, RMSE, MAPE
│   ├── 2_Analise_Segmentada.py # Heatmaps por Tiers ABC / Categoria
│   ├── 3_Vies_Bias.py          # Distribuição de erros e scatter real × previsto
│   ├── 4_Analise_Temporal.py   # Série semanal com toggle por fornecedor
│   ├── 5_Casos_Extremos.py     # SKUs com pior desempenho (tabela filtrável)
│   ├── 6_Placar_Final.py       # Ranking ponderado com pesos ajustáveis
│   └── 7_Analises_Avancadas.py # WAPE por SKU, decis de volume, uplift, coverage
├── src/
│   ├── data_loader.py          # Carga, limpeza e remoção de outliers (IQR)
│   ├── metrics.py              # WAPE, FA, Bias, MAPE, scorecard
│   ├── charts.py               # Gráficos Plotly reutilizáveis
│   └── sidebar.py              # Sidebar global com filtros
├── data/
│   ├── CASE_01.csv             # Cadastro de SKUs
│   └── CASE_01_DATA.csv        # Dados de previsão e volume real
├── notebooks/
│   └── Analise_Fornecedores.ipynb  # EDA + análise comparativa em PT-BR (referência analítica do dashboard)
├── .streamlit/
│   └── config.toml             # Tema (paleta do relatório original)
├── old/                        # Notebook e arquivos originais (referência, não alterados)
├── .dockerignore
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Executar Localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Acesse `http://localhost:8501`.

## Deploy na VPS com Docker

### Build e execução manual

```bash
docker compose up --build -d
```

O dashboard estará disponível na porta **8501**.

### Atualizar os dados sem rebuild

O volume `./data:/app/data:ro` está montado como somente-leitura dentro do container.
Para atualizar os CSVs, basta substituir os arquivos em `data/` e reiniciar:

```bash
docker compose restart
```

## Filtros da Sidebar

| Filtro | Descrição |
|---|---|
| Categoria | Filtra por categoria de produto |
| Tiers ABC | Filtra por classe de curva ABC (A, B, C, D) |
| Semanas | Slider de intervalo temporal |

Todos os gráficos e tabelas de todas as páginas respondem aos filtros da sidebar.

## Metodologia de Pontuação

| Critério | Peso Default |
|---|---|
| FA Global | 30% |
| FA Classe A | 25% |
| FA com Campanha | 20% |
| FA Top-20 SKUs | 15% |
| Consistência Semanal (Std FA) | 10% |

Os pesos são ajustáveis na página **Placar Final**.

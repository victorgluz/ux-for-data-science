import pandas as pd
import streamlit as st

from src.charts import bar_metricas_simples
from src.data_loader import CORES, FORNECEDORES, LABELS
from src.metrics import compute_global_metrics
from src.sidebar import render_sidebar

st.set_page_config(page_title="Métricas Globais", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Métricas de Acurácia Global")
st.caption("Comparativo completo de todos os fornecedores no conjunto de dados filtrado.")

met = compute_global_metrics(df)

st.markdown("### Tabela Comparativa")

display_df = met.copy()
display_df["WAPE"] = display_df["WAPE"].map("{:.2%}".format)
display_df["FA"] = display_df["FA"].map("{:.2%}".format)
display_df["Bias"] = met["Bias"].map("{:+.2%}".format)
display_df["MAE"] = met["MAE"].map("{:.2f}".format)
display_df["RMSE"] = met["RMSE"].map("{:.2f}".format)
display_df["MAPE"] = met["MAPE"].map("{:.2%}".format)
display_df.columns = ["WAPE", "FA", "Bias", "MAE", "RMSE", "MAPE"]

st.dataframe(display_df, use_container_width=True)

st.divider()
st.markdown("### Gráficos por Métrica")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        bar_metricas_simples(met, "FA", "Forecast Accuracy (FA) — quanto maior, melhor", pct=True),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        bar_metricas_simples(met, "WAPE", "WAPE — quanto menor, melhor", pct=True),
        use_container_width=True,
    )

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(
        bar_metricas_simples(met, "MAE", "MAE — quanto menor, melhor", pct=False),
        use_container_width=True,
    )
with col4:
    st.plotly_chart(
        bar_metricas_simples(met, "RMSE", "RMSE — quanto menor, melhor", pct=False),
        use_container_width=True,
    )

st.plotly_chart(
    bar_metricas_simples(met, "Bias", "Bias Global (+ = over-forecast, − = under-forecast)", pct=True),
    use_container_width=True,
)

st.divider()
st.markdown("### Definições das Métricas")
st.markdown(
    """
| Métrica | Fórmula | Interpretação |
|---|---|---|
| **WAPE** | Σ|Real−Prev| / ΣReal | Erro absoluto ponderado pelo volume total |
| **FA** | max(0, 1 − WAPE) | Forecast Accuracy; FA=100% é previsão perfeita |
| **Bias** | Σ(Prev−Real) / ΣReal | Tendência de sobre/sub-previsão; 0 é ideal |
| **MAE** | Média de |Real−Prev| | Erro médio absoluto em unidades de volume |
| **RMSE** | √(Média de (Real−Prev)²) | Penaliza erros grandes; sensível a outliers |
| **MAPE** | Média de |Real−Prev|/Real | % de erro médio absoluto; indefinido quando Real=0 |
"""
)

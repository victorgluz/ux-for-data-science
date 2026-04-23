import streamlit as st

from src.charts import dist_erros, scatter_erros
from src.data_loader import FORNECEDORES, LABELS
from src.metrics import bias, compute_global_metrics
from src.sidebar import render_sidebar

st.set_page_config(page_title="Viés e Bias", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Análise de Viés (Bias)")
st.caption(
    "Bias mede a direção sistêmica do erro: se o modelo prevê consistentemente mais (over-forecast) "
    "ou menos (under-forecast) que o real."
)

met = compute_global_metrics(df)

st.markdown("### Resumo de Bias Global")
cols = st.columns(3)
for i, (forn_label, row) in enumerate(met.iterrows()):
    bias_val = row["Bias"]
    direction = "Over-forecast" if bias_val > 0 else "Under-forecast"
    color = "#FF9800" if abs(bias_val) > 0.15 else "#4CAF50"
    with cols[i]:
        st.metric(
            label=forn_label,
            value=f"{bias_val:+.2%}",
            delta=direction,
            delta_color="inverse" if bias_val > 0 else "normal",
        )

st.divider()

st.markdown("### Distribuição de Erros Relativos")
st.caption("Histograma de (Previsto − Real) / Real para cada fornecedor. Distribuição centrada em 0 = sem viés.")
st.plotly_chart(dist_erros(df), use_container_width=True)

st.divider()

st.markdown("### Real × Previsto — Scatter Plot")
forn_sel = st.selectbox(
    "Selecione o fornecedor",
    options=[LABELS[f] for f in FORNECEDORES],
)
st.caption(
    "A linha vermelha tracejada indica previsão perfeita (Previsto = Real). "
    "Pontos acima da linha = over-forecast, abaixo = under-forecast. "
    "Amostrado em até 5.000 registros para visualização."
)
st.plotly_chart(scatter_erros(df, forn_sel), use_container_width=True)

st.divider()
st.markdown("### Interpretação do Bias")
st.info(
    """
**Bias positivo (over-forecast):** o modelo prevê MAIS do que o real → risco de excesso de estoque.

**Bias negativo (under-forecast):** o modelo prevê MENOS do que o real → risco de ruptura de estoque.

**Ideal:** Bias próximo de 0%, indicando que erros se compensam ao longo do portfólio.
"""
)

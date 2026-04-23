import plotly.express as px
import streamlit as st

from src.charts import tabela_extremos
from src.sidebar import render_sidebar

st.set_page_config(page_title="Casos Extremos", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Casos Extremos — SKUs com Pior Desempenho")
st.caption(
    "SKUs com maior WAPE (pior acurácia) por fornecedor. "
    "Use os filtros para investigar categorias ou classes ABC específicas."
)

n_skus = st.slider("Número de SKUs a exibir", min_value=10, max_value=100, value=30, step=10)

with st.spinner("Calculando métricas por SKU…"):
    extremos = tabela_extremos(df, n=n_skus)

col_forn, col_abc, col_cat = st.columns(3)
with col_forn:
    forn_opts = ["Todos"] + sorted(extremos["Fornecedor"].unique().tolist())
    forn_filter = st.selectbox("Fornecedor", forn_opts)
with col_abc:
    abc_opts = ["Todos"] + sorted(extremos["CLASS_ABC"].dropna().unique().tolist())
    abc_filter = st.selectbox("Tiers ABC", abc_opts)
with col_cat:
    cat_opts = ["Todos"] + sorted(extremos["CATEGORIA"].dropna().unique().tolist())
    cat_filter = st.selectbox("Categoria", cat_opts)

filtrado = extremos.copy()
if forn_filter != "Todos":
    filtrado = filtrado[filtrado["Fornecedor"] == forn_filter]
if abc_filter != "Todos":
    filtrado = filtrado[filtrado["CLASS_ABC"] == abc_filter]
if cat_filter != "Todos":
    filtrado = filtrado[filtrado["CATEGORIA"] == cat_filter]

st.markdown(f"**{len(filtrado)} SKUs exibidos**")

display = filtrado.copy()
display["WAPE"] = display["WAPE"].map("{:.2%}".format)
display["FA"] = display["FA"].map("{:.2%}".format)
display["Bias"] = filtrado["Bias"].map("{:+.2%}".format)
display["Volume Real Total"] = filtrado["Volume Real Total"].map("{:,.0f}".format)

st.dataframe(display, use_container_width=True)

st.divider()
st.markdown("### Distribuição de WAPE nos Casos Extremos")

if not filtrado.empty:
    fig = px.histogram(
        filtrado,
        x="WAPE",
        color="Fornecedor",
        nbins=30,
        title="Distribuição de WAPE — Casos Extremos",
        labels={"WAPE": "WAPE"},
        opacity=0.7,
        barmode="overlay",
    )
    fig.update_layout(xaxis_tickformat=".0%", height=380)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado para exibir com os filtros selecionados.")

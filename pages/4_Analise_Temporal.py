import streamlit as st

from src.charts import campanha_volume, linha_temporal
from src.sidebar import render_sidebar

st.set_page_config(page_title="Análise Temporal", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Análise Temporal")
st.caption(
    "Evolução das métricas mês a mês para cada fornecedor. "
    "Use o filtro de período na sidebar para ampliar ou reduzir o intervalo."
)

tab_fa, tab_wape, tab_bias, tab_vol = st.tabs(["FA por Mês", "WAPE por Mês", "Bias por Mês", "Volume"])

with tab_fa:
    st.plotly_chart(linha_temporal(df, "FA"), use_container_width=True)
    st.info(
        "FA mensal reflete a acurácia agregada de todos os SKUs naquele mês. "
        "Quedas bruscas podem indicar campanhas ou eventos não previstos."
    )

with tab_wape:
    st.plotly_chart(linha_temporal(df, "WAPE"), use_container_width=True)

with tab_bias:
    st.plotly_chart(linha_temporal(df, "Bias"), use_container_width=True)
    st.info(
        "Bias positivo = over-forecast, negativo = under-forecast. "
        "Picos positivos em meses de campanha indicam que o fornecedor super-estimou as vendas."
    )

with tab_vol:
    st.plotly_chart(campanha_volume(df), use_container_width=True)
    st.caption("Volume total real por mês, destacando meses com campanha ativa.")

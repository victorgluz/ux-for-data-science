import streamlit as st

from src.charts import heatmap_by_group
from src.metrics import compute_metrics_by_group
from src.sidebar import render_sidebar

st.set_page_config(page_title="Análise Segmentada", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Análise Segmentada")
st.caption("FA, WAPE e Bias segmentados por Tiers ABC, Categoria e Campanha.")

tab_abc, tab_cat, tab_camp = st.tabs(["Tiers ABC", "Categoria", "Campanha"])

with tab_abc:
    st.markdown("#### Heatmap de FA por Tiers ABC")
    st.plotly_chart(
        heatmap_by_group(df, "CLASS_ABC", "FA", "FA por Tiers ABC (verde = melhor)"),
        use_container_width=True,
    )
    st.markdown("#### Heatmap de WAPE por Tiers ABC")
    st.plotly_chart(
        heatmap_by_group(df, "CLASS_ABC", "WAPE", "WAPE por Tiers ABC (verde = melhor)"),
        use_container_width=True,
    )
    st.markdown("#### Bias por Tiers ABC")
    st.plotly_chart(
        heatmap_by_group(df, "CLASS_ABC", "Bias", "Bias por Tiers ABC"),
        use_container_width=True,
    )

    met_abc = compute_metrics_by_group(df, "CLASS_ABC")
    pivot_fa = met_abc.pivot(index="CLASS_ABC", columns="Fornecedor", values="FA")
    pivot_wape = met_abc.pivot(index="CLASS_ABC", columns="Fornecedor", values="WAPE")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**FA por Tiers ABC**")
        st.dataframe(pivot_fa.style.format("{:.2%}").highlight_max(axis=1, color="#c8e6c9"),
                     use_container_width=True)
    with col2:
        st.markdown("**WAPE por Tiers ABC**")
        st.dataframe(pivot_wape.style.format("{:.2%}").highlight_min(axis=1, color="#c8e6c9"),
                     use_container_width=True)

with tab_cat:
    st.markdown("#### Heatmap de FA por Categoria")
    st.plotly_chart(
        heatmap_by_group(df, "CATEGORIA", "FA", "FA por Categoria"),
        use_container_width=True,
    )
    st.markdown("#### Heatmap de WAPE por Categoria")
    st.plotly_chart(
        heatmap_by_group(df, "CATEGORIA", "WAPE", "WAPE por Categoria"),
        use_container_width=True,
    )

with tab_camp:
    df_camp = df.copy()
    df_camp["Campanha"] = df_camp["CAMPANHA_FLAG"].map({0: "Sem Campanha", 1: "Com Campanha"})

    met_camp = compute_metrics_by_group(df_camp, "Campanha")

    pivot_fa_camp = met_camp.pivot(index="Campanha", columns="Fornecedor", values="FA")
    pivot_wape_camp = met_camp.pivot(index="Campanha", columns="Fornecedor", values="WAPE")
    pivot_bias_camp = met_camp.pivot(index="Campanha", columns="Fornecedor", values="Bias")

    st.markdown("#### FA — Campanha vs Sem Campanha")
    st.dataframe(
        pivot_fa_camp.style.format("{:.2%}").highlight_max(axis=1, color="#c8e6c9"),
        use_container_width=True,
    )
    st.markdown("#### WAPE — Campanha vs Sem Campanha")
    st.dataframe(
        pivot_wape_camp.style.format("{:.2%}").highlight_min(axis=1, color="#c8e6c9"),
        use_container_width=True,
    )
    st.markdown("#### Bias — Campanha vs Sem Campanha")
    st.dataframe(
        pivot_bias_camp.style.format("{:+.2%}"),
        use_container_width=True,
    )
    st.info(
        "Bias positivo = over-forecast (previu mais do que o real). "
        "Bias negativo = under-forecast (previu menos)."
    )

import streamlit as st

from src.charts import bar_ranking, radar_scorecard
from src.metrics import (
    PESOS_DEFAULT,
    compute_ranking,
    compute_scorecard,
    compute_temporal_metrics,
)
from src.sidebar import render_sidebar

st.set_page_config(page_title="Placar Final", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Placar Final e Recomendação")
st.caption(
    "Score ponderado calculado com base em múltiplos critérios. "
    "Ajuste os pesos abaixo para simular diferentes prioridades de negócio."
)

st.markdown("### Ajuste os Pesos dos Critérios")
st.caption("Os pesos são normalizados automaticamente para somar 100%.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    w_fa_global = st.slider("FA Global", 0, 100, 30, step=5)
with col2:
    w_fa_a = st.slider("FA Classe A", 0, 100, 25, step=5)
with col3:
    w_fa_camp = st.slider("FA Campanha", 0, 100, 20, step=5)
with col4:
    w_fa_top20 = st.slider("FA Top-20 SKUs", 0, 100, 15, step=5)
with col5:
    w_consist = st.slider("Consistência", 0, 100, 10, step=5)

total_w = w_fa_global + w_fa_a + w_fa_camp + w_fa_top20 + w_consist
if total_w == 0:
    st.error("A soma dos pesos é zero. Ajuste pelo menos um critério.")
    st.stop()

pesos = {
    "FA Global": w_fa_global / total_w,
    "FA Classe A": w_fa_a / total_w,
    "FA Campanha": w_fa_camp / total_w,
    "FA Top-20 SKUs": w_fa_top20 / total_w,
    "Consistência (Std FA)": w_consist / total_w,
}

pesos_display = {k: f"{v:.0%}" for k, v in pesos.items()}
st.caption(f"Pesos normalizados: {pesos_display}")

temp_df = compute_temporal_metrics(df)
scorecard = compute_scorecard(df, temp_df)
ranking = compute_ranking(scorecard, pesos)
vencedor = ranking.index[0]

st.divider()

st.success(f"Fornecedor Recomendado: {vencedor} — Score Final: {ranking.loc[vencedor, 'Score Final']:.3f}")

col_rank, col_radar = st.columns([1, 1])
with col_rank:
    st.markdown("#### Ranking")
    st.plotly_chart(bar_ranking(ranking), use_container_width=True)
with col_radar:
    st.markdown("#### Radar de Desempenho (valores brutos)")
    st.plotly_chart(radar_scorecard(scorecard), use_container_width=True)

st.divider()
st.markdown("### Scorecard Detalhado")

sc_display = scorecard.copy()
for col in ["FA Global", "FA Classe A", "FA Campanha", "FA Top-20 SKUs"]:
    sc_display[col] = scorecard[col].map("{:.2%}".format)
sc_display["Bias"] = scorecard["Bias"].map("{:+.2%}".format)
sc_display["Bias Global Abs"] = scorecard["Bias Global Abs"].map("{:.2%}".format)
sc_display["Consistência (Std FA)"] = scorecard["Consistência (Std FA)"].map("{:.4f}".format)

st.dataframe(sc_display, use_container_width=True)
st.caption(
    "Bias signed (com sinal) é informativo: positivo indica superestimação (risco de estoque parado), "
    "negativo indica subestimação (risco de ruptura). O ranking usa Bias Abs porque não modelamos custo assimétrico."
)

st.divider()
st.markdown("### Relatório Textual de Recomendação")
for forn_label in ranking.index:
    score = ranking.loc[forn_label, "Score Final"]
    pos = ranking.loc[forn_label, "Posição"]
    is_winner = forn_label == vencedor
    fa = scorecard.loc[forn_label, "FA Global"]
    fa_a = scorecard.loc[forn_label, "FA Classe A"]
    fa_camp = scorecard.loc[forn_label, "FA Campanha"]
    bias_abs = scorecard.loc[forn_label, "Bias Global Abs"]

    with st.expander(f"[{pos}] {forn_label} — Score: {score:.3f}" + (" — RECOMENDADO" if is_winner else ""), expanded=is_winner):
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("FA Global", f"{fa:.2%}")
            st.metric("FA Classe A", f"{fa_a:.2%}")
        with col_b:
            st.metric("FA Campanha", f"{fa_camp:.2%}")
            st.metric("Bias Abs. Global", f"{bias_abs:.2%}")

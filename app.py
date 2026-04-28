import streamlit as st

from src.charts import bar_ranking, radar_scorecard
from src.data_loader import CORES, FORNECEDORES, LABELS
from src.metrics import (
    compute_global_metrics,
    compute_ranking,
    compute_scorecard,
    compute_temporal_metrics,
    forecast_accuracy,
    wape,
    bias,
)
from src.sidebar import render_sidebar

st.set_page_config(
    page_title="Análise de Fornecedores",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        color: #fff;
        padding: 2.5rem 2rem 2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .hero h1 { font-size: 2rem; font-weight: 800; margin-bottom: .3rem; }
    .hero p { opacity: .8; font-size: .95rem; margin: 0; }
    .kpi-card {
        background: #fff;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 6px rgba(0,0,0,.08);
        text-align: center;
    }
    .kpi-label { font-size: .78rem; color: #6b7280; text-transform: uppercase; letter-spacing: .05em; }
    .kpi-value { font-size: 1.7rem; font-weight: 700; margin: .1rem 0 0 0; }
    .winner-banner {
        background: linear-gradient(90deg,#e8f5e9,#c8e6c9);
        border-left: 5px solid #4CAF50;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

df = render_sidebar()

st.markdown(
    """
    <div class="hero">
        <h1>Análise de Seleção de Fornecedor</h1>
                <p>Previsão de Demanda — Comparativo de 3 fornecedores candidatos com dados de Fev/2017 a Jun/2018</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Premissas adotadas (clique para expandir)"):
    st.markdown(
        """
**Interpretação de `TEMPO`:** YYYYMM com extensão para 2018. Os valores `2017-13` a `2017-18` foram traduzidos para `2018-01` a `2018-06`, totalizando 17 meses (fev/2017 a jun/2018). O enunciado fala em "1 ano de previsão", mas a base contém 17 meses; optamos por manter todos eles, pois existe `VOLUME_REAL` para todos os períodos e descartar dados reduziria o poder estatístico da avaliação.

**Outliers:** mantidos. As previsões extremas do Fornecedor 03 (até 220 mil unidades, contra máximo real de 28 mil) fazem parte da qualidade real entregue pelo modelo e a análise as expõe em vez de mascará-las.

**Esparsidade:** combinações loja×material que não aparecem em todos os meses (lançamentos, descontinuação, ruptura) são tratadas como parte natural do problema e não são imputadas.

**Saneamento mínimo:** previsões negativas seriam clipadas em zero por sanidade física, e linhas com `VOLUME_REAL` negativo descartadas. Não há registros desse tipo nos dados atuais.

**Comparação justa:** todas as métricas são calculadas sobre o mesmo conjunto de linhas (mesmas chaves loja-material-período), garantindo comparação direta entre fornecedores.

A análise completa, com todas as decisões metodológicas e seções de limitações, está em `notebooks/Analise_Fornecedores.ipynb`.
"""
    )

met = compute_global_metrics(df)
temp_df = compute_temporal_metrics(df)
scorecard = compute_scorecard(df, temp_df)
ranking = compute_ranking(scorecard)
vencedor = ranking.index[0]

st.markdown(
    f"""
    <div class="winner-banner">
        <b>Fornecedor Recomendado:</b> {vencedor}
        &nbsp;|&nbsp; Score Final: <b>{ranking.loc[vencedor, "Score Final"]:.3f}</b>
        &nbsp;|&nbsp; FA Global: <b>{met.loc[vencedor, "FA"]:.2%}</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### KPIs Globais por Fornecedor")
cols = st.columns(3)
for i, (forn_label, row) in enumerate(met.iterrows()):
    color = CORES[list(LABELS.keys())[list(LABELS.values()).index(forn_label)]]
    with cols[i]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label" style="color:{color};font-weight:700">{forn_label}</div>
                <div class="kpi-value" style="color:{color}">{row["FA"]:.1%}</div>
                <div class="kpi-label">Forecast Accuracy</div>
                <hr style="margin:.5rem 0">
                <div style="display:flex;justify-content:space-between;font-size:.82rem;">
                    <span>WAPE: <b>{row["WAPE"]:.1%}</b></span>
                    <span>Bias: <b>{row["Bias"]:+.1%}</b></span>
                    <span>MAE: <b>{row["MAE"]:.1f}</b></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

col_radar, col_ranking = st.columns([1, 1])
with col_radar:
    st.plotly_chart(radar_scorecard(scorecard), use_container_width=True)
with col_ranking:
    st.plotly_chart(bar_ranking(ranking), use_container_width=True)

st.divider()
st.markdown("### Ranking Final Detalhado")
ranking_display = ranking.copy()
ranking_display["Score Final"] = ranking_display["Score Final"].map("{:.3f}".format)
st.dataframe(ranking_display, use_container_width=True)

st.divider()
st.markdown("### Metodologia de Pontuação")
st.markdown(
    """
| Critério | Peso | Justificativa |
|---|---|---|
| FA Global | 30% | Acurácia geral do portfólio |
| FA Classe A | 25% | Maior impacto financeiro |
| FA com Campanha | 20% | Capacidade de prever picos promocionais |
| FA Top-20 SKUs | 15% | SKUs de maior volume/criticidade |
| Consistência Mensal (Std FA) | 10% | Estabilidade do modelo ao longo do tempo |
"""
)

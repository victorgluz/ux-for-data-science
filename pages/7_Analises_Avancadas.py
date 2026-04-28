import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import CORES, FORNECEDORES, LABELS
from src.metrics import (
    compute_coverage_zeros,
    compute_fa_por_decil,
    compute_uplift_accuracy,
    compute_wape_per_sku,
)
from src.sidebar import render_sidebar

st.set_page_config(page_title="Análises Avançadas", page_icon=None, layout="wide")

df = render_sidebar()

st.title("Análises Avançadas")
st.caption(
    "Desdobramentos que não cabem nas métricas globais: distribuição de WAPE entre SKUs, "
    "estratificação por decil de volume, acurácia do uplift promocional e coverage de previsões."
)

forn_labels = [LABELS[f] for f in FORNECEDORES]
color_map = {LABELS[f]: CORES[f] for f in FORNECEDORES}

st.divider()
st.markdown("## 1. Distribuição de WAPE por SKU")
st.caption(
    "WAPE global pode esconder fornecedor ótimo na média e catastrófico em parte do portfólio. "
    "Aqui calculamos o WAPE individual de cada material."
)

wape_sku = compute_wape_per_sku(df)
if not wape_sku.empty:
    desc = wape_sku[forn_labels].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).round(3)
    st.dataframe(desc, use_container_width=True)

    long = wape_sku[forn_labels].clip(upper=3).melt(var_name="Fornecedor", value_name="WAPE")
    fig = px.box(
        long, x="Fornecedor", y="WAPE", color="Fornecedor",
        color_discrete_map=color_map,
        title="WAPE por SKU (clipado em 3 para visualização)",
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Mediana baixa com p95 alto significa subgrupo de SKUs onde o fornecedor falha sistematicamente."
    )
else:
    st.info("Sem dados suficientes após filtros.")

st.divider()
st.markdown("## 2. FA por Decil de Volume")
st.caption(
    "Em vez do corte binário Top-20 vs resto, agrupamos os SKUs em decis pelo volume real total. "
    "D1 = menores volumes, D10 = maiores."
)

try:
    dec = compute_fa_por_decil(df)
    pivot = dec.pivot(index="Decil", columns="Fornecedor", values="FA").round(3)
    st.dataframe(pivot, use_container_width=True)
    fig = px.bar(
        dec, x="Decil", y="FA", color="Fornecedor", barmode="group",
        color_discrete_map=color_map,
        title="FA por decil de volume",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Decis altos (D9, D10) concentram receita; FA baixo lá dói no negócio. "
        "Decis baixos têm FA naturalmente menor por causa da baixa previsibilidade da cauda."
    )
except Exception as e:
    st.warning(f"Não foi possível calcular decis (provavelmente filtros muito restritivos): {e}")

st.divider()
st.markdown("## 3. Acurácia do Uplift de Campanha")
st.caption(
    "FA em meses de campanha mistura nível e uplift. Aqui isolamos o multiplicador promocional: "
    "uplift_real = média(com campanha) / média(sem campanha) por loja+material, e comparamos com o uplift previsto."
)

uplift = compute_uplift_accuracy(df)
if uplift.empty:
    st.info("Sem combinações loja+material com campanha e sem-campanha simultaneamente nos filtros atuais.")
else:
    cols = st.columns(3)
    cols[0].metric("Combinações analisadas", f"{len(uplift):,}")
    cols[1].metric("Uplift real médio", f"{uplift['uplift_real'].mean():.2f}x")
    cols[2].metric("Uplift real mediana", f"{uplift['uplift_real'].median():.2f}x")

    rows = []
    for forn_label in forn_labels:
        err = (uplift[forn_label] - uplift["uplift_real"]) / uplift["uplift_real"]
        rows.append({
            "Fornecedor": forn_label,
            "Viés médio (uplift)": err.mean(),
            "MAE relativo": err.abs().mean(),
            "Mediana uplift previsto": uplift[forn_label].median(),
        })
    res = pd.DataFrame(rows).set_index("Fornecedor")
    res_display = res.copy()
    res_display["Viés médio (uplift)"] = res["Viés médio (uplift)"].map("{:+.2%}".format)
    res_display["MAE relativo"] = res["MAE relativo"].map("{:.2%}".format)
    res_display["Mediana uplift previsto"] = res["Mediana uplift previsto"].map("{:.2f}x".format)
    st.dataframe(res_display, use_container_width=True)
    st.caption(
        "Viés positivo = superestima o uplift (sugere comprar a mais para campanha). "
        "MAE relativo é o erro típico do multiplicador."
    )

st.divider()
st.markdown("## 4. Coverage e Zeros Sistemáticos")
st.caption(
    "Fornecedor que prevê zero por padrão difere de quem tentou e errou. "
    "Zeros previstos com real positivo indicam ruptura sistemática prevista (abdicação de modelagem)."
)

cov = compute_coverage_zeros(df)
cov_display = cov.copy()
cov_display["% sobre total"] = cov["% sobre total"].map("{:.2f}%".format)
st.dataframe(cov_display, use_container_width=True)
st.caption(
    "Muitos zeros previstos com real positivo indicam que o fornecedor abdica de prever em parte do portfólio, "
    "causando ruptura no operacional mesmo que o WAPE global pareça aceitável."
)

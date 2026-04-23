import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import CORES, FORNECEDORES, LABELS
from src.metrics import (
    bias,
    compute_metrics_by_group,
    compute_temporal_metrics,
    forecast_accuracy,
    mape_safe,
    mae,
    rmse,
    wape,
)

PALETTE = list(CORES.values())


def _forn_color(label: str) -> str:
    for k, v in LABELS.items():
        if v == label:
            return CORES[k]
    return "#888"


def bar_metricas_globais(met_df: pd.DataFrame) -> go.Figure:
    metrics = ["WAPE", "FA", "MAE", "RMSE", "MAPE"]
    figs = []
    for metric in metrics:
        fig = go.Figure()
        for forn_label in met_df.index:
            fig.add_trace(
                go.Bar(
                    name=forn_label,
                    x=[forn_label],
                    y=[met_df.loc[forn_label, metric]],
                    marker_color=_forn_color(forn_label),
                    showlegend=False,
                )
            )
        figs.append(fig)

    fig = go.Figure()
    fornecedores_labels = met_df.index.tolist()
    for metric in ["WAPE", "FA"]:
        for forn_label in fornecedores_labels:
            fig.add_trace(
                go.Bar(
                    name=f"{forn_label} — {metric}",
                    x=[forn_label],
                    y=[met_df.loc[forn_label, metric]],
                    marker_color=_forn_color(forn_label),
                    text=f"{met_df.loc[forn_label, metric]:.1%}",
                    textposition="outside",
                    showlegend=False,
                )
            )
    fig.update_layout(
        barmode="group",
        title="WAPE e FA Global por Fornecedor",
        yaxis_tickformat=".0%",
        height=400,
    )
    return fig


def bar_metricas_simples(met_df: pd.DataFrame, metric: str, title: str, pct: bool = True) -> go.Figure:
    fig = go.Figure()
    for forn_label in met_df.index:
        val = met_df.loc[forn_label, metric]
        fig.add_trace(
            go.Bar(
                name=forn_label,
                x=[forn_label],
                y=[val],
                marker_color=_forn_color(forn_label),
                text=f"{val:.2%}" if pct else f"{val:.2f}",
                textposition="outside",
                showlegend=False,
            )
        )
    fmt = ".0%" if pct else ".2f"
    fig.update_layout(
        title=title,
        yaxis_tickformat=fmt,
        height=380,
    )
    return fig


def heatmap_by_group(df: pd.DataFrame, grupo_col: str, metric: str, title: str) -> go.Figure:
    met = compute_metrics_by_group(df, grupo_col)
    pivot = met.pivot(index=grupo_col, columns="Fornecedor", values=metric)
    pivot = pivot[[LABELS[f] for f in FORNECEDORES if LABELS[f] in pivot.columns]]

    colorscale = "RdYlGn" if metric == "FA" else "RdYlGn_r"

    fig = px.imshow(
        pivot,
        text_auto=".1%",
        color_continuous_scale=colorscale,
        aspect="auto",
        title=title,
    )
    fig.update_layout(height=max(300, 60 * len(pivot) + 100))
    return fig


def scatter_erros(df: pd.DataFrame, forn_label: str) -> go.Figure:
    forn_key = None
    for k, v in LABELS.items():
        if v == forn_label:
            forn_key = k
            break
    if forn_key is None:
        return go.Figure()

    col = f"VOLUME_{forn_key}"
    sample = df.sample(min(5000, len(df)), random_state=42)
    fig = px.scatter(
        sample,
        x="VOLUME_REAL",
        y=col,
        color="CLASS_ABC",
        opacity=0.4,
        title=f"Real vs Previsto — {forn_label}",
        labels={"VOLUME_REAL": "Volume Real", col: "Volume Previsto"},
    )
    max_val = max(sample["VOLUME_REAL"].max(), sample[col].max()) * 1.05
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="red", dash="dash"))
    fig.update_layout(height=450)
    return fig


def dist_erros(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for forn in FORNECEDORES:
        col = f"VOLUME_{forn}"
        erros = (df[col] - df["VOLUME_REAL"]) / df["VOLUME_REAL"].replace(0, np.nan)
        erros = erros.dropna().clip(-3, 3)
        fig.add_trace(
            go.Histogram(
                x=erros,
                name=LABELS[forn],
                opacity=0.6,
                marker_color=CORES[forn],
                nbinsx=60,
            )
        )
    fig.update_layout(
        barmode="overlay",
        title="Distribuição de Erros Relativos (Previsto − Real) / Real",
        xaxis_title="Erro Relativo",
        yaxis_title="Contagem",
        height=420,
    )
    return fig


def linha_temporal(df: pd.DataFrame, metric: str = "FA") -> go.Figure:
    temp = compute_temporal_metrics(df)
    fig = go.Figure()
    for forn in FORNECEDORES:
        lbl = LABELS[forn]
        sub = temp[temp["Fornecedor"] == lbl].sort_values("TEMPO")
        fmt = ".1%" if metric in ("FA", "WAPE", "Bias") else ".2f"
        fig.add_trace(
            go.Scatter(
                x=sub["TEMPO"],
                y=sub[metric],
                mode="lines+markers",
                name=lbl,
                line=dict(color=CORES[forn], width=2),
                marker=dict(size=7),
                hovertemplate=f"%{{x}}<br>{metric}: %{{y:{fmt}}}<extra>{lbl}</extra>",
            )
        )
    yaxis_fmt = ".0%" if metric in ("FA", "WAPE", "Bias") else ".2f"
    fig.update_layout(
        title=f"{metric} por Mês",
        xaxis_title="Mês",
        yaxis_title=metric,
        yaxis_tickformat=yaxis_fmt,
        height=420,
        hovermode="x unified",
    )
    return fig


def tabela_extremos(df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    rows = []
    for forn in FORNECEDORES:
        col = f"VOLUME_{forn}"
        lbl = LABELS[forn]
        grp = (
            df.groupby("MATERIAL")
            .apply(
                lambda g: pd.Series(
                    {
                        "Fornecedor": lbl,
                        "CATEGORIA": g["CATEGORIA"].iloc[0],
                        "CLASS_ABC": g["CLASS_ABC"].iloc[0],
                        "WAPE": wape(g["VOLUME_REAL"], g[col]),
                        "FA": forecast_accuracy(g["VOLUME_REAL"], g[col]),
                        "Bias": bias(g["VOLUME_REAL"], g[col]),
                        "Volume Real Total": g["VOLUME_REAL"].sum(),
                    }
                )
            )
            .reset_index()
        )
        rows.append(grp)

    resultado = pd.concat(rows, ignore_index=True)
    piores = resultado.sort_values("WAPE", ascending=False).head(n)
    return piores


def bar_ranking(ranking: pd.DataFrame) -> go.Figure:
    fornecedores_ord = ranking.index.tolist()
    scores_ord = ranking["Score Final"].tolist()

    fig = go.Figure()
    for i, (forn_label, score) in enumerate(zip(fornecedores_ord, scores_ord)):
        fig.add_trace(
            go.Bar(
                x=[score],
                y=[forn_label],
                orientation="h",
                marker_color=_forn_color(forn_label),
                text=f"{score:.3f}",
                textposition="outside",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Ranking Final — Score Ponderado por Critérios de Negócio",
        xaxis=dict(range=[0, 1.15], tickformat=".2f"),
        xaxis_title="Score (0 a 1)",
        height=350,
        yaxis=dict(categoryorder="array", categoryarray=fornecedores_ord[::-1]),
    )
    fig.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.6)
    return fig


def radar_scorecard(scorecard: pd.DataFrame) -> go.Figure:
    categories = [c for c in scorecard.columns if c not in ("Bias Global Abs", "Consistência (Std FA)")]
    categories_display = categories + [categories[0]]

    fig = go.Figure()
    for forn_label in scorecard.index:
        vals = scorecard.loc[forn_label, categories].tolist()
        vals += [vals[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=categories_display,
                fill="toself",
                name=forn_label,
                line_color=_forn_color(forn_label),
                opacity=0.7,
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Scorecard — Radar de Desempenho",
        height=450,
    )
    return fig


def campanha_volume(df: pd.DataFrame) -> go.Figure:
    camp = df.groupby(["TEMPO", "CAMPANHA_FLAG"])["VOLUME_REAL"].sum().reset_index()
    camp["Tipo"] = camp["CAMPANHA_FLAG"].map({0: "Sem Campanha", 1: "Com Campanha"})
    fig = px.bar(
        camp,
        x="TEMPO",
        y="VOLUME_REAL",
        color="Tipo",
        barmode="stack",
        title="Volume Real por Mês — Campanhas vs Sem Campanha",
        labels={"VOLUME_REAL": "Volume", "TEMPO": "Mês"},
        color_discrete_map={"Com Campanha": "#FF9800", "Sem Campanha": "#2196F3"},
    )
    fig.update_layout(height=380)
    return fig

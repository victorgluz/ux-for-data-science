import streamlit as st

from src.data_loader import FORNECEDORES, LABELS, apply_filters, load_data


def render_sidebar():
    df, sku = load_data()

    with st.sidebar:
        st.markdown("## Filtros")

        todas_categorias = sorted(df["CATEGORIA"].dropna().unique().tolist())
        categorias_sel = st.multiselect(
            "Categoria",
            options=todas_categorias,
            default=[],
            placeholder="Todas",
        )

        todas_abc = sorted(df["CLASS_ABC"].dropna().unique().tolist())
        abc_sel = st.multiselect(
            "Tiers ABC",
            options=todas_abc,
            default=[],
            placeholder="Todas",
        )

        todos_meses = sorted(df["TEMPO"].unique().tolist())
        mes_range = st.select_slider(
            "Período (mês)",
            options=todos_meses,
            value=(todos_meses[0], todos_meses[-1]),
        )
        meses_sel = [m for m in todos_meses if mes_range[0] <= m <= mes_range[1]]

        st.divider()
        st.caption("Fornecedores ativos (todos sempre incluídos na comparação)")
        for forn in FORNECEDORES:
            st.markdown(
                f"<span style='color:{_forn_color(forn)}'>●</span> {LABELS[forn]}",
                unsafe_allow_html=True,
            )

    df_filtrado = apply_filters(
        df,
        categorias=categorias_sel if categorias_sel else None,
        abc_classes=abc_sel if abc_sel else None,
        meses=meses_sel if meses_sel else None,
    )

    return df_filtrado


def _forn_color(forn_key: str) -> str:
    from src.data_loader import CORES
    return CORES.get(forn_key, "#888")

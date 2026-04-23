import os
import numpy as np
import pandas as pd
import streamlit as st

FORNECEDORES = ["FORNECEDOR_01", "FORNECEDOR_02", "FORNECEDOR_03"]
CORES = {
    "FORNECEDOR_01": "#2196F3",
    "FORNECEDOR_02": "#FF9800",
    "FORNECEDOR_03": "#4CAF50",
}
LABELS = {
    "FORNECEDOR_01": "Forn. 01",
    "FORNECEDOR_02": "Forn. 02",
    "FORNECEDOR_03": "Forn. 03",
}
LABELS_INV = {v: k for k, v in LABELS.items()}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _normalizar_tempo(valor: str) -> str:
    valor = str(valor).strip()
    if len(valor) == 6 and "-" not in valor:
        return f"{valor[:4]}-{valor[4:]}"
    return valor


def _adicionar_limites_iqr(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("MATERIAL")["VOLUME_REAL"]
    q1 = grp.transform("quantile", 0.25)
    q3 = grp.transform("quantile", 0.75)
    iqr = q3 - q1
    fator = np.where(df["CAMPANHA_FLAG"] == 1, 2.5, 1.5)
    df = df.copy()
    df["_lower"] = q1 - fator * iqr
    df["_upper"] = q3 + fator * iqr
    return df


@st.cache_data(show_spinner="Carregando dados…")
def load_data():
    sku = pd.read_csv(os.path.join(DATA_DIR, "CASE_01.csv"))
    sku.columns = sku.columns.str.strip()

    df_raw = pd.read_csv(
        os.path.join(DATA_DIR, "CASE_01_DATA.csv"),
        decimal=",",
        thousands=None,
    )
    df_raw.columns = df_raw.columns.str.strip()

    vol_cols = [
        "VOLUME_REAL",
        "VOLUME_FORNECEDOR_01",
        "VOLUME_FORNECEDOR_02",
        "VOLUME_FORNECEDOR_03",
    ]
    for col in vol_cols:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    df = df_raw.merge(
        sku[["MATERIAL", "CATEGORIA", "SUBCATEG", "MARCA", "CLASS_ABC"]],
        on="MATERIAL",
        how="left",
    )

    df = df.dropna(subset=["VOLUME_REAL"])
    df = df[df["VOLUME_REAL"] >= 0].copy()

    for col in ["VOLUME_FORNECEDOR_01", "VOLUME_FORNECEDOR_02", "VOLUME_FORNECEDOR_03"]:
        df[col] = df[col].clip(lower=0)

    df["TEMPO"] = df["TEMPO"].astype(str).str.strip()
    df["TEMPO"] = df["TEMPO"].apply(_normalizar_tempo)
    df["CAMPANHA_FLAG"] = df["CAMPANHA_FLAG"].astype(int)

    df = _adicionar_limites_iqr(df)

    outlier_mask = (df["VOLUME_REAL"] < df["_lower"]) | (df["VOLUME_REAL"] > df["_upper"])

    for col in ["VOLUME_FORNECEDOR_01", "VOLUME_FORNECEDOR_02", "VOLUME_FORNECEDOR_03"]:
        df[col] = df[col].clip(upper=df["_upper"])

    df = df[~outlier_mask].drop(columns=["_lower", "_upper"]).copy()

    return df, sku


def apply_filters(df, fornecedores=None, categorias=None, abc_classes=None, meses=None):
    filtered = df.copy()

    if categorias:
        filtered = filtered[filtered["CATEGORIA"].isin(categorias)]

    if abc_classes:
        filtered = filtered[filtered["CLASS_ABC"].isin(abc_classes)]

    if meses:
        filtered = filtered[filtered["TEMPO"].isin(meses)]

    return filtered

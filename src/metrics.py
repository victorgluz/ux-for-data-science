import numpy as np
import pandas as pd

from src.data_loader import FORNECEDORES, LABELS


def wape(real: pd.Series, prev: pd.Series) -> float:
    total_real = real.sum()
    if total_real == 0:
        return np.nan
    return float(np.abs(real - prev).sum() / total_real)


def forecast_accuracy(real: pd.Series, prev: pd.Series) -> float:
    return max(0.0, 1.0 - wape(real, prev))


def bias(real: pd.Series, prev: pd.Series) -> float:
    total_real = real.sum()
    if total_real == 0:
        return np.nan
    return float((prev - real).sum() / total_real)


def mae(real: pd.Series, prev: pd.Series) -> float:
    return float(np.abs(real - prev).mean())


def rmse(real: pd.Series, prev: pd.Series) -> float:
    return float(np.sqrt(((real - prev) ** 2).mean()))


def mape_safe(real: pd.Series, prev: pd.Series) -> float:
    mask = real > 0
    if mask.sum() == 0:
        return np.nan
    return float((np.abs((real[mask] - prev[mask]) / real[mask])).mean())


def compute_global_metrics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for forn in FORNECEDORES:
        col = f"VOLUME_{forn}"
        real = df["VOLUME_REAL"]
        prev = df[col]
        rows.append(
            {
                "Fornecedor": LABELS[forn],
                "WAPE": wape(real, prev),
                "FA": forecast_accuracy(real, prev),
                "Bias": bias(real, prev),
                "MAE": mae(real, prev),
                "RMSE": rmse(real, prev),
                "MAPE": mape_safe(real, prev),
            }
        )
    return pd.DataFrame(rows).set_index("Fornecedor")


def compute_metrics_by_group(df: pd.DataFrame, grupo_col: str) -> pd.DataFrame:
    rows = []
    for g, grp in df.groupby(grupo_col):
        for forn in FORNECEDORES:
            col = f"VOLUME_{forn}"
            real = grp["VOLUME_REAL"]
            prev = grp[col]
            rows.append(
                {
                    grupo_col: g,
                    "Fornecedor": LABELS[forn],
                    "WAPE": wape(real, prev),
                    "FA": forecast_accuracy(real, prev),
                    "Bias": bias(real, prev),
                    "n_registros": len(grp),
                    "volume_real_total": real.sum(),
                }
            )
    return pd.DataFrame(rows)


def compute_temporal_metrics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tempo, grp in df.groupby("TEMPO"):
        for forn in FORNECEDORES:
            col = f"VOLUME_{forn}"
            real = grp["VOLUME_REAL"]
            prev = grp[col]
            rows.append(
                {
                    "TEMPO": tempo,
                    "Fornecedor": LABELS[forn],
                    "FA": forecast_accuracy(real, prev),
                    "WAPE": wape(real, prev),
                    "Bias": bias(real, prev),
                }
            )
    return pd.DataFrame(rows)


def compute_scorecard(df: pd.DataFrame, temporal_df: pd.DataFrame | None = None) -> pd.DataFrame:
    if temporal_df is None:
        temporal_df = compute_temporal_metrics(df)

    vol_por_material = (
        df.groupby("MATERIAL")["VOLUME_REAL"].sum().sort_values(ascending=False)
    )
    top20_materiais = vol_por_material.head(20).index
    df_top20 = df[df["MATERIAL"].isin(top20_materiais)]

    rows = []
    for forn in FORNECEDORES:
        col = f"VOLUME_{forn}"
        lbl = LABELS[forn]
        real = df["VOLUME_REAL"]
        prev = df[col]

        real_a = df[df["CLASS_ABC"] == "A"]["VOLUME_REAL"]
        prev_a = df[df["CLASS_ABC"] == "A"][col]

        camp_real = df[df["CAMPANHA_FLAG"] == 1]["VOLUME_REAL"]
        camp_prev = df[df["CAMPANHA_FLAG"] == 1][col]

        std_fa = temporal_df[temporal_df["Fornecedor"] == lbl]["FA"].std()

        b = bias(real, prev)
        rows.append(
            {
                "Fornecedor": lbl,
                "FA Global": forecast_accuracy(real, prev),
                "FA Classe A": forecast_accuracy(real_a, prev_a),
                "FA Campanha": forecast_accuracy(camp_real, camp_prev),
                "Bias": b,
                "Bias Global Abs": abs(b),
                "FA Top-20 SKUs": forecast_accuracy(
                    df_top20["VOLUME_REAL"], df_top20[col]
                ),
                "Consistência (Std FA)": std_fa,
            }
        )
    return pd.DataFrame(rows).set_index("Fornecedor")


def compute_wape_per_sku(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mat, sub in df.groupby("MATERIAL"):
        real = sub["VOLUME_REAL"]
        if real.sum() == 0:
            continue
        row = {"MATERIAL": mat, "volume_real": real.sum()}
        for forn in FORNECEDORES:
            row[LABELS[forn]] = wape(real, sub[f"VOLUME_{forn}"])
        rows.append(row)
    return pd.DataFrame(rows)


def compute_fa_por_decil(df: pd.DataFrame) -> pd.DataFrame:
    vol_por_mat = df.groupby("MATERIAL")["VOLUME_REAL"].sum()
    decis = pd.qcut(vol_por_mat, 10, labels=[f"D{i+1}" for i in range(10)])
    df_dec = df.merge(decis.rename("DECIL"), on="MATERIAL")
    rows = []
    for d, sub in df_dec.groupby("DECIL", observed=True):
        for forn in FORNECEDORES:
            rows.append(
                {
                    "Decil": d,
                    "Fornecedor": LABELS[forn],
                    "FA": forecast_accuracy(sub["VOLUME_REAL"], sub[f"VOLUME_{forn}"]),
                    "volume_real": sub["VOLUME_REAL"].sum(),
                }
            )
    return pd.DataFrame(rows)


def compute_uplift_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (loja, mat), sub in df.groupby(["LOJA", "MATERIAL"]):
        com = sub[sub["CAMPANHA_FLAG"] == 1]
        sem = sub[sub["CAMPANHA_FLAG"] == 0]
        if len(com) == 0 or len(sem) == 0:
            continue
        base_real = sem["VOLUME_REAL"].mean()
        if base_real <= 0:
            continue
        row = {"LOJA": loja, "MATERIAL": mat, "uplift_real": com["VOLUME_REAL"].mean() / base_real}
        valid = True
        for forn in FORNECEDORES:
            base = sem[f"VOLUME_{forn}"].mean()
            if base <= 0:
                valid = False
                break
            row[LABELS[forn]] = com[f"VOLUME_{forn}"].mean() / base
        if valid:
            rows.append(row)
    return pd.DataFrame(rows)


def compute_coverage_zeros(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = len(df)
    for forn in FORNECEDORES:
        col = f"VOLUME_{forn}"
        n_zero = int((df[col] == 0).sum())
        n_zero_real_pos = int(((df[col] == 0) & (df["VOLUME_REAL"] > 0)).sum())
        n_zero_real_zero = int(((df[col] == 0) & (df["VOLUME_REAL"] == 0)).sum())
        rows.append(
            {
                "Fornecedor": LABELS[forn],
                "Previsões zero": n_zero,
                "% sobre total": n_zero / total * 100,
                "Zero c/ real>0 (ruptura prevista)": n_zero_real_pos,
                "Zero c/ real=0 (acertou ausência)": n_zero_real_zero,
            }
        )
    return pd.DataFrame(rows).set_index("Fornecedor")


PESOS_DEFAULT = {
    "FA Global": 0.30,
    "FA Classe A": 0.25,
    "FA Campanha": 0.20,
    "FA Top-20 SKUs": 0.15,
    "Consistência (Std FA)": 0.10,
}


def compute_ranking(scorecard: pd.DataFrame, pesos: dict | None = None) -> pd.DataFrame:
    if pesos is None:
        pesos = PESOS_DEFAULT

    score_norm = scorecard.copy()

    for col in ["FA Global", "FA Classe A", "FA Campanha", "FA Top-20 SKUs"]:
        col_min, col_max = score_norm[col].min(), score_norm[col].max()
        if col_max > col_min:
            score_norm[col] = (score_norm[col] - col_min) / (col_max - col_min)
        else:
            score_norm[col] = 1.0

    col_std = "Consistência (Std FA)"
    col_min, col_max = score_norm[col_std].min(), score_norm[col_std].max()
    if col_max > col_min:
        score_norm[col_std] = 1 - (score_norm[col_std] - col_min) / (col_max - col_min)
    else:
        score_norm[col_std] = 1.0

    score_norm["Score Final"] = sum(
        score_norm[col] * peso for col, peso in pesos.items()
    )

    ranking = score_norm[["Score Final"]].sort_values("Score Final", ascending=False)
    ranking["Posição"] = range(1, len(ranking) + 1)
    return ranking

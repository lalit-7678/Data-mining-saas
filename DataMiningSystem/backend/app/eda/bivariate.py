import numpy as np
import pandas as pd


def compute_bivariate_analysis(
    df: pd.DataFrame, col1: str, col2: str, top_n: int = 10
) -> dict:
    if col1 not in df.columns or col2 not in df.columns:
        return {"error": "One or both columns not found in dataset."}

    # 1. NUMERICAL vs NUMERICAL (Scatter Plot + Correlation)
    if pd.api.types.is_numeric_dtype(
        df[col1]
    ) and pd.api.types.is_numeric_dtype(df[col2]):
        clean_df = df[[col1, col2]].dropna()
        if len(clean_df) == 0:
            return {"error": "No valid data pairs remaining after dropping NaNs."}

        corr = float(clean_df[col1].corr(clean_df[col2]))

        # Downsample scatter points for smooth frontend rendering if > 1000 rows
        scatter_data = clean_df
        if len(clean_df) > 1000:
            scatter_data = clean_df.sample(n=1000, random_state=42)

        points = [
            {"x": float(row[col1]), "y": float(row[col2])}
            for _, row in scatter_data.iterrows()
        ]

        return {
            "type": "num_num",
            "columns": [col1, col2],
            "correlation": round(corr, 4),
            "chart_type": "scatter",
            "data": points,
        }

    # 2. CATEGORICAL vs NUMERICAL (Grouped Statistics + Boxplot Data)
    elif (
        pd.api.types.is_numeric_dtype(df[col1])
        and not pd.api.types.is_numeric_dtype(df[col2])
    ) or (
        pd.api.types.is_numeric_dtype(df[col2])
        and not pd.api.types.is_numeric_dtype(df[col1])
    ):

        num_col = col1 if pd.api.types.is_numeric_dtype(df[col1]) else col2
        cat_col = col2 if num_col == col1 else col1

        clean_df = df[[cat_col, num_col]].dropna()
        top_cats = clean_df[cat_col].value_counts().head(top_n).index.tolist()
        filtered_df = clean_df[clean_df[cat_col].isin(top_cats)]

        grouped_stats = []
        for cat, group in filtered_df.groupby(cat_col):
            series = group[num_col]
            if len(series) == 0:
                continue
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            grouped_stats.append(
                {
                    "category": str(cat),
                    "mean": round(float(series.mean()), 2),
                    "median": round(float(series.median()), 2),
                    "std": round(float(series.std()), 2) if len(series) > 1 else 0.0,
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2),
                    "q1": round(q1, 2),
                    "q3": round(q3, 2),
                }
            )

        return {
            "type": "cat_num",
            "num_column": num_col,
            "cat_column": cat_col,
            "chart_type": "grouped_bar",
            "data": grouped_stats,
        }

    # 3. CATEGORICAL vs CATEGORICAL (Crosstab Heatmap)
    else:
        clean_df = df[[col1, col2]].dropna()
        crosstab = pd.crosstab(
            clean_df[col1], clean_df[col2], normalize="index"
        ) * 100

        crosstab = crosstab.iloc[:top_n, :top_n]

        heatmap_data = []
        for r_idx, row in crosstab.iterrows():
            for c_col, val in row.items():
                heatmap_data.append(
                    {
                        "var1": str(r_idx),
                        "var2": str(c_col),
                        "percentage": round(float(val), 2),
                    }
                )

        return {
            "type": "cat_cat",
            "columns": [col1, col2],
            "chart_type": "heatmap",
            "data": heatmap_data,
        }
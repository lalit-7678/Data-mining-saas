import numpy as np
import pandas as pd


def generate_key_insights(df: pd.DataFrame) -> dict:
    insights = []

    # 1. Skewness Insights
    for col in df.select_dtypes(include=[np.number]).columns:
        if col.lower().endswith("_id") or col.lower() == "id":
            continue
        series = df[col].dropna()
        if len(series) > 2:
            skew = float(series.skew())
            if abs(skew) >= 3.0:
                insights.append(
                    {
                        "title": f"Extreme Right/Left Skew in '{col}'",
                        "finding": f"Distribution for '{col}' is heavily skewed.",
                        "evidence": f"Skewness = {round(skew, 2)}, Median = {round(float(series.median()), 2)}, Mean = {round(float(series.mean()), 2)}",
                        "columns": [col],
                        "severity": "MEDIUM",
                        "interpretation": "A small number of extreme values are pulling the mean away from the typical median observation.",
                    }
                )

    # 2. Strong Correlation Insights
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] >= 2:
        corr_matrix = num_df.corr().abs()
        np.fill_diagonal(corr_matrix.values, 0)

        for col1 in corr_matrix.columns:
            for col2 in corr_matrix.columns:
                if col1 < col2:  # Avoid duplicate pairs
                    val = float(corr_matrix.loc[col1, col2])
                    if val >= 0.75:
                        insights.append(
                            {
                                "title": f"Strong Correlation: '{col1}' & '{col2}'",
                                "finding": f"High linear statistical association detected.",
                                "evidence": f"Pearson Correlation = {round(val, 2)}",
                                "columns": [col1, col2],
                                "severity": "HIGH",
                                "interpretation": "These two metrics move together strongly. Check for multicollinearity if planning prediction models.",
                            }
                        )

    # 3. Dominant Category Insights
    for col in df.select_dtypes(include=["object", "category"]).columns:
        if col.lower().endswith("_id") or col.lower() == "id":
            continue
        value_counts = df[col].value_counts(normalize=True)
        if not value_counts.empty and value_counts.iloc[0] >= 0.70:
            top_cat = str(value_counts.index[0])
            top_pct = round(float(value_counts.iloc[0]) * 100, 1)
            insights.append(
                {
                    "title": f"Dominant Class in '{col}'",
                    "finding": f"Single category dominates '{col}'.",
                    "evidence": f"Category '{top_cat}' represents {top_pct}% of total records.",
                    "columns": [col],
                    "severity": "MEDIUM",
                    "interpretation": "Low variance in categorical representation. Target outcomes or features might be heavily imbalanced.",
                }
            )

    return {"total_insights": len(insights), "insights": insights}
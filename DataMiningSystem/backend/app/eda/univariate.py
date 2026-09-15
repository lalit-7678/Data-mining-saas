import numpy as np
import pandas as pd


def compute_univariate_analysis(
    df: pd.DataFrame, column: str, top_n: int = 10
) -> dict:
    if column not in df.columns:
        return {"error": f"Column '{column}' not found in dataset."}

    series = df[column].dropna()
    total_rows = len(df)
    missing_count = int(df[column].isna().sum())
    missing_pct = (
        round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    # Identifier Column Safety Guardrail
    if column.lower().endswith("_id") or column.lower() == "id":
        return {
            "column": column,
            "type": "identifier",
            "message": "Identifier column detected. Skipping distribution charts to prevent meaningless visuals.",
            "unique_count": int(df[column].nunique()),
            "missing_pct": missing_pct,
        }

    # A. NUMERICAL ANALYSIS
    if pd.api.types.is_numeric_dtype(df[column]):
        if len(series) == 0:
            return {
                "column": column,
                "type": "numerical",
                "error": "All values are missing.",
            }

        mean_val = float(series.mean())
        median_val = float(series.median())
        mode_val = float(series.mode()[0]) if not series.mode().empty else None
        std_val = float(series.std()) if len(series) > 1 else 0.0
        var_val = float(series.var()) if len(series) > 1 else 0.0
        min_val = float(series.min())
        max_val = float(series.max())

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        skew = (
            float(series.skew())
            if len(series) > 2
            else 0.0
        )
        kurt = (
            float(series.kurtosis())
            if len(series) > 3
            else 0.0
        )

        # 10-Bin Histogram Setup
        counts, bin_edges = np.histogram(series, bins=10)
        histogram_data = []
        for i in range(len(counts)):
            histogram_data.append(
                {
                    "bin_start": round(float(bin_edges[i]), 2),
                    "bin_end": round(float(bin_edges[i + 1]), 2),
                    "count": int(counts[i]),
                }
            )

        # Boxplot Outer Outliers Detection
        lower_whisker = float(max(min_val, q1 - 1.5 * iqr))
        upper_whisker = float(min(max_val, q3 + 1.5 * iqr))
        outliers = series[
            (series < lower_whisker) | (series > upper_whisker)
        ].tolist()

        return {
            "column": column,
            "type": "numerical",
            "statistics": {
                "mean": round(mean_val, 2),
                "median": round(median_val, 2),
                "mode": round(mode_val, 2) if mode_val is not None else None,
                "std": round(std_val, 2),
                "variance": round(var_val, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "skewness": round(skew, 2),
                "kurtosis": round(kurt, 2),
                "missing_pct": missing_pct,
            },
            "chart_data": {
                "histogram": histogram_data,
                "boxplot": {
                    "min": round(min_val, 2),
                    "q1": round(q1, 2),
                    "median": round(median_val, 2),
                    "q3": round(q3, 2),
                    "max": round(max_val, 2),
                    "lower_whisker": round(lower_whisker, 2),
                    "upper_whisker": round(upper_whisker, 2),
                    "outliers_count": len(outliers),
                },
            },
        }

    # B. DATETIME ANALYSIS
    elif pd.api.types.is_datetime64_any_dtype(df[column]):
        dt_series = pd.to_datetime(df[column], errors="coerce").dropna()
        if len(dt_series) == 0:
            return {
                "column": column,
                "type": "datetime",
                "error": "No valid dates found.",
            }

        min_date = str(dt_series.min())
        max_date = str(dt_series.max())
        date_range_days = (dt_series.max() - dt_series.min()).days

        year_dist = dt_series.dt.year.value_counts().to_dict()
        month_dist = dt_series.dt.strftime("%Y-%m").value_counts().to_dict()

        return {
            "column": column,
            "type": "datetime",
            "statistics": {
                "min_date": min_date,
                "max_date": max_date,
                "range_days": date_range_days,
                "missing_pct": missing_pct,
            },
            "chart_data": {
                "year_distribution": [
                    {"year": str(k), "count": int(v)} for k, v in year_dist.items()
                ],
                "month_distribution": [
                    {"month": str(k), "count": int(v)}
                    for k, v in list(month_dist.items())[:12]
                ],
            },
        }

    # C. CATEGORICAL ANALYSIS
    else:
        unique_count = int(series.nunique())
        value_counts = series.value_counts()

        high_cardinality = unique_count > 50
        top_categories = value_counts.head(top_n)

        freq_distribution = []
        for cat, cnt in top_categories.items():
            freq_distribution.append(
                {
                    "category": str(cat),
                    "count": int(cnt),
                    "percentage": round((cnt / len(series)) * 100, 2),
                }
            )

        return {
            "column": column,
            "type": "categorical",
            "high_cardinality_flag": high_cardinality,
            "statistics": {
                "unique_values": unique_count,
                "most_frequent": (
                    str(value_counts.index[0])
                    if not value_counts.empty
                    else None
                ),
                "most_frequent_count": (
                    int(value_counts.iloc[0]) if not value_counts.empty else 0
                ),
                "least_frequent": (
                    str(value_counts.index[-1])
                    if not value_counts.empty
                    else None
                ),
                "missing_pct": missing_pct,
            },
            "chart_data": {
                "top_categories": freq_distribution,
                "note": (
                    "High-cardinality variable detected (>50 categories). Showing Top-N."
                    if high_cardinality
                    else "Standard distribution."
                ),
            },
        }
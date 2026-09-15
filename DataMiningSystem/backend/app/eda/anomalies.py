import numpy as np
import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> dict:
    findings = []
    total_rows = len(df)

    for col in df.columns:
        # A. Constant Columns
        if df[col].nunique(dropna=False) <= 1:
            findings.append(
                {
                    "column": col,
                    "type": "Constant Column",
                    "severity": "HIGH",
                    "description": f"Column '{col}' contains only 1 unique value across all rows. It provides zero variance/information.",
                }
            )
            continue

        # B. High Missingness
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / total_rows) * 100
        if missing_pct >= 40.0:
            findings.append(
                {
                    "column": col,
                    "type": "High Missingness",
                    "severity": "HIGH" if missing_pct > 70 else "MEDIUM",
                    "description": f"Column '{col}' has {round(missing_pct, 1)}% missing values ({missing_count} rows).",
                }
            )

        # C. High Cardinality (Categorical)
        if (
            not pd.api.types.is_numeric_dtype(df[col])
            and not pd.api.types.is_datetime64_any_dtype(df[col])
        ):
            unique_cnt = df[col].nunique()
            if unique_cnt > 50 and not (
                col.lower().endswith("_id") or col.lower() == "id"
            ):
                findings.append(
                    {
                        "column": col,
                        "type": "High Cardinality",
                        "severity": "LOW",
                        "description": f"Categorical column '{col}' has {unique_cnt} unique values. Consider grouping or Top-N aggregations.",
                    }
                )

        # D. High Skewness & Outliers (Numerical)
        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()
            if len(series) > 2:
                skewness = series.skew()
                if abs(skewness) > 2.0:
                    findings.append(
                        {
                            "column": col,
                            "type": "High Skewness",
                            "severity": "MEDIUM",
                            "description": f"Column '{col}' is highly skewed (Skewness = {round(skewness, 2)}). Distribution is heavily asymmetric.",
                        }
                    )

                # Outlier count via IQR
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                outlier_cnt = (
                    (series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr))
                ).sum()
                outlier_pct = (outlier_cnt / len(series)) * 100

                if outlier_pct > 5.0:
                    findings.append(
                        {
                            "column": col,
                            "type": "Potential Outliers",
                            "severity": "LOW",
                            "description": f"Detected {outlier_cnt} potential statistical outliers ({round(outlier_pct, 1)}% of values) outside IQR 1.5x bounds.",
                        }
                    )

    return {"total_findings": len(findings), "findings": findings}
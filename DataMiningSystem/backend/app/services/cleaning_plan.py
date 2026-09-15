import pandas as pd
import numpy as np
from typing import List, Dict, Any

def generate_cleaning_plan(df: pd.DataFrame, semantic_profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes the dataframe and semantic classifications to construct a 
    non-destructive, actionable Cleaning Plan.
    """
    plan_items = []
    total_rows = len(df)
    
    # ---------------------------------------------------------
    # 1. DUPLICATE ROWS CHECK
    # ---------------------------------------------------------
    exact_duplicates = int(df.duplicated().sum())
    if exact_duplicates > 0:
        plan_items.append({
            "id": "dup_exact_rows",
            "column": "__dataframe__",
            "issue_type": "Duplicate Rows",
            "severity": "MEDIUM",
            "recommended_action": "Remove exact duplicate rows",
            "method": "pandas.DataFrame.drop_duplicates",
            "reason": f"Found {exact_duplicates} exact duplicate row(s) across all columns.",
            "confidence": 100,
            "affected_rows": exact_duplicates,
            "status": "Pending Review",
            "approved": False,
            "category": "DUPLICATE",
            "metadata": {"duplicate_count": exact_duplicates}
        })

    # Map semantic profiles by column name for quick lookup
    profile_map = {item["name"]: item for item in semantic_profiles}

    for col in df.columns:
        series = df[col]
        profile = profile_map.get(col, {})
        semantic_type = profile.get("semantic_type", "CATEGORICAL")
        
        # ---------------------------------------------------------
        # 2. TYPE MISMATCHES (String -> Datetime / Numerical)
        # ---------------------------------------------------------
        if semantic_type == "DATETIME" and str(series.dtype) in ["object", "string"]:
            non_nulls = series.dropna()
            parsed_dates = pd.to_datetime(non_nulls, errors="coerce")
            invalid_count = int(parsed_dates.isna().sum())
            
            plan_items.append({
                "id": f"type_{col}_datetime",
                "column": col,
                "issue_type": "Physical Type Mismatch",
                "severity": "LOW",
                "recommended_action": "Convert string to datetime64",
                "method": "pandas.to_datetime",
                "reason": f"Column semantic type is DATETIME but physical type is {series.dtype}.",
                "confidence": profile.get("confidence", 90),
                "affected_rows": invalid_count,  # Invalid dates that would become NaT
                "status": "Pending Review",
                "approved": False,
                "category": "TYPE_CONVERSION",
                "metadata": {"invalid_date_count": invalid_count}
            })

        # ---------------------------------------------------------
        # 3. MISSING VALUE HANDLING PLAN
        # ---------------------------------------------------------
        missing_count = int(series.isna().sum())
        if missing_count > 0:
            if semantic_type == "IDENTIFIER":
                plan_items.append({
                    "id": f"missing_{col}_id",
                    "column": col,
                    "issue_type": "Missing Primary Identifier",
                    "severity": "HIGH",
                    "recommended_action": "Investigate missing key values (No Auto-Imputation)",
                    "method": "manual_review",
                    "reason": "Identifier columns should never be automatically imputed.",
                    "confidence": 100,
                    "affected_rows": missing_count,
                    "status": "Requires Attention",
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": "none"}
                })
            elif semantic_type == "NUMERICAL":
                non_nulls = series.dropna()
                skewness = float(non_nulls.skew()) if len(non_nulls) > 2 else 0.0
                strategy = "median" if abs(skewness) > 1.0 else "mean"
                
                plan_items.append({
                    "id": f"missing_{col}_num",
                    "column": col,
                    "issue_type": "Missing Numerical Values",
                    "severity": "MEDIUM",
                    "recommended_action": f"Impute missing values using {strategy.upper()} (Skewness: {round(skewness, 2)})",
                    "method": f"pandas.fillna({strategy})",
                    "reason": f"Distribution is {'skewed' if abs(skewness) > 1.0 else 'symmetric'}.",
                    "confidence": 90,
                    "affected_rows": missing_count,
                    "status": "Pending Review",
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": strategy, "skewness": round(skewness, 2)}
                })
            elif semantic_type == "CATEGORICAL":
                unique_count = int(series.nunique())
                strategy = "mode" if unique_count <= 20 else "Unknown"
                
                plan_items.append({
                    "id": f"missing_{col}_cat",
                    "column": col,
                    "issue_type": "Missing Categorical Values",
                    "severity": "MEDIUM",
                    "recommended_action": f"Fill missing values with '{strategy}'",
                    "method": "pandas.fillna",
                    "reason": f"Low-cardinality categorical column ({unique_count} unique values)." if strategy == "mode" else "High-cardinality categorical column.",
                    "confidence": 85,
                    "affected_rows": missing_count,
                    "status": "Pending Review",
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": strategy}
                })

        # ---------------------------------------------------------
        # 4. OUTLIER DIAGNOSTICS (NON-DESTRUCTIVE)
        # ---------------------------------------------------------
        if semantic_type == "NUMERICAL":
            non_nulls = series.dropna()
            if len(non_nulls) > 4:
                q1 = float(non_nulls.quantile(0.25))
                q3 = float(non_nulls.quantile(0.75))
                iqr = q3 - q1
                lower_bound = q1 - (1.5 * iqr)
                upper_bound = q3 + (1.5 * iqr)
                
                outliers = non_nulls[(non_nulls < lower_bound) | (non_nulls > upper_bound)]
                outlier_count = int(len(outliers))
                
                if outlier_count > 0:
                    outlier_pct = round((outlier_count / total_rows) * 100, 2)
                    plan_items.append({
                        "id": f"outlier_{col}_iqr",
                        "column": col,
                        "issue_type": "Suspected Numerical Outliers",
                        "severity": "LOW",
                        "recommended_action": "Review suspected outliers (Do not auto-delete)",
                        "method": "IQR_bounds_check",
                        "reason": f"Found {outlier_count} values outside [{round(lower_bound, 2)}, {round(upper_bound, 2)}].",
                        "confidence": 80,
                        "affected_rows": outlier_count,
                        "status": "Pending Review",
                        "approved": False,
                        "category": "OUTLIER",
                        "metadata": {
                            "lower_bound": round(lower_bound, 2),
                            "upper_bound": round(upper_bound, 2),
                            "outlier_count": outlier_count,
                            "outlier_pct": outlier_pct
                        }
                    })

    return plan_items
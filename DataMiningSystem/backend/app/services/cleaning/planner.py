import pandas as pd
import numpy as np
from typing import List, Dict, Any

def generate_cleaning_plan(df: pd.DataFrame, semantic_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    plan_items = []
    total_rows = len(df)
    
    # 1. DUPLICATE ROWS
    exact_duplicates = int(df.duplicated().sum())
    if exact_duplicates > 0:
        plan_items.append({
            "id": "dup_exact_rows",
            "column": "__dataframe__",
            "issue_type": "Duplicate Rows",
            "severity": "MEDIUM",
            "current_state": f"{exact_duplicates} duplicate rows ({round((exact_duplicates/total_rows)*100, 2)}%)",
            "proposed_action": "Remove exact duplicate rows",
            "method": "pandas.DataFrame.drop_duplicates",
            "reason": f"Found {exact_duplicates} exact duplicate row(s) across all columns.",
            "confidence": 100,
            "risk": "SAFE",
            "affected_rows": exact_duplicates,
            "approved": False,
            "category": "DUPLICATE",
            "metadata": {"duplicate_count": exact_duplicates}
        })

    profile_map = {item["name"]: item for item in semantic_profiles}

    for col in df.columns:
        series = df[col]
        profile = profile_map.get(col, {})
        semantic_type = profile.get("semantic_type", "CATEGORICAL")
        physical_type = str(series.dtype)

        # 2. TYPE MISMATCHES
        if semantic_type == "DATETIME" and physical_type in ["object", "string"]:
            non_nulls = series.dropna()
            parsed_dates = pd.to_datetime(non_nulls, errors="coerce")
            invalid_count = int(parsed_dates.isna().sum())
            conf = profile.get("confidence", 90)
            risk = "SAFE" if (invalid_count == 0 and conf >= 90) else "REVIEW_REQUIRED"
            
            plan_items.append({
                "id": f"type_{col}_datetime",
                "column": col,
                "issue_type": "Physical Type Mismatch",
                "severity": "LOW" if risk == "SAFE" else "MEDIUM",
                "current_state": f"Stored as {physical_type}",
                "proposed_action": "Convert string to datetime64",
                "method": "pandas.to_datetime",
                "reason": f"Column semantic type is DATETIME. {invalid_count} values failed parsing.",
                "confidence": conf,
                "risk": risk,
                "affected_rows": invalid_count,
                "approved": False,
                "category": "TYPE_CONVERSION",
                "metadata": {"target_type": "datetime64[ns]", "invalid_date_count": invalid_count}
            })

        # 3. MISSING VALUES
        missing_count = int(series.isna().sum())
        if missing_count > 0:
            if semantic_type == "IDENTIFIER":
                plan_items.append({
                    "id": f"missing_{col}_id",
                    "column": col,
                    "issue_type": "Missing Primary Identifier",
                    "severity": "HIGH",
                    "current_state": f"{missing_count} missing values",
                    "proposed_action": "Investigate missing key values (No Auto-Imputation)",
                    "method": "manual_review",
                    "reason": "Primary keys and unique identifiers must never be automatically imputed.",
                    "confidence": 100,
                    "risk": "REVIEW_REQUIRED",
                    "affected_rows": missing_count,
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": "none"}
                })
            elif semantic_type == "NUMERICAL":
                non_nulls = series.dropna()
                skewness = float(non_nulls.skew()) if len(non_nulls) > 2 else 0.0
                strategy = "median" if abs(skewness) > 1.0 else "mean"
                risk = "SAFE" if abs(skewness) <= 1.0 else "REVIEW_REQUIRED"
                
                plan_items.append({
                    "id": f"missing_{col}_num",
                    "column": col,
                    "issue_type": "Missing Numerical Values",
                    "severity": "MEDIUM",
                    "current_state": f"{missing_count} missing values ({round((missing_count/total_rows)*100, 2)}%)",
                    "proposed_action": f"Impute missing values using {strategy.upper()}",
                    "method": f"pandas.fillna({strategy})",
                    "reason": f"Distribution skewness is {round(skewness, 2)}. Preferred strategy: {strategy}.",
                    "confidence": 90,
                    "risk": risk,
                    "affected_rows": missing_count,
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": strategy, "skewness": round(skewness, 2)}
                })
            elif semantic_type == "CATEGORICAL":
                unique_count = int(series.nunique())
                strategy = "mode" if unique_count <= 20 else "Unknown"
                risk = "SAFE" if strategy == "mode" else "REVIEW_REQUIRED"
                
                plan_items.append({
                    "id": f"missing_{col}_cat",
                    "column": col,
                    "issue_type": "Missing Categorical Values",
                    "severity": "MEDIUM",
                    "current_state": f"{missing_count} missing values",
                    "proposed_action": f"Fill missing values with '{strategy}'",
                    "method": f"pandas.fillna('{strategy}')",
                    "reason": f"Low-cardinality feature ({unique_count} unique categories)." if strategy == "mode" else "High-cardinality feature; explicit label avoids distortion.",
                    "confidence": 85,
                    "risk": risk,
                    "affected_rows": missing_count,
                    "approved": False,
                    "category": "MISSING_VALUE",
                    "metadata": {"strategy": strategy}
                })

        # 4. OUTLIER DIAGNOSTICS (NON-DESTRUCTIVE)
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
                    plan_items.append({
                        "id": f"outlier_{col}_iqr",
                        "column": col,
                        "issue_type": "Suspected Numerical Outliers",
                        "severity": "LOW",
                        "current_state": f"{outlier_count} values outside IQR bounds",
                        "proposed_action": "Flag & Review Outliers (No Deletion)",
                        "method": "IQR_bounds_flagging",
                        "reason": f"Values lie outside range [{round(lower_bound, 2)}, {round(upper_bound, 2)}]. Outliers may represent valid extreme records.",
                        "confidence": 80,
                        "risk": "REVIEW_REQUIRED",
                        "affected_rows": outlier_count,
                        "approved": False,
                        "category": "OUTLIER",
                        "metadata": {
                            "lower_bound": round(lower_bound, 2),
                            "upper_bound": round(upper_bound, 2),
                            "outlier_count": outlier_count
                        }
                    })

    safe_count = sum(1 for i in plan_items if i["risk"] == "SAFE")
    review_count = sum(1 for i in plan_items if i["risk"] == "REVIEW_REQUIRED")

    return {
        "total_items": len(plan_items),
        "safe_count": safe_count,
        "review_required_count": review_count,
        "items": plan_items
    }
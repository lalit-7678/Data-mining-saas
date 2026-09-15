import pandas as pd
import numpy as np

def generate_cleaning_diagnosis(df: pd.DataFrame, semantic_analysis: list) -> dict:
    """
    Non-destructive diagnostic engine that generates a structured cleaning plan
    based on semantic profiling results.
    """
    total_rows = len(df)
    cleaning_plan = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    # 1. DUPLICATE DETECTION
    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    if duplicate_rows > 0:
        severity = "HIGH" if duplicate_pct > 5.0 else "MEDIUM"
        severity_counts[severity] += 1
        cleaning_plan.append({
            "column": "DATASET_LEVEL",
            "issue_type": "duplicate_rows",
            "severity": severity,
            "current_state": f"{duplicate_rows} exact duplicate rows ({duplicate_pct}%)",
            "recommended_action": "review_and_deduplicate",
            "recommended_method": "drop_duplicates",
            "reason": f"Exact duplicate rows detected ({duplicate_rows} records) which can bias statistical analysis.",
            "confidence": 0.99
        })

    # 2. COLUMN-BY-COLUMN QUALITY DIAGNOSIS
    for col_info in semantic_analysis:
        col_name = col_info.get("name")
        if not col_name or col_name not in df.columns:
            continue

        # Normalize semantic type to lowercase for safe comparisons
        semantic_type = str(col_info.get("semantic_type", "")).lower()
        physical_type = str(col_info.get("physical_type", "")).lower()
        
        missing_count = col_info.get("missing_count", int(df[col_name].isna().sum()))
        missing_pct = col_info.get("missing_pct", round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0)
        
        series = df[col_name]
        non_null = series.dropna()

        # A. MISSING VALUE DIAGNOSIS
        if missing_count > 0:
            if "identifier" in semantic_type or semantic_type == "id":
                severity = "CRITICAL" if missing_pct > 1.0 else "HIGH"
                severity_counts[severity] += 1
                cleaning_plan.append({
                    "column": col_name,
                    "issue_type": "missing_identifiers",
                    "severity": severity,
                    "current_state": f"{missing_count} missing IDs ({missing_pct}%)",
                    "recommended_action": "manual_review",
                    "recommended_method": "flag_or_exclude",
                    "reason": "Identifiers cannot be automatically imputed without creating duplicate keys.",
                    "confidence": 0.98
                })

            elif "datetime" in semantic_type or "date" in semantic_type:
                severity = "HIGH" if missing_pct > 10.0 else "MEDIUM"
                severity_counts[severity] += 1
                cleaning_plan.append({
                    "column": col_name,
                    "issue_type": "missing_dates",
                    "severity": severity,
                    "current_state": f"{missing_count} missing dates ({missing_pct}%)",
                    "recommended_action": "flag_missingness",
                    "recommended_method": "preserve_or_filter",
                    "reason": "Date imputation using mean/median introduces artificial time biases.",
                    "confidence": 0.95
                })

            elif "numeric" in semantic_type or "number" in semantic_type or "float" in semantic_type or "int" in semantic_type:
                stats = col_info.get("stats", {})
                skewness = abs(stats.get("skewness", 0.0))
                method = "median" if skewness > 1.0 else "mean"
                severity = "HIGH" if missing_pct > 20.0 else ("MEDIUM" if missing_pct > 5.0 else "LOW")
                severity_counts[severity] += 1
                
                cleaning_plan.append({
                    "column": col_name,
                    "issue_type": "missing_numerical",
                    "severity": severity,
                    "current_state": f"{missing_count} missing cells ({missing_pct}%)",
                    "recommended_action": "impute",
                    "recommended_method": f"{method}_imputation",
                    "reason": f"Distribution skewness is {round(skewness, 2)}. Using {method} preserves central tendency.",
                    "confidence": 0.92
                })

            elif "cat" in semantic_type or "string" in semantic_type or "text" in semantic_type:
                method = "mode" if missing_pct < 5.0 else "explicit_unknown_category"
                severity = "HIGH" if missing_pct > 20.0 else ("MEDIUM" if missing_pct > 5.0 else "LOW")
                severity_counts[severity] += 1
                
                cleaning_plan.append({
                    "column": col_name,
                    "issue_type": "missing_categorical",
                    "severity": severity,
                    "current_state": f"{missing_count} missing cells ({missing_pct}%)",
                    "recommended_action": "impute_or_encode",
                    "recommended_method": method,
                    "reason": "Higher missingness is safer as an explicit 'Unknown' category rather than forcing mode.",
                    "confidence": 0.90
                })

        # B. OUTLIER DIAGNOSIS (NUMERICAL ONLY - IQR METHOD)
        if ("numeric" in semantic_type or "float" in semantic_type or "int" in semantic_type) and len(non_null) > 10:
            try:
                numeric_series = pd.to_numeric(non_null, errors='coerce').dropna()
                if len(numeric_series) > 10:
                    q1 = float(numeric_series.quantile(0.25))
                    q3 = float(numeric_series.quantile(0.75))
                    iqr = q3 - q1
                    if iqr > 0:
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers = numeric_series[(numeric_series < lower_bound) | (numeric_series > upper_bound)]
                        outlier_count = len(outliers)
                        outlier_pct = round((outlier_count / len(numeric_series)) * 100, 2)

                        if outlier_count > 0:
                            severity = "MEDIUM" if outlier_pct > 5.0 else "LOW"
                            severity_counts[severity] += 1
                            cleaning_plan.append({
                                "column": col_name,
                                "issue_type": "numerical_outliers",
                                "severity": severity,
                                "current_state": f"{outlier_count} IQR outliers detected ({outlier_pct}%)",
                                "recommended_action": "review_and_cap",
                                "recommended_method": "iqr_bounds_inspection",
                                "reason": f"Values fall outside IQR bounds [{round(lower_bound, 2)}, {round(upper_bound, 2)}]. Review before capping or trimming.",
                                "confidence": 0.88
                            })
            except Exception:
                pass  # Safely ignore non-numeric series conversion issues

        # C. TYPE CONVERSION ISSUES
        if ("datetime" in semantic_type or "date" in semantic_type) and physical_type in ["object", "string"]:
            confidence_val = col_info.get("confidence", 95)
            confidence_score = round(confidence_val / 100.0, 2) if confidence_val > 1.0 else confidence_val
            
            severity_counts["LOW"] += 1
            cleaning_plan.append({
                "column": col_name,
                "issue_type": "physical_type_mismatch",
                "severity": "LOW",
                "current_state": f"Stored as string/object ({col_info.get('physical_type', 'object')})",
                "recommended_action": "type_cast",
                "recommended_method": "to_datetime64",
                "reason": f"{confidence_val}% of non-null values parse cleanly as dates.",
                "confidence": confidence_score
            })

    total_issues = len(cleaning_plan)

    return {
        "summary": {
            "total_issues": total_issues,
            "critical_severity": severity_counts["CRITICAL"],
            "high_severity": severity_counts["HIGH"],
            "medium_severity": severity_counts["MEDIUM"],
            "low_severity": severity_counts["LOW"]
        },
        "cleaning_plan": cleaning_plan
    }
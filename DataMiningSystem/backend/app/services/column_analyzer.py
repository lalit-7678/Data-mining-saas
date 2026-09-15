import pandas as pd
import numpy as np


def analyze_columns(df: pd.DataFrame) -> list:
    """
    Analyzes all columns in a pandas DataFrame to extract physical types,
    infer semantic types, compute summary statistics, and provide recommendations.
    """
    total_rows = len(df)
    results = []

    for col_name in df.columns:
        series = df[col_name]
        non_null = series.dropna()

        # Physical Data Type
        physical_type = str(series.dtype)

        # Basic Counters
        missing_count = int(series.isna().sum())
        missing_pct = (
            round((missing_count / total_rows) * 100, 2)
            if total_rows > 0
            else 0.0
        )
        unique_count = int(series.nunique(dropna=True))

        # Initialize Default Variables
        semantic_type = "CATEGORICAL"
        role = "feature"
        confidence = 80
        reason = "Default categorical inference"
        recommended_actions = []
        stats = {}

        # ----------------------------------------------------
        # 1. SEMANTIC TYPE INFERENCE ENGINE
        # ----------------------------------------------------

        # A. IDENTIFIER DETECTION
        is_id_name = any(
            id_kw in col_name.lower()
            for id_kw in ["id", "uuid", "guid", "code", "key", "number", "no"]
        )
        if unique_count == total_rows and total_rows > 0:
            semantic_type = "IDENTIFIER"
            role = "primary_key"
            confidence = 98
            reason = "100% unique values across all rows."
            recommended_actions.append("Keep as primary key or index")

        elif is_id_name and unique_count > (total_rows * 0.8):
            semantic_type = "IDENTIFIER"
            role = "key"
            confidence = 90
            reason = "High cardinality and column name matches identifier patterns."
            recommended_actions.append("Verify if column serves as a unique key")

        # B. NUMERICAL DETECTION & STATS
        elif pd.api.types.is_numeric_dtype(series):
            # Check if it acts like a categorical code (e.g., 0/1 or low cardinality integers)
            if unique_count <= 10 and not is_id_name:
                semantic_type = "CATEGORICAL"
                role = "categorical_feature"
                confidence = 85
                reason = "Low unique integer values indicate encoded categories."
                recommended_actions.append(
                    "Consider one-hot or label encoding"
                )
            else:
                semantic_type = "NUMERICAL"
                role = "feature"
                confidence = 95
                reason = "Column contains numeric values."

                # Calculate Detailed Stats
                if len(non_null) > 0:
                    mean_val = float(non_null.mean())
                    std_val = float(non_null.std(ddof=1)) if len(non_null) > 1 else 0.0
                    skewness = float(non_null.skew()) if len(non_null) > 2 else 0.0

                    stats = {
                        "mean": round(mean_val, 2),
                        "std": round(std_val, 2),
                        "min": round(float(non_null.min()), 2),
                        "max": round(float(non_null.max()), 2),
                        "skewness": round(skewness, 2),
                    }

                    if abs(skewness) > 1.0:
                        recommended_actions.append(
                            "Apply log or power transformation for skewed distribution"
                        )
                    else:
                        recommended_actions.append(
                            "Standardize or normalize for modeling"
                        )

        # C. DATETIME DETECTION
        elif pd.api.types.is_datetime64_any_dtype(series):
            semantic_type = "DATETIME"
            role = "temporal"
            confidence = 100
            reason = "Native datetime format."
            recommended_actions.append("Extract year, month, day features")

        # Check strings for date patterns
        elif physical_type in ["object", "string"] and len(non_null) > 0:
            sample = non_null.astype(str).head(50)
            parsed_dates = pd.to_datetime(sample, errors="coerce")
            valid_date_pct = (parsed_dates.notna().sum() / len(sample)) * 100

            if valid_date_pct > 80:
                semantic_type = "DATETIME"
                role = "temporal"
                confidence = int(valid_date_pct)
                reason = f"{int(valid_date_pct)}% of sampled values parse cleanly as dates."
                recommended_actions.append("Convert string to datetime type")

            # D. CATEGORICAL DETECTION (DEFAULT STRING HANDLING)
            else:
                semantic_type = "CATEGORICAL"
                role = "feature"
                confidence = 90
                reason = "Text/String column with categorical distribution."

                if unique_count > 50:
                    recommended_actions.append(
                        "High cardinality text: consider target encoding or feature extraction"
                    )
                else:
                    recommended_actions.append(
                        "Categorical: consider one-hot encoding"
                    )

        # ----------------------------------------------------
        # 2. MISSING DATA CHECKS
        # ----------------------------------------------------
        if missing_pct > 0:
            recommended_actions.append(
                f"Address {missing_pct}% missing values"
            )

        # Build Output Structure
        results.append(
            {
                "name": col_name,
                "physical_type": physical_type,
                "semantic_type": semantic_type,
                "role": role,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "confidence": confidence,
                "reason": reason,
                "recommended_actions": (
                    recommended_actions
                    if recommended_actions
                    else ["No action required"]
                ),
                "stats": stats,
            }
        )

    return results
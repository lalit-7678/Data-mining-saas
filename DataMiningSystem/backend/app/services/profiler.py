import pandas as pd
import numpy as np

def generate_data_profile(df: pd.DataFrame) -> dict:
    """
    Generates summary metrics and column-level statistics for a dataframe.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # Calculate global dataset metrics
    total_cells = total_rows * total_cols
    total_missing = int(df.isnull().sum().sum())
    missing_percentage = round((total_missing / total_cells) * 100, 2) if total_cells > 0 else 0.0
    duplicate_rows = int(df.duplicated().sum())

    columns_summary = []

    for col in df.columns:
        col_data = df[col]
        missing_count = int(col_data.isnull().sum())
        missing_pct = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        unique_count = int(col_data.nunique(dropna=True))
        inferred_type = str(col_data.dtype)

        stat_entry = {
            "name": col,
            "data_type": inferred_type,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
        }

        # Calculate numerical statistics if applicable
        if pd.api.types.is_numeric_dtype(col_data):
            stat_entry["mean"] = round(float(col_data.mean()), 2) if not pd.isna(col_data.mean()) else None
            stat_entry["std"] = round(float(col_data.std()), 2) if not pd.isna(col_data.std()) else None
            stat_entry["min"] = round(float(col_data.min()), 2) if not pd.isna(col_data.min()) else None
            stat_entry["max"] = round(float(col_data.max()), 2) if not pd.isna(col_data.max()) else None

        columns_summary.append(stat_entry)

    return {
        "summary": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_missing_cells": total_missing,
            "missing_percentage": missing_percentage,
            "duplicate_rows": duplicate_rows,
        },
        "columns": columns_summary,
    }
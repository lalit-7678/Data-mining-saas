import pandas as pd


def compute_dataset_overview(df: pd.DataFrame) -> dict:
    total_rows, total_cols = df.shape
    total_cells = total_rows * total_cols

    missing_cells = int(df.isna().sum().sum())
    missing_percentage = (
        round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0
    )

    duplicate_rows = int(df.duplicated().sum())

    memory_bytes = df.memory_usage(deep=True).sum()
    memory_usage_mb = round(float(memory_bytes) / (1024 * 1024), 2)

    column_types = {
        "numerical": [],
        "categorical": [],
        "datetime": [],
        "boolean": [],
    }

    column_details = []

    for col in df.columns:
        dtype = str(df[col].dtype)
        col_missing = int(df[col].isna().sum())
        col_missing_pct = (
            round((col_missing / total_rows) * 100, 2) if total_rows > 0 else 0.0
        )
        unique_vals = int(df[col].nunique())

        if pd.api.types.is_numeric_dtype(df[col]):
            col_type = "numerical"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_type = "datetime"
        elif pd.api.types.is_bool_dtype(df[col]):
            col_type = "boolean"
        else:
            col_type = "categorical"

        column_types[col_type].append(col)

        column_details.append(
            {
                "column_name": col,
                "data_type": dtype,
                "detected_type": col_type,
                "missing_count": col_missing,
                "missing_percentage": col_missing_pct,
                "unique_values": unique_vals,
            }
        )

    return {
        "summary": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "missing_cells": missing_cells,
            "missing_percentage": missing_percentage,
            "duplicate_rows": duplicate_rows,
            "memory_usage_mb": memory_usage_mb,
        },
        "type_counts": {
            "numerical": len(column_types["numerical"]),
            "categorical": len(column_types["categorical"]),
            "datetime": len(column_types["datetime"]),
            "boolean": len(column_types["boolean"]),
        },
        "columns": column_details,
    }
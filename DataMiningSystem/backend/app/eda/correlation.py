import numpy as np
import pandas as pd


def compute_correlation_matrix(df: pd.DataFrame) -> dict:
    num_df = df.select_dtypes(include=[np.number])

    if num_df.shape[1] < 2:
        return {
            "error": "Dataset requires at least 2 numerical columns for correlation matrix."
        }

    corr_matrix = num_df.corr(method="pearson").round(3)

    formatted_matrix = []
    columns = list(corr_matrix.columns)

    for i, col1 in enumerate(columns):
        for j, col2 in enumerate(columns):
            formatted_matrix.append(
                {
                    "x": col1,
                    "y": col2,
                    "value": (
                        float(corr_matrix.iloc[i, j])
                        if not np.isnan(corr_matrix.iloc[i, j])
                        else 0.0
                    ),
                }
            )

    return {"columns": columns, "matrix": formatted_matrix}
import os
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.eda.overview import compute_dataset_overview
from app.eda.univariate import compute_univariate_analysis
from app.eda.bivariate import compute_bivariate_analysis
from app.eda.correlation import compute_correlation_matrix

router = APIRouter(prefix="/api/v1/eda", tags=["Exploratory Data Analysis"])

UPLOAD_DIR = "./uploads"

def _load_dataset(dataset_id: str) -> pd.DataFrame:
    # Check cleaned file first, then reference uploaded file
    xlsx_path = os.path.join(UPLOAD_DIR, f"{dataset_id}.xlsx")
    csv_path = os.path.join(UPLOAD_DIR, f"{dataset_id}.csv")

    if os.path.exists(xlsx_path):
        return pd.read_excel(xlsx_path)
    elif os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

@router.get("/overview/{dataset_id}")
async def get_overview(dataset_id: str):
    df = _load_dataset(dataset_id)
    overview_data = compute_dataset_overview(df)
    return {
        "status": "SUCCESS",
        "dataset_id": dataset_id,
        "overview": overview_data
    }

@router.get("/univariate/{dataset_id}")
async def get_univariate(dataset_id: str, column: str):
    df = _load_dataset(dataset_id)
    univariate_data = compute_univariate_analysis(df, column=column)
    return {
        "status": "SUCCESS",
        "dataset_id": dataset_id,
        "univariate": univariate_data
    }

@router.get("/bivariate/{dataset_id}")
async def get_bivariate(dataset_id: str, col1: str, col2: str):
    df = _load_dataset(dataset_id)
    bivariate_data = compute_bivariate_analysis(df, col1=col1, col2=col2)
    return {
        "status": "SUCCESS",
        "dataset_id": dataset_id,
        "bivariate": bivariate_data,
    }


@router.get("/correlation/{dataset_id}")
async def get_correlation(dataset_id: str):
    df = _load_dataset(dataset_id)
    correlation_data = compute_correlation_matrix(df)
    return {
        "status": "SUCCESS",
        "dataset_id": dataset_id,
        "correlation": correlation_data,
    }
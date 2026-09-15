from fastapi import UploadFile, HTTPException
import pandas as pd
import io

from app.services.column_analyzer import analyze_columns
from app.services.cleaning_diagnostics import generate_cleaning_diagnosis
from app.services.cleaning_plan import generate_cleaning_plan

async def process_uploaded_file(file: UploadFile):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # 1. Non-destructive profiling
        semantic_results = analyze_columns(df)

        # 2. Quality diagnostics
        diagnosis_results = generate_cleaning_diagnosis(df, semantic_results)

        # 3. Generate actionable Cleaning Plan (Iteration 4 - Phase 1)
        cleaning_plan_items = generate_cleaning_plan(df, semantic_results)

        return {
            "filename": file.filename,
            "row_count": len(df),
            "column_count": len(df.columns),
            "semantic_analysis": semantic_results,
            "cleaning_diagnosis": diagnosis_results,
            "cleaning_plan": {
                "total_items": len(cleaning_plan_items),
                "items": cleaning_plan_items
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
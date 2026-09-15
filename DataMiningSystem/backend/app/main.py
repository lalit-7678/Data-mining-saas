import uuid
import os
import pandas as pd
import numpy as np
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# PDF Generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

app = FastAPI(title="Data Profiling & Quality Diagnostics Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

DATASETS_DB = {}

class CleanRequest(BaseModel):
    dataset_id: str
    approved_item_ids: List[str]

@app.post("/api/v1/data/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    dataset_id = f"dataset_{uuid.uuid4().hex[:8]}"
    file_path = os.path.join(UPLOAD_DIR, f"{dataset_id}.csv")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        df = pd.read_csv(file_path)
        DATASETS_DB[dataset_id] = df

        semantic_analysis = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing_cnt = int(df[col].isnull().sum())
            missing_pct = round((missing_cnt / len(df)) * 100, 2) if len(df) > 0 else 0
            unique_cnt = int(df[col].nunique())

            if "id" in col.lower() or unique_cnt == len(df):
                sem_type, role = "IDENTIFIER", "key"
            elif pd.api.types.is_numeric_dtype(df[col]):
                sem_type, role = "NUMERICAL", "metric"
            elif "date" in col.lower() or "time" in col.lower():
                sem_type, role = "DATETIME", "dimension"
            else:
                sem_type, role = "CATEGORICAL", "dimension"

            stats = None
            if pd.api.types.is_numeric_dtype(df[col]):
                stats = {
                    "mean": round(float(df[col].mean()), 2) if not df[col].isnull().all() else None,
                    "std": round(float(df[col].std()), 2) if not df[col].isnull().all() else None,
                    "min": round(float(df[col].min()), 2) if not df[col].isnull().all() else None,
                    "max": round(float(df[col].max()), 2) if not df[col].isnull().all() else None,
                }

            semantic_analysis.append({
                "name": col,
                "physical_type": dtype,
                "semantic_type": sem_type,
                "role": role,
                "missing_count": missing_cnt,
                "missing_pct": missing_pct,
                "unique_count": unique_cnt,
                "stats": stats
            })

        cleaning_items = []
        for idx, col in enumerate(df.columns):
            missing_cnt = int(df[col].isnull().sum())
            if missing_cnt > 0:
                cleaning_items.append({
                    "id": f"op_missing_{idx}",
                    "column": col,
                    "issue_type": "MISSING_VALUES",
                    "severity": "MEDIUM",
                    "proposed_action": "Impute missing data"
                })

        return {
            "dataset_id": dataset_id,
            "row_count": len(df),
            "column_count": len(df.columns),
            "semantic_analysis": semantic_analysis,
            "cleaning_plan": {"items": cleaning_items}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/eda/overview/{dataset_id}")
async def get_eda_overview(dataset_id: str):
    """Generates charts adhering strictly to the UBM (Overview -> Univariate -> Bivariate -> Multivariate) flow with dynamic color schemes."""
    if dataset_id not in DATASETS_DB:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = DATASETS_DB[dataset_id]
    chart_urls = []

    # Distinct Color Palettes
    palette_pie = ['#2563eb', '#7c3aed', '#db2777', '#059669']
    palette_univariate = sns.color_palette("muted")
    palette_bivariate = sns.color_palette("Set2")
    
    # Filter features based on meaningful cardinality
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.select_dtypes(include=['object', 'category']).columns if df[c].nunique() < 20 and df[c].nunique() > 1]

    # --- 0. OVERVIEW: Pie Chart (Data Type Composition) ---
    plt.figure(figsize=(6, 4))
    type_counts = {
        'Numerical': len(num_cols),
        'Categorical': len(cat_cols),
        'Other/Identifiers': len(df.columns) - (len(num_cols) + len(cat_cols))
    }
    type_counts = {k: v for k, v in type_counts.items() if v > 0}
    
    plt.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%', colors=palette_pie, startangle=140)
    plt.title("Dataset Overview: Column Type Split", fontsize=12, fontweight='bold')
    filename = f"{dataset_id}_chart_1.png"
    plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
    plt.close()
    chart_urls.append(f"/static/{filename}")

    # --- 1. UNIVARIATE ANALYSIS ---
    # Top Numerical Distributions
    for i, col in enumerate(num_cols[:3]):
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True, color=palette_univariate[i % len(palette_univariate)])
        plt.title(f"Univariate: Distribution of '{col}'", fontsize=11, fontweight='bold')
        filename = f"{dataset_id}_chart_{len(chart_urls)+1}.png"
        plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
        plt.close()
        chart_urls.append(f"/static/{filename}")

    # Top Categorical Distributions
    for i, col in enumerate(cat_cols[:3]):
        plt.figure(figsize=(6, 4))
        order = df[col].value_counts().head(8).index
        sns.countplot(data=df, y=col, order=order, palette="deep")
        plt.title(f"Univariate: Top Categories in '{col}'", fontsize=11, fontweight='bold')
        filename = f"{dataset_id}_chart_{len(chart_urls)+1}.png"
        plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
        plt.close()
        chart_urls.append(f"/static/{filename}")

    # --- 2. BIVARIATE ANALYSIS ---
    # Scatter Plots
    if len(num_cols) >= 2:
        for i in range(min(3, len(num_cols) - 1)):
            plt.figure(figsize=(6, 4))
            sns.scatterplot(data=df, x=num_cols[i], y=num_cols[i+1], color=palette_bivariate[i % len(palette_bivariate)])
            plt.title(f"Bivariate: {num_cols[i]} vs {num_cols[i+1]}", fontsize=11, fontweight='bold')
            filename = f"{dataset_id}_chart_{len(chart_urls)+1}.png"
            plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
            plt.close()
            chart_urls.append(f"/static/{filename}")

    # Boxplots (Categorical vs Numerical)
    if len(cat_cols) > 0 and len(num_cols) > 0:
        for i in range(min(3, len(num_cols))):
            plt.figure(figsize=(6, 4))
            top_cats = df[cat_cols[0]].value_counts().head(5).index
            sub_df = df[df[cat_cols[0]].isin(top_cats)]
            sns.boxplot(data=sub_df, x=cat_cols[0], y=num_cols[i], palette="Accent")
            plt.title(f"Bivariate Spread: {cat_cols[0]} vs {num_cols[i]}", fontsize=11, fontweight='bold')
            plt.xticks(rotation=25)
            filename = f"{dataset_id}_chart_{len(chart_urls)+1}.png"
            plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
            plt.close()
            chart_urls.append(f"/static/{filename}")

    # --- 3. MULTIVARIATE ANALYSIS ---
    if len(num_cols) >= 2 and len(cat_cols) > 0:
        top_cats = df[cat_cols[0]].value_counts().head(4).index
        sub_df = df[df[cat_cols[0]].isin(top_cats)]

        for i in range(min(2, len(num_cols) - 1)):
            plt.figure(figsize=(6, 4))
            sns.scatterplot(data=sub_df, x=num_cols[i], y=num_cols[i+1], hue=cat_cols[0], palette="viridis")
            plt.title(f"Multivariate: {num_cols[i]} vs {num_cols[i+1]} by {cat_cols[0]}", fontsize=10, fontweight='bold')
            filename = f"{dataset_id}_chart_{len(chart_urls)+1}.png"
            plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
            plt.close()
            chart_urls.append(f"/static/{filename}")

    # Correlation Heatmap
    if len(num_cols) > 1:
        plt.figure(figsize=(7, 5))
        corr = df[num_cols].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', linewidths=0.5)
        plt.title("Multivariate Correlation Heatmap", fontsize=11, fontweight='bold')
        filename = f"{dataset_id}_chart_heatmap.png"
        plt.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
        plt.close()
        chart_urls.append(f"/static/{filename}")

    # Pairplot Matrix
    if len(num_cols) >= 2:
        sample_df = df[num_cols[:4]].dropna().sample(min(400, len(df)))
        pairplot_grid = sns.pairplot(sample_df, corner=True, palette="husl")
        pairplot_grid.fig.suptitle("Multivariate Feature Matrix", y=1.02, fontsize=12)
        filename = f"{dataset_id}_chart_pairplot.png"
        pairplot_grid.savefig(os.path.join(UPLOAD_DIR, filename), bbox_inches='tight', dpi=150)
        plt.close()
        chart_urls.append(f"/static/{filename}")

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0

    return {
        "status": "SUCCESS",
        "overview": {
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "missing_pct": missing_pct,
            "quality_score": max(0, int(100 - missing_pct)),
            "charts": chart_urls
        }
    }


@app.get("/api/v1/eda/insights/{dataset_id}")
async def get_eda_insights(dataset_id: str):
    """Generates statistical insights for the frontend."""
    if dataset_id not in DATASETS_DB:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = DATASETS_DB[dataset_id]
    insights = []

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isnull().sum().sum())
    if missing_cells > 0:
        missing_pct = round((missing_cells / total_cells) * 100, 2)
        insights.append({
            "title": "Missing Data Detected",
            "severity": "MEDIUM",
            "interpretation": f"Dataset contains {missing_cells} missing values across features.",
            "evidence": f"{missing_pct}% of total cells are null."
        })

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        corr_matrix = df[num_cols].corr().abs()
        np.fill_diagonal(corr_matrix.values, 0)
        max_corr = corr_matrix.max().max()
        if max_corr > 0.7:
            pair = corr_matrix.stack().idxmax()
            insights.append({
                "title": "Strong Multi-Collinearity Risk",
                "severity": "HIGH",
                "interpretation": f"High correlation found between '{pair[0]}' and '{pair[1]}'.",
                "evidence": f"Pearson Correlation Coefficient = {round(max_corr, 2)}"
            })

    if not insights:
        insights.append({
            "title": "Optimal Structural Integrity",
            "severity": "LOW",
            "interpretation": "No severe missingness or extreme anomalies detected across primary features.",
            "evidence": "Data readiness level meets core analytical standards."
        })

    return {"status": "SUCCESS", "insights": insights}

@app.post("/api/v1/data/clean")
async def apply_cleaning(request: CleanRequest):
    """Executes data cleaning and produces properly auto-formatted XLSX dataset export."""
    if request.dataset_id not in DATASETS_DB:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = DATASETS_DB[request.dataset_id].copy()

    # Impute missing values
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                mode_val = df[col].mode()
                fill_val = mode_val[0] if not mode_val.empty else "Unknown"
                df[col] = df[col].fillna(fill_val)

    cleaned_dataset_id = f"dataset_cleaned_{uuid.uuid4().hex[:8]}"
    export_filename = f"{cleaned_dataset_id}.xlsx"
    export_path = os.path.join(UPLOAD_DIR, export_filename)

    try:
        # Save using openpyxl and adjust column widths automatically
        with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Cleaned Data")
            worksheet = writer.sheets["Cleaned Data"]

            # Calculate maximum length for each column and adjust width
            for col in worksheet.columns:
                max_len = 0
                col_letter = col[0].column_letter  # Get Excel column letter (A, B, C, etc.)
                for cell in col:
                    if cell.value is not None:
                        # Find the longest value string
                        val_str = str(cell.value)
                        if len(val_str) > max_len:
                            max_len = len(val_str)
                # Apply padding so text isn't cramped
                worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    except Exception as e:
        # Fallback to CSV if Excel formatting fails
        export_filename = f"{cleaned_dataset_id}.csv"
        export_path = os.path.join(UPLOAD_DIR, export_filename)
        df.to_csv(export_path, index=False)

    DATASETS_DB[cleaned_dataset_id] = df

    return {
        "status": "SUCCESS",
        "cleaned_dataset_id": cleaned_dataset_id,
        "download_url": f"/static/{export_filename}"
    }

@app.get("/api/v1/eda/export-pdf/{dataset_id}")
async def export_eda_pdf(dataset_id: str):
    """Compiles generated EDA charts into a PDF report using valid ReportLab styles."""
    if dataset_id not in DATASETS_DB:
        raise HTTPException(status_code=404, detail="Dataset not found")

    pdf_filename = f"EDA_Report_{dataset_id}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Exploratory Data Analysis Report", styles['Title']))
    story.append(Paragraph(f"Dataset ID: {dataset_id}", styles['Normal']))
    story.append(Spacer(1, 15))

    for i in range(1, 25):
        img_path = os.path.join(UPLOAD_DIR, f"{dataset_id}_chart_{i}.png")
        if os.path.exists(img_path):
            story.append(Image(img_path, width=450, height=300))
            story.append(Spacer(1, 15))

    for special_chart in ["heatmap", "pairplot"]:
        img_path = os.path.join(UPLOAD_DIR, f"{dataset_id}_chart_{special_chart}.png")
        if os.path.exists(img_path):
            story.append(Image(img_path, width=450, height=300))
            story.append(Spacer(1, 15))

    doc.build(story)

    return {
        "status": "SUCCESS",
        "download_url": f"/static/{pdf_filename}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
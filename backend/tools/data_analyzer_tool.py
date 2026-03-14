import pandas as pd
import numpy as np
import json
import os
from typing import Optional


def analyze_dataframe(df: pd.DataFrame, filename: str = "dataset") -> str:
    result = []
    result.append(f"=== AUTO EDA REPORT: {filename} ===\n")

    result.append(f"DATASET OVERVIEW:")
    result.append(f"  Rows: {len(df)}")
    result.append(f"  Columns: {len(df.columns)}")
    result.append(f"  Total cells: {len(df) * len(df.columns)}")
    result.append(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB\n")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    result.append(f"COLUMN TYPES:")
    result.append(f"  Numeric: {numeric_cols}")
    result.append(f"  Categorical: {categorical_cols}")
    result.append(f"  Datetime: {datetime_cols}\n")

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
    missing_df = missing_df[missing_df["missing_count"] > 0]

    if len(missing_df) > 0:
        result.append(f"MISSING VALUES:")
        for col in missing_df.index:
            result.append(f"  {col}: {missing_df.loc[col, 'missing_count']} ({missing_df.loc[col, 'missing_pct']}%)")
        result.append("")
    else:
        result.append("MISSING VALUES: None found\n")

    if numeric_cols:
        result.append(f"NUMERIC STATISTICS:")
        stats = df[numeric_cols].describe().round(3)
        result.append(stats.to_string())
        result.append("")

    if categorical_cols:
        result.append(f"CATEGORICAL COLUMNS:")
        for col in categorical_cols[:5]:
            unique_count = df[col].nunique()
            top_values = df[col].value_counts().head(5)
            result.append(f"  {col}: {unique_count} unique values")
            result.append(f"    Top values: {top_values.to_dict()}")
        result.append("")

    if len(numeric_cols) > 1:
        result.append(f"TOP CORRELATIONS:")
        corr_matrix = df[numeric_cols].corr()
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                if not np.isnan(corr_val):
                    corr_pairs.append((col1, col2, corr_val))
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        for col1, col2, corr_val in corr_pairs[:5]:
            strength = "strong" if abs(corr_val) > 0.7 else "moderate" if abs(corr_val) > 0.4 else "weak"
            direction = "positive" if corr_val > 0 else "negative"
            result.append(f"  {col1} vs {col2}: {corr_val:.3f} ({strength} {direction})")
        result.append("")

    duplicates = df.duplicated().sum()
    result.append(f"DUPLICATE ROWS: {duplicates}")

    if numeric_cols:
        result.append(f"\nOUTLIERS (IQR method):")
        for col in numeric_cols[:5]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                result.append(f"  {col}: {len(outliers)} outliers detected")

    result.append(f"\nANALYSIS SUGGESTIONS:")
    if len(missing_df) > 0:
        result.append("  - Handle missing values")
    if duplicates > 0:
        result.append("  - Remove duplicate rows")
    if len(numeric_cols) > 1:
        result.append("  - Explore correlations between numeric features")
    if categorical_cols:
        result.append("  - Encode categorical variables for ML models")

    return "\n".join(result)


def analyze_file(file_path: str) -> str:
    try:
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            return f"Data analyzer supports CSV, Excel, and JSON files. Got: {ext}"
        return analyze_dataframe(df, filename)
    except Exception as e:
        return f"Analysis error: {str(e)}"


def safe_float(v):
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return 0.0
        return round(f, 2)
    except:
        return 0.0


def generate_chart_data(file_path: str) -> dict:
    """
    Generate ALL chart types from CSV/Excel.
    Returns bar, line, pie, histogram, scatter, area, radar, heatmap charts.
    """
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            return {"error": "Only CSV and Excel supported for charts", "success": False}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        charts = []

        # 1. BAR CHART
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            grouped = df.groupby(cat_col)[num_col].mean().head(10)
            charts.append({
                "type": "bar",
                "title": f"Average {num_col} by {cat_col}",
                "labels": [str(x) for x in grouped.index.tolist()],
                "data": [safe_float(v) for v in grouped.values],
                "color": "#4f46e5"
            })

        # 2. LINE CHART
        if numeric_cols:
            charts.append({
                "type": "line",
                "title": f"Trend: {numeric_cols[0]} over records",
                "labels": [str(i) for i in range(min(50, len(df)))],
                "data": [safe_float(v) for v in df[numeric_cols[0]].head(50).tolist()],
                "color": "#10b981"
            })

        # 3. PIE CHART
        if categorical_cols:
            cat_col = categorical_cols[0]
            counts = df[cat_col].value_counts().head(8)
            charts.append({
                "type": "pie",
                "title": f"Distribution of {cat_col}",
                "labels": [str(x) for x in counts.index.tolist()],
                "data": [int(v) for v in counts.values.tolist()],
                "colors": ["#4f46e5","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899","#f97316"]
            })

        # 4. HISTOGRAM
        if numeric_cols:
            col = numeric_cols[0]
            clean_data = df[col].dropna()
            hist_values, bin_edges = np.histogram(clean_data, bins=10)
            bin_labels = [f"{bin_edges[i]:.1f}" for i in range(len(bin_edges)-1)]
            charts.append({
                "type": "histogram",
                "title": f"Frequency Distribution of {col}",
                "labels": bin_labels,
                "data": [int(v) for v in hist_values.tolist()],
                "color": "#f59e0b"
            })

        # 5. AREA CHART
        if len(numeric_cols) >= 2:
            charts.append({
                "type": "area",
                "title": f"Area: {numeric_cols[0]} & {numeric_cols[1]}",
                "labels": [str(i) for i in range(min(40, len(df)))],
                "data": [safe_float(v) for v in df[numeric_cols[0]].head(40).tolist()],
                "data2": [safe_float(v) for v in df[numeric_cols[1]].head(40).tolist()],
                "color": "#06b6d4",
                "color2": "#8b5cf6",
                "key1": numeric_cols[0],
                "key2": numeric_cols[1]
            })

        # 6. SCATTER CHART
        if len(numeric_cols) >= 2:
            sample = df[[numeric_cols[0], numeric_cols[1]]].dropna().head(80)
            charts.append({
                "type": "scatter",
                "title": f"Scatter: {numeric_cols[0]} vs {numeric_cols[1]}",
                "data": [
                    {"x": safe_float(row[numeric_cols[0]]), "y": safe_float(row[numeric_cols[1]])}
                    for _, row in sample.iterrows()
                ],
                "xKey": numeric_cols[0],
                "yKey": numeric_cols[1],
                "color": "#ec4899"
            })

        # 7. MULTI-BAR CHART (grouped)
        if categorical_cols and len(numeric_cols) >= 2:
            cat_col = categorical_cols[0]
            grouped = df.groupby(cat_col)[numeric_cols[:3]].mean().head(8)
            charts.append({
                "type": "multibar",
                "title": f"Comparison: Multiple Metrics by {cat_col}",
                "labels": [str(x) for x in grouped.index.tolist()],
                "series": [
                    {
                        "name": col,
                        "data": [safe_float(v) for v in grouped[col].tolist()],
                        "color": ["#4f46e5","#10b981","#f59e0b"][i]
                    }
                    for i, col in enumerate(numeric_cols[:3])
                ]
            })

        # 8. HEATMAP (correlation matrix)
        if len(numeric_cols) >= 3:
            corr = df[numeric_cols[:6]].corr().round(2)
            heatmap_data = []
            for i, row_name in enumerate(corr.index):
                for j, col_name in enumerate(corr.columns):
                    val = corr.iloc[i, j]
                    heatmap_data.append({
                        "x": col_name,
                        "y": row_name,
                        "value": safe_float(val)
                    })
            charts.append({
                "type": "heatmap",
                "title": "Correlation Heatmap",
                "labels": numeric_cols[:6],
                "data": heatmap_data
            })

        # 9. DONUT CHART
        if categorical_cols:
            cat_col = categorical_cols[0]
            counts = df[cat_col].value_counts().head(6)
            charts.append({
                "type": "donut",
                "title": f"Donut: {cat_col} Share",
                "labels": [str(x) for x in counts.index.tolist()],
                "data": [int(v) for v in counts.values.tolist()],
                "colors": ["#4f46e5","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6"]
            })

        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_cols": numeric_cols,
            "categorical_cols": categorical_cols,
        }

        return {
            "success": True,
            "charts": charts,
            "summary": summary,
            "filename": os.path.basename(file_path)
        }

    except Exception as e:
        return {"error": str(e), "success": False}


def run_data_analyzer_tool(input: str) -> str:
    from tools.file_reader_tool import _uploaded_files

    input = input.strip()

    if input in _uploaded_files:
        file_info = _uploaded_files[input]
        return analyze_file(file_info["path"])

    for file_id, info in _uploaded_files.items():
        if info["name"].lower() == input.lower():
            return analyze_file(info["path"])

    if os.path.exists(input):
        return analyze_file(input)

    for file_id, info in _uploaded_files.items():
        ext = info.get("extension", "")
        if ext in [".csv", ".xlsx", ".xls", ".json"]:
            return analyze_file(info["path"])

    return "No data file found. Please upload a CSV or Excel file first."
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json
import os
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

CODER_AGENT_PROMPT = """You are an expert Python Data Scientist (Coder Agent).
You will receive a dataset description and must write Python EDA code.

RULES:
1. Use only: pandas (as df), numpy (as np), already imported
2. DO NOT import anything — imports are already done
3. Write code that prints statistics and findings
4. Use print() for ALL outputs
5. Code must be executable as-is
6. Focus on: shape, dtypes, describe, missing values, correlations, value counts
7. Return ONLY executable Python code — no markdown, no backticks

The dataframe is already loaded as 'df'. Write code to analyze it."""

ANALYST_AGENT_PROMPT = """You are an expert Data Analyst (Analyst Agent).
You receive raw EDA statistics output and explain it clearly.

RULES:
1. Explain findings in simple, clear English
2. Identify key patterns, anomalies, trends
3. Suggest ML preprocessing steps
4. Use bullet points and sections
5. Be specific — mention actual column names and numbers
6. End with: Top 3 recommendations for this dataset

Format your response with these sections:
## 📊 Dataset Overview
## 🔍 Key Findings
## ⚠️ Data Quality Issues
## 🤖 ML Preprocessing Suggestions
## ✅ Top 3 Recommendations"""


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
        max_tokens=2048
    )


def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight',
                facecolor='#0f0f0f', edgecolor='none', dpi=100)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    buf.close()
    return img_base64


def set_dark_style():
    """Set dark theme for all charts."""
    plt.style.use('dark_background')
    sns.set_theme(style="darkgrid", palette="husl")


def generate_distribution_charts(df: pd.DataFrame) -> List[Dict]:
    """Generate distribution plots for all numeric columns."""
    charts = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols[:6]:
        try:
            set_dark_style()
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            fig.patch.set_facecolor('#0f0f0f')

            # Histogram
            axes[0].hist(df[col].dropna(), bins=30, color='#6366f1',
                        alpha=0.8, edgecolor='#4338ca')
            axes[0].set_title(f'Distribution: {col}', color='white', fontsize=12)
            axes[0].set_xlabel(col, color='#888')
            axes[0].set_ylabel('Frequency', color='#888')
            axes[0].tick_params(colors='#888')
            axes[0].set_facecolor('#1a1a2e')

            # Box plot
            axes[1].boxplot(df[col].dropna(), patch_artist=True,
                           boxprops=dict(facecolor='#6366f1', color='#a5b4fc'),
                           whiskerprops=dict(color='#a5b4fc'),
                           capprops=dict(color='#a5b4fc'),
                           medianprops=dict(color='#10b981', linewidth=2))
            axes[1].set_title(f'Boxplot: {col}', color='white', fontsize=12)
            axes[1].set_facecolor('#1a1a2e')
            axes[1].tick_params(colors='#888')

            plt.tight_layout()
            charts.append({
                "type": "distribution",
                "title": f"Distribution & Boxplot: {col}",
                "column": col,
                "image": fig_to_base64(fig)
            })
        except Exception as e:
            continue

    return charts


def generate_correlation_heatmap(df: pd.DataFrame) -> Dict:
    """Generate correlation heatmap."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return None

    try:
        set_dark_style()
        corr = df[numeric_cols].corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#0f0f0f')
        ax.set_facecolor('#0f0f0f')

        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f',
                   cmap='coolwarm', ax=ax,
                   linewidths=0.5, linecolor='#222',
                   annot_kws={"size": 9, "color": "white"},
                   cbar_kws={"shrink": 0.8})

        ax.set_title('Correlation Heatmap', color='white',
                    fontsize=14, pad=15)
        ax.tick_params(colors='#aaa', labelsize=9)
        plt.tight_layout()

        return {
            "type": "heatmap",
            "title": "Correlation Heatmap",
            "image": fig_to_base64(fig)
        }
    except Exception:
        return None


def generate_missing_values_chart(df: pd.DataFrame) -> Dict:
    """Generate missing values bar chart."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if len(missing) == 0:
        return None

    try:
        set_dark_style()
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#0f0f0f')
        ax.set_facecolor('#1a1a2e')

        colors = ['#ef4444' if v > df.shape[0] * 0.3 else '#f59e0b'
                 for v in missing.values]
        bars = ax.bar(missing.index, missing.values, color=colors,
                     edgecolor='#222', linewidth=0.5)

        for bar, val in zip(bars, missing.values):
            pct = val / len(df) * 100
            ax.text(bar.get_x() + bar.get_width() / 2,
                   bar.get_height() + 0.5,
                   f'{pct:.1f}%', ha='center', va='bottom',
                   color='white', fontsize=9)

        ax.set_title('Missing Values by Column', color='white', fontsize=14)
        ax.set_xlabel('Columns', color='#888')
        ax.set_ylabel('Missing Count', color='#888')
        ax.tick_params(colors='#888', rotation=45)
        plt.tight_layout()

        return {
            "type": "missing_values",
            "title": "Missing Values Analysis",
            "image": fig_to_base64(fig)
        }
    except Exception:
        return None


def generate_categorical_charts(df: pd.DataFrame) -> List[Dict]:
    """Generate value count charts for categorical columns."""
    charts = []
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    for col in cat_cols[:4]:
        try:
            value_counts = df[col].value_counts().head(10)
            set_dark_style()
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#0f0f0f')
            ax.set_facecolor('#1a1a2e')

            colors = plt.cm.Set3(np.linspace(0, 1, len(value_counts)))
            bars = ax.barh(value_counts.index.astype(str),
                          value_counts.values, color=colors)

            for bar, val in zip(bars, value_counts.values):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                       str(val), va='center', color='white', fontsize=9)

            ax.set_title(f'Value Counts: {col}', color='white', fontsize=13)
            ax.set_xlabel('Count', color='#888')
            ax.tick_params(colors='#888')
            plt.tight_layout()

            charts.append({
                "type": "categorical",
                "title": f"Value Counts: {col}",
                "column": col,
                "image": fig_to_base64(fig)
            })
        except Exception:
            continue

    return charts


def generate_pairplot(df: pd.DataFrame) -> Dict:
    """Generate pairplot for top numeric columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return None

    try:
        cols_to_plot = numeric_cols[:4]
        set_dark_style()

        pair_df = df[cols_to_plot].dropna()
        if len(pair_df) > 1000:
            pair_df = pair_df.sample(1000, random_state=42)

        fig, axes = plt.subplots(
            len(cols_to_plot), len(cols_to_plot),
            figsize=(12, 10)
        )
        fig.patch.set_facecolor('#0f0f0f')
        fig.suptitle('Pairplot (Sample)', color='white', fontsize=14, y=1.02)

        for i, col1 in enumerate(cols_to_plot):
            for j, col2 in enumerate(cols_to_plot):
                ax = axes[i][j]
                ax.set_facecolor('#1a1a2e')
                if i == j:
                    ax.hist(pair_df[col1].dropna(), bins=20,
                           color='#6366f1', alpha=0.8)
                else:
                    ax.scatter(pair_df[col2], pair_df[col1],
                              alpha=0.3, s=8, color='#10b981')
                if i == len(cols_to_plot) - 1:
                    ax.set_xlabel(col2, color='#888', fontsize=8)
                if j == 0:
                    ax.set_ylabel(col1, color='#888', fontsize=8)
                ax.tick_params(colors='#555', labelsize=7)

        plt.tight_layout()
        return {
            "type": "pairplot",
            "title": "Feature Pairplot",
            "image": fig_to_base64(fig)
        }
    except Exception:
        return None


def run_coder_agent(df: pd.DataFrame) -> str:
    """Coder Agent: generates and executes EDA code."""
    llm = get_llm()

    dataset_info = f"""
Dataset shape: {df.shape}
Columns: {df.columns.tolist()}
Data types:
{df.dtypes.to_string()}

First 3 rows:
{df.head(3).to_string()}

Basic stats:
{df.describe().to_string()}
"""

    messages = [
        SystemMessage(content=CODER_AGENT_PROMPT),
        HumanMessage(content=f"Dataset info:\n{dataset_info}\n\nWrite Python EDA code:")
    ]

    response = llm.invoke(messages)
    code = response.content.strip()

    # Clean code
    code = code.replace('```python', '').replace('```', '').strip()

    # Execute code safely
    output_lines = []
    import sys
    import io as _io

    old_stdout = sys.stdout
    sys.stdout = _io.StringIO()

    try:
        exec(code, {
            'df': df.copy(),
            'pd': pd,
            'np': np,
            'print': print
        })
        output = sys.stdout.getvalue()
    except Exception as e:
        output = f"Code execution note: {str(e)}\n"
        # Fallback basic stats
        sys.stdout = old_stdout
        basic = []
        basic.append(f"Shape: {df.shape}")
        basic.append(f"Columns: {df.columns.tolist()}")
        basic.append(f"Missing values:\n{df.isnull().sum().to_string()}")
        basic.append(f"Stats:\n{df.describe().to_string()}")
        output = "\n".join(basic)
    finally:
        sys.stdout = old_stdout

    return output


def run_analyst_agent(stats_output: str, df_info: str) -> str:
    """Analyst Agent: explains the EDA findings."""
    llm = get_llm()

    messages = [
        SystemMessage(content=ANALYST_AGENT_PROMPT),
        HumanMessage(content=f"""
Dataset Info:
{df_info}

EDA Statistics Output:
{stats_output[:3000]}

Now provide your expert analysis:""")
    ]

    response = llm.invoke(messages)
    return response.content.strip()


def run_full_eda(file_path: str) -> Dict[str, Any]:
    """
    Run complete EDA pipeline on uploaded file.
    Returns charts, stats, and AI insights.
    """
    try:
        # Load file
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            return {"success": False, "error": f"Unsupported format: {ext}"}

        # Dataset info
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)

        df_info = f"""
Rows: {len(df)} | Columns: {len(df.columns)}
Numeric columns ({len(numeric_cols)}): {numeric_cols}
Categorical columns ({len(cat_cols)}): {cat_cols}
Missing values: {missing[missing > 0].to_dict()}
Duplicates: {df.duplicated().sum()}
"""

        # Generate all charts
        charts = []

        dist_charts = generate_distribution_charts(df)
        charts.extend(dist_charts)

        heatmap = generate_correlation_heatmap(df)
        if heatmap:
            charts.append(heatmap)

        missing_chart = generate_missing_values_chart(df)
        if missing_chart:
            charts.append(missing_chart)

        cat_charts = generate_categorical_charts(df)
        charts.extend(cat_charts)

        pairplot = generate_pairplot(df)
        if pairplot:
            charts.append(pairplot)

        # Run Coder Agent
        stats_output = run_coder_agent(df)

        # Run Analyst Agent
        ai_insights = run_analyst_agent(stats_output, df_info)

        # Summary stats
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_cols": numeric_cols,
            "categorical_cols": cat_cols,
            "missing_values": missing[missing > 0].to_dict(),
            "missing_pct": missing_pct[missing_pct > 0].to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1)
        }

        # Generate downloadable report
        report = generate_text_report(df, stats_output, ai_insights, summary)

        return {
            "success": True,
            "summary": summary,
            "charts": charts,
            "stats_output": stats_output,
            "ai_insights": ai_insights,
            "report": report,
            "df_info": df_info
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_text_report(df, stats_output, ai_insights, summary) -> str:
    """Generate downloadable EDA report."""
    lines = []
    lines.append("=" * 60)
    lines.append("NEXUS AGENT — AGENTIC AI EDA REPORT")
    lines.append("=" * 60)
    lines.append(f"\nRows: {summary['rows']} | Columns: {summary['columns']}")
    lines.append(f"Numeric columns: {summary['numeric_cols']}")
    lines.append(f"Categorical columns: {summary['categorical_cols']}")
    lines.append(f"Missing values: {summary['missing_values']}")
    lines.append(f"Duplicate rows: {summary['duplicates']}")
    lines.append(f"Memory usage: {summary['memory_kb']} KB")
    lines.append("\n" + "=" * 60)
    lines.append("CODER AGENT OUTPUT (Statistics):")
    lines.append("=" * 60)
    lines.append(stats_output)
    lines.append("\n" + "=" * 60)
    lines.append("ANALYST AGENT INSIGHTS:")
    lines.append("=" * 60)
    lines.append(ai_insights)
    lines.append("\n" + "=" * 60)
    lines.append("Generated by NEXUS AGENT — NeuraX 2.0 Hackathon")
    lines.append("=" * 60)
    return "\n".join(lines)


def analyze_dataframe(df: pd.DataFrame, filename: str = "dataset") -> str:
    """Legacy function — kept for compatibility."""
    result = []
    result.append(f"=== AUTO EDA REPORT: {filename} ===\n")
    result.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        result.append(f"\nNumeric Stats:\n{df[numeric_cols].describe().to_string()}")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        result.append(f"\nMissing Values:\n{missing.to_string()}")
    return "\n".join(result)


def analyze_file(file_path: str) -> str:
    """Legacy function — kept for compatibility."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            return f"Unsupported: {ext}"
        return analyze_dataframe(df, os.path.basename(file_path))
    except Exception as e:
        return f"Error: {str(e)}"


def generate_chart_data(file_path: str) -> dict:
    """Legacy function — kept for compatibility."""
    return {"success": False, "message": "Use /eda endpoint instead"}


def run_data_analyzer_tool(input: str) -> str:
    """Tool function called by agent."""
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

    return "No data file found. Please upload a CSV, Excel, or JSON file first."
import os
import pandas as pd
import json
from typing import Optional
import pymupdf
from docx import Document
from PIL import Image
from bs4 import BeautifulSoup
import requests


# Store uploaded file paths in memory
_uploaded_files: dict = {}


def register_file(file_id: str, file_path: str, original_name: str):
    """Register an uploaded file for the agent to access."""
    _uploaded_files[file_id] = {
        "path": file_path,
        "name": original_name,
        "extension": os.path.splitext(original_name)[1].lower()
    }


def get_registered_files() -> dict:
    return _uploaded_files


def read_file(file_path: str, original_name: str = "") -> str:
    """
    Universal file reader — detects file type and extracts text.
    Supports: PDF, DOCX, CSV, XLSX, JSON, TXT, PNG, JPG, HTML
    """
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if not ext and original_name:
            ext = os.path.splitext(original_name)[1].lower()

        if ext == ".pdf":
            return read_pdf(file_path)
        elif ext == ".docx":
            return read_docx(file_path)
        elif ext in [".csv"]:
            return read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            return read_excel(file_path)
        elif ext == ".json":
            return read_json(file_path)
        elif ext in [".txt", ".md", ".py", ".js", ".ts", ".html", ".css"]:
            return read_text(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
            return read_image(file_path)
        else:
            return read_text(file_path)

    except Exception as e:
        return f"Error reading file: {str(e)}"


def read_pdf(file_path: str) -> str:
    try:
        doc = pymupdf.open(file_path)
        text_parts = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num} ---\n{text}")
        doc.close()
        if not text_parts:
            return "PDF appears to be empty or contains only images."
        full_text = "\n\n".join(text_parts)
        if len(full_text) > 5000:
            return full_text[:5000] + f"\n\n[Truncated — {len(full_text)} total characters]"
        return full_text
    except Exception as e:
        return f"PDF read error: {str(e)}"


def read_docx(file_path: str) -> str:
    try:
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        if len(text) > 5000:
            return text[:5000] + f"\n\n[Truncated — {len(text)} total characters]"
        return text
    except Exception as e:
        return f"DOCX read error: {str(e)}"


def read_csv(file_path: str) -> str:
    try:
        df = pd.read_csv(file_path)
        result = f"CSV File Summary:\n"
        result += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
        result += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        result += f"First 10 rows:\n{df.head(10).to_string()}\n\n"
        result += f"Data Types:\n{df.dtypes.to_string()}\n\n"
        null_counts = df.isnull().sum()
        if null_counts.any():
            result += f"Missing Values:\n{null_counts[null_counts > 0].to_string()}"
        return result
    except Exception as e:
        return f"CSV read error: {str(e)}"


def read_excel(file_path: str) -> str:
    try:
        df = pd.read_excel(file_path)
        result = f"Excel File Summary:\n"
        result += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
        result += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        result += f"First 10 rows:\n{df.head(10).to_string()}"
        return result
    except Exception as e:
        return f"Excel read error: {str(e)}"


def read_json(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = json.dumps(data, indent=2)
        if len(text) > 5000:
            return text[:5000] + "\n[Truncated]"
        return text
    except Exception as e:
        return f"JSON read error: {str(e)}"


def read_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if len(text) > 5000:
            return text[:5000] + "\n[Truncated]"
        return text
    except Exception as e:
        return f"Text read error: {str(e)}"


def read_image(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        return f"Image loaded: {img.size[0]}x{img.size[1]} pixels. (OCR not available in cloud deployment)"
    except Exception as e:
        return f"Image read error: {str(e)}"


def read_url(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if len(l.strip()) > 30]
        text = "\n".join(lines[:100])
        if len(text) > 5000:
            return text[:5000] + "\n[Truncated]"
        return text
    except Exception as e:
        return f"URL read error: {str(e)}"


def run_file_reader_tool(input: str) -> str:
    """
    Main entry point. Input can be a file_id or file path.
    """
    input = input.strip()

    # Check if it's a URL
    if input.startswith("http://") or input.startswith("https://"):
        return read_url(input)

    # Check registered files
    if input in _uploaded_files:
        file_info = _uploaded_files[input]
        return read_file(file_info["path"], file_info["name"])

    # Check if it's a direct path
    if os.path.exists(input):
        return read_file(input)

    # Try to find by name
    for file_id, info in _uploaded_files.items():
        if info["name"].lower() == input.lower():
            return read_file(info["path"], info["name"])

    return f"File not found: '{input}'. Available files: {list(_uploaded_files.keys())}"
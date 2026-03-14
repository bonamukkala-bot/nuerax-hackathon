import os
import pandas as pd
import json
from typing import Optional
import pymupdf
from docx import Document
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import requests

# Set Tesseract path explicitly for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Store uploaded file paths in memory
_uploaded_files: dict = {}


def register_file(file_id: str, file_path: str, original_name: str):
    """Register an uploaded file for the agent to access."""
    _uploaded_files[file_id] = {
        "path": file_path,
        "name": original_name,
        "extension": os.path.splitext(original_name)[1].lower()
    }
    # Also register by filename for easy lookup
    _uploaded_files[original_name] = {
        "path": file_path,
        "name": original_name,
        "extension": os.path.splitext(original_name)[1].lower()
    }


def get_registered_files() -> dict:
    return _uploaded_files


def get_latest_file() -> Optional[dict]:
    """Get the most recently uploaded file."""
    files = {k: v for k, v in _uploaded_files.items()
             if len(k) == 8 and not os.path.splitext(k)[1]}
    if not files:
        return None
    return list(files.values())[-1]


def read_file(file_path: str, original_name: str = "") -> str:
    """
    Universal file reader — detects file type and extracts text/content.
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
    """
    Read image — extract text via OCR and describe contents.
    """
    try:
        img = Image.open(file_path)
        width, height = img.size
        mode = img.mode

        result = f"Image Information:\n"
        result += f"  Size: {width}x{height} pixels\n"
        result += f"  Mode: {mode}\n"
        result += f"  Format: {img.format or 'Unknown'}\n\n"

        # Try OCR to extract text
        try:
            text = pytesseract.image_to_string(img)
            if text.strip():
                result += f"Text extracted from image (OCR):\n{text.strip()}\n"
            else:
                result += "No text detected in image via OCR.\n"
                result += "This appears to be a photo or diagram without readable text.\n"
        except Exception as ocr_err:
            result += f"OCR error: {str(ocr_err)}\n"

        return result

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
    Main entry point. Input can be a file_id, filename, or URL.
    """
    input = input.strip()

    # Check if it's a URL
    if input.startswith("http://") or input.startswith("https://"):
        return read_url(input)

    # Check registered files by file_id
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

    # Try latest uploaded file
    latest = get_latest_file()
    if latest:
        return read_file(latest["path"], latest["name"])

    return f"File not found: '{input}'. Please upload a file first."
import csv
import os

import docx
import fitz  # PyMuPDF

MAX_PDF_PAGES = 100
MAX_EXTRACTED_TEXT_CHARS = 500_000


def _bounded_text(text: str) -> str:
    if len(text) > MAX_EXTRACTED_TEXT_CHARS:
        raise ValueError("Extracted text exceeds 500,000-character limit")
    return text


def parse_txt(file_path: str) -> str:
    """Reads and returns text from a .txt or .md file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return _bounded_text(file.read(MAX_EXTRACTED_TEXT_CHARS + 1))


def parse_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    text_content = []
    with fitz.open(file_path) as doc:
        if doc.page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF exceeds {MAX_PDF_PAGES}-page text extraction limit")
        for page in doc:
            text_content.append(page.get_text())
            if sum(map(len, text_content)) > MAX_EXTRACTED_TEXT_CHARS:
                raise ValueError("Extracted text exceeds 500,000-character limit")
    return "\n".join(text_content)


def parse_docx(file_path: str) -> str:
    """Extracts text from a Word document (.docx)."""
    doc = docx.Document(file_path)
    text_content = [paragraph.text for paragraph in doc.paragraphs]
    return _bounded_text("\n".join(text_content))


def parse_csv(file_path: str) -> str:
    """Reads a CSV and returns it as pipe-separated rows (one chunk per row group)."""
    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = [", ".join(row) for row in reader]
    return _bounded_text("\n".join(rows))


def parse_document(file_path: str) -> str:
    """
    Master routing function to extract text from a file based on its extension.
    Supported extensions: .txt, .md, .pdf, .docx, .csv
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path.lower())

    if ext in [".txt", ".md"]:
        return parse_txt(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".csv":
        return parse_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type for parsing: {ext}")

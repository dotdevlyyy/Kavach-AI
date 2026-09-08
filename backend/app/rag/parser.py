import os
import fitz  # PyMuPDF
import docx

def parse_txt(file_path: str) -> str:
    """Reads and returns text from a .txt or .md file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    text_content = []
    doc = fitz.open(file_path)
    for page in doc:
        text_content.append(page.get_text())
    doc.close()
    return "\n".join(text_content)

def parse_docx(file_path: str) -> str:
    """Extracts text from a Word document (.docx)."""
    doc = docx.Document(file_path)
    text_content = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(text_content)

def parse_document(file_path: str) -> str:
    """
    Master routing function to extract text from a file based on its extension.
    Supported extensions: .txt, .md, .pdf, .docx
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path.lower())
    
    if ext in ['.txt', '.md']:
        return parse_txt(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type for parsing: {ext}")

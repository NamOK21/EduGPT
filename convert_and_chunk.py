import os
import re
import json
from pathlib import Path
from docx import Document
from PyPDF2 import PdfReader

# Divide text into small chunks (~1000 characters)
def chunk_text(text, max_chars=500):
    paragraphs = re.split(r'\n{2,}', text)
    chunks = []
    buffer = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buffer) + len(para) <= max_chars:
            buffer += " " + para
        else:
            chunks.append(buffer.strip())
            buffer = para
    if buffer:
        chunks.append(buffer.strip())
    return chunks


def process_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return full_text


def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])


def convert_and_chunk(file_path, output_dir="data", max_chars=1000):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        raw_text = process_pdf(file_path)
    elif ext == ".docx":
        raw_text = process_docx(file_path)
    else:
        raise ValueError("❌ Chỉ hỗ trợ file .pdf hoặc .docx")

    chunks = chunk_text(raw_text, max_chars=max_chars)
    structured = [{"section": f"{Path(file_path).stem} - đoạn {i+1}", "content": chunk} for i, chunk in enumerate(chunks)]

    output_path = os.path.join(output_dir, f"{Path(file_path).stem}_chunks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã xử lý: {file_path} ➜ {len(chunks)} đoạn")
    return output_path

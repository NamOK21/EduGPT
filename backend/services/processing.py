import re
import pdfplumber
from docx import Document

def clean_text(text):
    text = re.sub(r'(?<!\n)([IVXLCDM]{1,3}\.\s+[^\n]{4,})', r'\n\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def chunk_text(text, max_chars=800):
    text = clean_text(text)
    if '\n\n' not in text:
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks = []
        buffer = ""
        for sent in sentences:
            if len(buffer) + len(sent) <= max_chars:
                buffer += " " + sent
            else:
                chunks.append(buffer.strip())
                buffer = sent
        if buffer.strip():
            chunks.append(buffer.strip())
        return chunks

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

def describe_table(table_data):
    if not table_data or len(table_data) < 2:
        return ""
    header = [clean_text(cell) if cell else "" for cell in table_data[0]]
    lines = []
    for row in table_data[1:]:
        row = [clean_text(cell) if cell else "" for cell in row]
        subject = row[0] if row else "Nội dung"
        desc = []
        for i in range(1, len(header)):
            col_name = header[i] if i < len(header) else f"Cột {i+1}"
            value = row[i] if i < len(row) else ""
            if value:
                desc.append(f"{col_name.lower()}: {value} tiết")
        lines.append(f"{subject}: {', '.join(desc)}")
    return " ".join(lines)

def extract_pdf_text(pdf_path):
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)

def extract_described_tables(pdf_path):
    described = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for idx, table in enumerate(tables):
                desc = describe_table(table)
                if desc:
                    described.append({
                        "section": f"Bảng {idx+1} trang {page_num}",
                        "subsection": "",
                        "type": "table",
                        "content": desc
                    })
    return described

def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
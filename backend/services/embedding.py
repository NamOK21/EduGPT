from pathlib import Path
import os
import json
import sqlite3
import numpy as np
from config import model, DB_PATH
from services.processing import clean_text, chunk_text, extract_pdf_text, extract_described_tables, process_docx


def convert_and_embed(file_path):
    ext = Path(file_path).suffix.lower()
    filename = Path(file_path).name
    records = []

    # Extract content như cũ
    if ext == ".pdf":
        text = extract_pdf_text(file_path)
        records = extract_sections(text)
        records += extract_described_tables(file_path)
    elif ext == ".docx":
        text = process_docx(file_path)
        records = [{
            "section": Path(file_path).stem,
            "subsection": f"Đoạn {i+1}",
            "type": "text",
            "content": chunk
        } for i, chunk in enumerate(chunk_text(text))]
    else:
        raise ValueError("Chỉ hỗ trợ PDF hoặc DOCX.")

    # Ghi JSON như cũ
    os.makedirs("data", exist_ok=True)
    json_path = f"data/{Path(file_path).stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # === NHÚNG HÀNG LOẠT ===
    contents = [r["content"] for r in records]
    vectors = model.encode(contents, batch_size=32, show_progress_bar=True)

    # Lưu vào SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            file TEXT,
            category TEXT,
            section TEXT,
            subsection TEXT,
            type TEXT,
            content TEXT,
            vector BLOB
        )
    """)

    for r, vec in zip(records, vectors):
        cur.execute("""
            INSERT INTO chunks (file, category, section, subsection, type, content, vector)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            None,
            r.get("section", ""),
            r.get("subsection", ""),
            r.get("type", "text"),
            r["content"],
            vec.astype(np.float32).tobytes()
        ))

    conn.commit()
    conn.close()
    return len(records)


def extract_sections(text):
    text = clean_text(text)
    import re
    pattern = re.compile(r'(?:^|\n)([IVXLCDM]{1,3}\.?\s+[^\n]{4,50})\s')
    matches = list(pattern.finditer(text))

    if not matches:
        chunks = chunk_text(text)
        return [{
            "section": "Toàn văn",
            "subsection": f"Đoạn {i+1}",
            "type": "text",
            "content": chunk
        } for i, chunk in enumerate(chunks)]

    sections = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        body = text[start:end].strip()
        for j, chunk in enumerate(chunk_text(body)):
            sections.append({
                "section": title,
                "subsection": f"Đoạn {j+1}",
                "type": "text",
                "content": chunk
            })
    return sections
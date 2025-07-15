from pathlib import Path
import os
import json
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from config import DB_PATH
from services.processing import clean_text, chunk_text, extract_pdf_text, extract_described_tables, process_docx, extract_sections

model = SentenceTransformer("all-MiniLM-L6-v2")

def infer_category_from_filename(filename: str) -> str:
    name = filename.lower()
    if "nghi_quyet" in name:
        return "Nghị quyết"
    elif "thong_tu" in name:
        return "Thông tư"
    elif "vb" in name or "vanban" in name:
        return "Văn bản"
    else:
        return "Khác"

def convert_and_embed(file_path):
    ext = Path(file_path).suffix.lower()
    filename = Path(file_path).name
    category = infer_category_from_filename(filename)

    # === Trích xuất nội dung ===
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

    # === Lưu bản sao JSON để debug nếu cần ===
    os.makedirs("data", exist_ok=True)
    json_path = f"data/{Path(file_path).stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # === Vector hóa toàn bộ ===
    contents = [r["content"] for r in records]
    vectors = model.encode(contents, batch_size=32, show_progress_bar=True)

    # === Ghi vào SQLite ===
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
        # Ghi log kiểm tra
        print(f"[{r.get('section', '')}] {r.get('subsection', '')}: {r['content'][:60]}...")

        cur.execute("""
            INSERT INTO chunks (file, category, section, subsection, type, content, vector)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            category,
            r.get("section", ""),
            r.get("subsection", ""),
            r.get("type", "text"),
            r["content"],
            vec.astype(np.float32).tobytes()
        ))

    conn.commit()
    conn.close()
    print(f"✅ Đã xử lý {len(records)} đoạn từ file {filename}")
    return len(records)

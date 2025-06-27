
import json
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import re

# Kết nối CSDL
conn = sqlite3.connect("db/vectors.db")
cur = conn.cursor()

# Tạo bảng nếu chưa có
cur.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    section TEXT,
    content TEXT,
    vector BLOB
)
""") 

model = SentenceTransformer("all-MiniLM-L6-v2")

def split_text(text, max_tokens=300):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) < max_tokens:
            current += " " + sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())

    return chunks

# Duyệt các file JSON trong thư mục data/
for filename in os.listdir("data"):
    if filename.endswith(".json"):
        with open(os.path.join("data", filename), encoding="utf-8") as f:
            data = json.load(f)
            for chunk in data:
                section = chunk.get("section", "").replace("\n", " ").strip()
                content = chunk.get("content", "").replace("\n", " ").strip()
                small_chunks = split_text(content)
                for sub in small_chunks:
                    cleaned_sub = sub.replace("\n", " ").strip()
                    vec = model.encode(cleaned_sub).astype(np.float32)
                    cur.execute(
                        "INSERT INTO chunks (section, content, vector) VALUES (?, ?, ?)",
                        (section, cleaned_sub, vec.tobytes())
                    )

conn.commit()
conn.close()
print("✅ Đã nhúng và lưu CSDL (đã loại bỏ \n).")

from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_query_sqlite import retrieve_context, build_prompt
from PyPDF2 import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer

import os
import tempfile
import json
import re
import sqlite3
import numpy as np
from pathlib import Path
import requests

app = Flask(__name__)
CORS(app)

DB_PATH = "db/vectors.db"
model = SentenceTransformer("all-MiniLM-L6-v2")
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")

# 🔹 Tách đoạn văn
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

# 🔹 Đọc nội dung file
def process_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])

# 🔹 Nhúng và lưu vào SQLite
def convert_and_embed(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        raw_text = process_pdf(file_path)
    elif ext == ".docx":
        raw_text = process_docx(file_path)
    else:
        raise ValueError("Chỉ hỗ trợ file PDF hoặc DOCX.")

    chunks = chunk_text(raw_text, max_chars=800)
    records = [{"section": f"{Path(file_path).stem} - đoạn {i+1}", "content": c} for i, c in enumerate(chunks)]

    # Lưu file json
    os.makedirs("data", exist_ok=True)
    basename = os.path.basename(file_path)
    json_name = os.path.splitext(basename)[0] + ".json"
    json_path = os.path.join("data", json_name)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Nhúng vector
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            section TEXT,
            content TEXT,
            vector BLOB
        )
    """)
    for r in records:
        vector = model.encode(r["content"]).astype(np.float32)
        cur.execute("INSERT INTO chunks (section, content, vector) VALUES (?, ?, ?)",
                    (r["section"], r["content"], vector.tobytes()))
    conn.commit()
    conn.close()

    return len(records)  # ✅ phải nằm trong thân hàm này



# 🧠 Gửi prompt tới LM Studio
def query_lmstudio(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý giáo dục thông minh, chỉ trả lời theo tài liệu."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 512
    }

    try:
        res = requests.post(LM_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Lỗi từ LM Studio: {e}"

# 📤 API hỏi đáp
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"answer": "❗ Vui lòng nhập câu hỏi."})

    context = retrieve_context(question)
    if not context:
        return jsonify({"answer": "❗ Không tìm thấy nội dung phù hợp trong tài liệu."})

    prompt = build_prompt(context, question)
    answer = query_lmstudio(prompt)
    return jsonify({"answer": answer})

# 📎 API upload file
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Không tìm thấy hoặc tên file trống."}), 400

    filename = str(file.filename).strip()
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".docx"]:
        return jsonify({"status": "error", "message": "Chỉ hỗ trợ file PDF hoặc DOCX."}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp.name)
            count = convert_and_embed(tmp.name)
        return jsonify({"status": "success", "message": f"✅ Đã xử lý {count} đoạn từ file."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"❌ Lỗi xử lý file: {e}"}), 500

if __name__ == "__main__":
    app.run(port=5678, debug=True)

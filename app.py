from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_query_sqlite import retrieve_context
from docx import Document
from sentence_transformers import SentenceTransformer

import os
import json
import re
import sqlite3
import numpy as np
from pathlib import Path
import requests
import pdfplumber
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

DB_PATH = "db/vectors.db"
model = SentenceTransformer("all-MiniLM-L6-v2")
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")


### ===============================
### XỬ LÝ NỘI DUNG (PDF, DOCX, TEXT)
### ===============================

def clean_text(text):
    text = text.strip()
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def chunk_text(text, max_chars=800):
    paragraphs = re.split(r'\n{2,}', clean_text(text))
    chunks = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) <= max_chars:
            buffer += " " + para
        else:
            if buffer.strip():
                chunks.append(buffer.strip())
            buffer = para
    if buffer.strip():
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

def extract_pdf_text(pdf_path):
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)

def extract_sections(text):
    pattern = r'(Chương\s+[IVXLCDM]+.*?)\n'
    parts = re.split(pattern, text)

    if len(parts) == 1:
        chunks = chunk_text(text)
        return [{
            "section": "Toàn văn",
            "subsection": f"Đoạn {i+1}",
            "type": "text",
            "content": chunk
        } for i, chunk in enumerate(chunks)]

    sections = []
    for i in range(1, len(parts), 2):
        title = clean_text(parts[i])
        body = clean_text(parts[i + 1]) if i + 1 < len(parts) else ""
        chunks = chunk_text(body)
        for j, c in enumerate(chunks):
            sections.append({
                "section": title,
                "subsection": f"Đoạn {j+1}",
                "type": "text",
                "content": c
            })
    return sections

def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])


### ===============================
### XỬ LÝ VÀ LƯU DỮ LIỆU (EMBED, LƯU DB, LƯU JSON)
### ===============================

def convert_and_embed(file_path):
    ext = Path(file_path).suffix.lower()
    filename = Path(file_path).name
    records = []

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
        raise ValueError("Chỉ hỗ trợ file PDF hoặc DOCX.")

    # Lưu JSON
    os.makedirs("data", exist_ok=True)
    with open(f"data/{Path(file_path).stem}.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Nhúng vector và lưu vào SQLite
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
    for r in records:
        vec = model.encode(r["content"]).astype(np.float32)
        cur.execute("""
            INSERT INTO chunks (file, category, section, subsection, type, content, vector)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            filename, None, r["section"], r["subsection"], r["type"], r["content"], vec.tobytes()
        ))
    conn.commit()
    conn.close()

    return len(records)


### ===============================
### XÂY DỰNG PROMPT VÀ GỌI MODEL
### ===============================

def build_prompt(context_chunks, question):
    context_text = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])

    system_instruction = (
        "Bạn là trợ lý giáo dục thông minh. "
        "Hãy ưu tiên trả lời theo thông tin trong tài liệu dưới đây. "
        "Nếu cần thiết, bạn có thể diễn giải hoặc suy luận nhẹ dựa trên ngữ cảnh, "
        "nhưng phải đảm bảo không gây hiểu nhầm và không bịa đặt thông tin không có cơ sở. "
        "Nếu tài liệu không cung cấp đủ dữ kiện, hãy nói rõ điều đó."
    )

    user_prompt = (
        f"--- TÀI LIỆU ---\n{context_text}\n\n"
        f"--- CÂU HỎI ---\n{question}\n\n"
        f"--- YÊU CẦU ---\n"
        f"Trả lời ngắn gọn, đúng trọng tâm, dựa trên tài liệu. "
        f"Có thể diễn giải nhẹ nếu có cơ sở từ ngữ cảnh, nhưng cần thận trọng và rõ ràng."
    )

    return {
        "system": system_instruction,
        "user": user_prompt
    }

def query_lmstudio(user_msg, system_msg):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg.strip()}
        ],
        "temperature": 0.2,
        "max_tokens": 512
    }

    try:
        res = requests.post(LM_API_URL, headers=headers, json=payload)
        res.raise_for_status()  # Raise lỗi nếu không phải 2xx
        return res.json()["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as err:
        print("❌ Lỗi HTTP:", err.response.status_code, err.response.reason)
        print("📨 Nội dung phản hồi từ LM Studio:", err.response.text)  # In JSON lỗi chi tiết
        return f"❌ Lỗi từ LM Studio: {err.response.status_code} - {err.response.reason}"

    except Exception as e:
        print("❌ Lỗi kết nối hoặc xử lý khác:", str(e))
        return f"❌ Lỗi kết nối đến LM Studio: {e}"


### ===============================
### API FLASK
### ===============================

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
    answer = query_lmstudio(prompt["user"], prompt["system"])
    return jsonify({"answer": answer})


@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Không có file."}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx"]:
            return jsonify({"status": "error", "message": "Chỉ hỗ trợ PDF hoặc DOCX."}), 400

        os.makedirs("uploaded", exist_ok=True)
        safe_name = secure_filename(file.filename)
        save_path = os.path.join("uploaded", safe_name)
        file.save(save_path)

        count = convert_and_embed(save_path)

        return jsonify({
            "status": "success",
            "message": f"✅ Đã xử lý {count} đoạn từ file {file.filename}.",
            "processed": count,
            "filename": file.filename
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Lỗi xử lý backend: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(port=5678, debug=True)

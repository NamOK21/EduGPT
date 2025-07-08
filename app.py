from flask import Flask, request, jsonify, send_from_directory
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

app = Flask(__name__, static_folder="frontend/react-ui/build", static_url_path="/")
CORS(app)

DB_PATH = "db/vectors.db"
model = SentenceTransformer("all-MiniLM-L6-v2")
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")


### ===============================
### TIỀN XỬ LÝ VĂN BẢN
### ===============================

def clean_text(text):
    # Đảm bảo heading La Mã như I. II. có dòng riêng
    text = re.sub(r'(?<!\n)([IVXLCDM]{1,3}\.?\s+[^\n]{4,})', r'\n\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def chunk_text(text, max_chars=800):
    text = clean_text(text)
    
    # Nếu không có \n\n thì chia theo dấu chấm câu
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

    # Nếu có \n\n thì chia theo đoạn bình thường
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
    text = clean_text(text)
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

def process_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])


### ===============================
### NHÚNG VÀ LƯU
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
        raise ValueError("Chỉ hỗ trợ PDF hoặc DOCX.")

    os.makedirs("data", exist_ok=True)
    json_path = f"data/{Path(file_path).stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

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
            filename,
            None,
            r.get("section", ""),
            r.get("subsection", ""),
            r.get("type", "text"),
            r["content"],
            vec.tobytes()
        ))

    conn.commit()
    conn.close()
    return len(records)


### ===============================
### GỌI LLM
### ===============================

def build_prompt(context_chunks, question, max_chars=3000):
    context_text = ""
    total_len = 0
    for i, chunk in enumerate(context_chunks):
        chunk_text = f"[{i+1}] {chunk.strip()}\n\n"
        if total_len + len(chunk_text) > max_chars:
            break
        context_text += chunk_text
        total_len += len(chunk_text)

    system_instruction = (
        "Bạn là một trợ lý thông minh, chuyên hỗ trợ trả lời các câu hỏi liên quan đến các Nghị quyết, văn bản được ban hành bởi Đảng Cộng sản Việt Nam. "
        "Hãy ưu tiên trả lời theo thông tin trong các tài liệu được cung cấp. "
        "Nếu tài liệu không đủ dữ kiện, hãy nói rõ điều đó. "
        "Trả lời ngắn gọn, chính xác, đúng trọng tâm."
    )

    user_prompt = (
        f"--- TÀI LIỆU ---\n{context_text}\n\n"
        f"--- CÂU HỎI ---\n{question}\n\n"
        f"--- YÊU CẦU ---\n"
        f"Trả lời rõ ràng, ngắn gọn, dựa vào tài liệu. "
        f"Nếu cần diễn giải, hãy đảm bảo không suy diễn trong giới hạn cho phép."
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
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as err:
        return f"❌ Lỗi LM Studio: {err.response.status_code} - {err.response.text}"
    except Exception as e:
        return f"❌ Không kết nối được LM Studio: {e}"
    
    
def generate_related_questions(question):
    prompt = f"""
        Người dùng vừa hỏi: "{question}"

        Hãy tạo 6-8 câu hỏi liên quan, giúp người dùng hiểu sâu hơn về chủ đề.
        Ưu tiên những câu hỏi liên quan đến giải pháp, trách nhiệm, phương pháp.
        Chỉ xuất ra câu hỏi, mỗi câu một dòng, không đánh số, không thêm lời giải thích, không lặp lại câu gốc.
        """

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-3b-instruct",  
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 256
    }

    try:
        res = requests.post(LM_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        suggestions = [line.strip("-•. 1234567890 ") for line in content.split("\n") if line.strip()]
        return suggestions[:6]
    except Exception as e:
        return []



### ===============================
### FLASK API
### ===============================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    static_dir = app.static_folder or "frontend/react-ui/build"
    static_dir = str(static_dir)  

    full_path = os.path.join(static_dir, path)
    if path and os.path.exists(full_path):
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, "index.html")


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

    # Gợi ý câu hỏi liên quan
    related = generate_related_questions(question)

    return jsonify({
        "answer": answer,
        "related_questions": related
    })


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
            "message": f"Lỗi xử lý file: {str(e)}"
        }), 500
    
@app.route("/related_questions", methods=["POST"])
def related_questions():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"related_questions": []})
    return jsonify({"related_questions": generate_related_questions(question)})



if __name__ == "__main__":
    app.run(port=5678, debug=True)

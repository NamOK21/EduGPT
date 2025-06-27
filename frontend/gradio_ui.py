import gradio as gr
import requests
import random
import os
import sys
import json
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

# Đường dẫn
sys.path.append("..")
from convert_and_chunk import convert_and_chunk

DB_PATH = os.path.join("..", "db", "vectors.db")
DATA_PATH = os.path.join("..", "data")
model = SentenceTransformer("all-MiniLM-L6-v2")

# === 📤 Truy vấn Flask API ===
def ask_question(q):
    if not q:
        return "❗ Vui lòng nhập hoặc chọn một câu hỏi."
    try:
        res = requests.post("http://127.0.0.1:5678/ask", json={"question": q})
        return res.json().get("answer", "⚠️ Không có phản hồi từ hệ thống.")
    except Exception as e:
        return f"❌ Lỗi kết nối: {e}"

# === 📎 Xử lý upload file văn bản ===
def upload_and_embed(file):
    if not file:
        return "❌ Vui lòng chọn file"
    try:
        json_path = convert_and_chunk(file.name, output_dir=DATA_PATH)
        with open(json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for chunk in chunks:
            vector = model.encode(chunk["content"]).astype(np.float32)
            cur.execute("INSERT INTO chunks (section, content, vector) VALUES (?, ?, ?)",
                        (chunk["section"], chunk["content"], vector.tobytes()))
        conn.commit(); conn.close()
        return f"✅ Đã xử lý {len(chunks)} đoạn từ file: {os.path.basename(file.name)}"
    except Exception as e:
        return f"❌ Lỗi xử lý: {e}"

# === 💡 Câu hỏi gợi ý ngẫu nhiên ===
all_suggestions = [
    "Mục tiêu của chương trình giáo dục phổ thông là gì?",
    "Môn Tiếng Anh ở cấp trung học cơ sở dạy gì?",
    "Học sinh được đánh giá thế nào trong môn Giáo dục thể chất?",
    "Môn Toán ở tiểu học gồm những nội dung gì?",
    "Chương trình có chia giai đoạn giáo dục không?",
    "Các môn học bắt buộc và tự chọn gồm những gì?",
    "Giáo dục định hướng nghề nghiệp bắt đầu từ lớp mấy?",
    "Yêu cầu cần đạt trong môn Lịch sử là gì?",
    "Chương trình môn Địa lý giúp học sinh phát triển năng lực nào?",
    "Nội dung giáo dục của địa phương được dạy như thế nào?",
]
suggested_questions = random.sample(all_suggestions, 4)

# === 🚀 Giao diện Gradio UI ===
with gr.Blocks(title="Trợ lý giáo dục", css="body { font-family: 'Segoe UI'; }") as demo:
    gr.Markdown("# 🎓 Trợ lý giáo dục - Hỏi đáp theo Thông tư")
    gr.Markdown("🧠 Nhập câu hỏi hoặc chọn một gợi ý bên dưới để nhận phản hồi từ hệ thống dựa trên các Thông tư và văn bản pháp luật.")

    with gr.Tab("❓ Đặt câu hỏi"):
        with gr.Row():
            question_input = gr.Textbox(placeholder="Ví dụ: Môn Toán tiểu học dạy gì?", label="📥 Câu hỏi")
            ask_btn = gr.Button("📤 Gửi")
        output = gr.Textbox(label="📘 Trả lời", lines=12, interactive=False)
        ask_btn.click(fn=ask_question, inputs=question_input, outputs=output)
        question_input.submit(fn=ask_question, inputs=question_input, outputs=output)

        gr.Markdown("## 💡 Câu hỏi gợi ý:")
        with gr.Row():
            for q in suggested_questions[:2]:
                gr.Button(q).click(fn=ask_question, inputs=gr.Textbox(value=q, visible=False), outputs=output)
        with gr.Row():
            for q in suggested_questions[2:]:
                gr.Button(q).click(fn=ask_question, inputs=gr.Textbox(value=q, visible=False), outputs=output)

    with gr.Tab("📎 Tải văn bản"):
        gr.Markdown("Tải lên file **PDF** hoặc **DOCX**. Hệ thống sẽ tự động chuyển đổi, phân đoạn và nhúng dữ liệu vào vector database.")
        file_input = gr.File(label="📂 Chọn file văn bản", file_types=[".pdf", ".docx"])
        upload_btn = gr.Button("🚀 Xử lý và Nhúng")
        upload_log = gr.Textbox(label="📜 Nhật ký", lines=10, interactive=False)
        upload_btn.click(fn=upload_and_embed, inputs=file_input, outputs=upload_log)

demo.launch()

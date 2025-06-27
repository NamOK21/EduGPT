from flask import Flask, request, jsonify
from rag_query_sqlite import retrieve_context, build_prompt
import requests
import os

app = Flask(__name__)

LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")  # Đường dẫn LM Studio

def query_lmstudio(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "vistral-7b-chat",  # hoặc "llama-3.2-3b-instruct" nếu bạn dùng model đó
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý giáo dục thông minh, chỉ trả lời theo tài liệu."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 512
    }

    try:
        response = requests.post("http://127.0.0.1:1234/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Lỗi từ LM Studio: {e}"


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "❗ Vui lòng nhập câu hỏi."})

    context = retrieve_context(question)
    if not context:
        return jsonify({"answer": "Tôi không tìm thấy nội dung này trong tài liệu."})

    prompt = build_prompt(context, question)
    answer = query_lmstudio(prompt)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(port=5678)

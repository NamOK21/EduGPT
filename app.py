from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_query_sqlite import retrieve_context, build_prompt
import requests
import os

app = Flask(__name__)
CORS(app)  # Allowing React frontend to access from different domain

# URL to local LM Studio API
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")

# Send prompt to LM Studio
def query_lmstudio(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-3b-instruct",  # Can be changed to different models
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý giáo dục thông minh, chỉ trả lời theo tài liệu."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 512
    }

    try:
        response = requests.post(LM_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Lỗi từ LM Studio: {e}"

# API receives question from React frontend
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

# Ready
if __name__ == "__main__":
    app.run(port=5678, debug=True)

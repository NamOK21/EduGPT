from flask import Blueprint, request, jsonify
from services.llm import build_prompt, query_lmstudio
from rag_query_sqlite import retrieve_context

ask_bp = Blueprint("ask", __name__)

@ask_bp.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"status": "error", "message": "Câu hỏi trống."}), 400

        context_chunks = retrieve_context(question)
        prompt_parts = build_prompt(context_chunks, question)
        answer = query_lmstudio(prompt_parts["user"], prompt_parts["system"])

        return jsonify({
            "status": "success",
            "question": question,
            "context": context_chunks,
            "answer": answer
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi xử lý câu hỏi: {e}"}), 500

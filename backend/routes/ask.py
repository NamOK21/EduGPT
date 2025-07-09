from flask import Blueprint, request, jsonify
from services.llm import build_prompt, query_lmstudio, generate_related_questions
from rag_query_sqlite import retrieve_context

ask_bp = Blueprint("ask", __name__)

@ask_bp.route("/ask", methods=["POST"])
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
    related = generate_related_questions(question)
    return jsonify({"answer": answer, "related_questions": related})
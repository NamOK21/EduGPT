from flask import Blueprint, request, jsonify
from services.llm import generate_related_questions

related_bp = Blueprint("related", __name__)

@related_bp.route("/related_questions", methods=["POST"])
def related_questions():
    print("✅ [Flask] Đã nhận được request /related_questions", flush=True)
    try:
        data = request.get_json(force=True)  # thêm force để ép đọc
        print("❓ Question nhận vào:", data.get("question"), flush=True)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"related_questions": []})
        suggestions = generate_related_questions(question)
        return jsonify({"related_questions": suggestions})
    except Exception as e:
        print("[ERROR - /related_questions]:", str(e))
        return jsonify({"related_questions": [], "error": str(e)}), 500
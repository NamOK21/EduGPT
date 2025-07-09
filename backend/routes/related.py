from flask import Blueprint, request, jsonify
from services.llm import generate_related_questions

related_bp = Blueprint("related", __name__)

@related_bp.route("/related_questions", methods=["POST"])
def related_questions():
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"related_questions": []})
    return jsonify({"related_questions": generate_related_questions(question)})
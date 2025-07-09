from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.embedding import convert_and_embed
import os

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload", methods=["POST"])
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
        return jsonify({"status": "error", "message": f"Lỗi xử lý file: {str(e)}"}), 500
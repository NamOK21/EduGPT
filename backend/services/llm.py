import requests
from config import LM_API_URL

def build_prompt(context_chunks, question, max_chars=3000):
    context_text = ""
    total_len = 0

    # Tạo nội dung tài liệu với đánh số đoạn [1], [2], ...
    for i, chunk in enumerate(context_chunks):
        chunk_text = f"[{i+1}] {chunk.strip()}\n\n"
        if total_len + len(chunk_text) > max_chars:
            break
        context_text += chunk_text
        total_len += len(chunk_text)

    # Prompt system (chỉ thị nghiêm ngặt)
    system_instruction = (
        "Bạn là một trợ lý ảo nghiêm túc, chỉ trả lời dựa trên các tài liệu được cung cấp. "
        "Không được suy diễn, không được thêm thông tin ngoài context. "
        "Nếu không có thông tin trong tài liệu, hãy trả lời: 'Tôi không tìm thấy nội dung này trong tài liệu.' "
        "Tránh mọi khái quát hoặc tổng hợp vượt quá nội dung được cung cấp. "
        "Nếu có thể, hãy trích dẫn số thứ tự đoạn tài liệu theo dạng [1], [2]... để minh bạch nguồn thông tin."
    )

    # Prompt người dùng
    user_prompt = (
        f"--- TÀI LIỆU ---\n{context_text}\n\n"
        f"--- CÂU HỎI ---\n{question}\n\n"
        f"--- YÊU CẦU ---\n"
        f"- Trả lời rõ ràng, đúng trọng tâm, dựa vào nội dung tài liệu.\n"
        f"- Không thêm bình luận chủ quan hoặc giả định.\n"
        f"- Nếu câu trả lời có thể trích dẫn từ tài liệu, hãy ghi số đoạn tham chiếu theo định dạng [1], [2]... Mỗi ý đều xuống dòng\n"
        f"- Nếu không đủ dữ kiện, hãy nói rõ là tài liệu không có thông tin đó."
    )

    return {
        "system": system_instruction,
        "user": user_prompt
    }



def query_lmstudio(user_msg, system_msg):
    payload = {
        "model": "llama-3.2-3b-instruct",  # hoặc model bạn đang dùng trong LM Studio
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
        "max_tokens": 768
    }
    try:
        res = requests.post(LM_API_URL, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Không kết nối được LM Studio: {e}"


def generate_related_questions(question):
    prompt = f"""Từ câu hỏi: "{question}", hãy tạo ra 6–8 câu hỏi mở rộng có liên quan,
    ưu tiên tập trung vào giải pháp, trách nhiệm, phương pháp triển khai.
    Yêu cầu:
    - Chỉ xuất ra danh sách câu hỏi.
    - Mỗi câu nằm trên một dòng, không đánh số, không gạch đầu dòng.
    - Không ghi phần mở đầu, không lặp lại câu gốc.
    - Văn phong rõ ràng, nghiêm túc, ngắn gọn."""

    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 256
    }

    try:
        res = requests.post(LM_API_URL, json=payload)
        res.raise_for_status()
        result = res.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            print("[⚠️ EMPTY CONTENT]:", result)
        questions = [
            line.strip("•-–. 1234567890\t") for line in content.split("\n")
            if line.strip() and len(line.strip()) > 10
        ]
        return questions[:6]
    except Exception as e:
        print("[❌ ERROR - generate_related_questions]:", str(e))
        return []


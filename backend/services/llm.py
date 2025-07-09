import requests
from config import LM_API_URL

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
        f"Nếu cần diễn giải, hãy đảm bảo chỉ suy diễn trong giới hạn cho phép."
    )
    return {"system": system_instruction, "user": user_prompt}

def query_lmstudio(user_msg, system_msg):
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        "temperature": 0.2,
        "max_tokens": 512
    }
    try:
        res = requests.post(LM_API_URL, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Không kết nối được LM Studio: {e}"

def generate_related_questions(question):
    prompt = f"""
        Từ câu hỏi: "{question}", hãy tạo ra 6–8 câu hỏi mở rộng có liên quan,
        ưu tiên tập trung vào giải pháp, trách nhiệm, phương pháp triển khai.
        Chỉ xuất ra danh sách câu hỏi, **không ghi phần mở đầu, không dẫn nhập, không giải thích**.
        Không lặp lại câu gốc. Mỗi câu nằm trên một dòng. Không đánh số.
        Câu hỏi phải rõ ràng, nghiêm túc, ngắn gọn.
"""
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 256
    }
    try:
        res = requests.post(LM_API_URL, json=payload)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return [line.strip("-•. 1234567890 ") for line in content.split("\n") if line.strip()][:6]
    except Exception:
        return []
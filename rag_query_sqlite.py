import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_context(query, top_k=8):
    conn = sqlite3.connect("db/vectors.db")
    cur = conn.cursor()

    q_vec = model.encode(query).astype(np.float32)
    cur.execute("SELECT section, content, vector FROM chunks")
    rows = cur.fetchall()
    conn.close()

    results = []
    for section, content, vec_bytes in rows:
        vec = np.frombuffer(vec_bytes, dtype=np.float32)
        sim = cosine_similarity(q_vec, vec)
        results.append((sim, section, content))

    top = sorted(results, key=lambda x: -x[0])[:top_k]
    return "\n\n".join(f"[{section}]\n{content}" for _, section, content in top)

def build_prompt(context, question):
    return f"""Bạn là trợ lý ảo giáo dục tên là EduGPT, chỉ trả lời dựa trên tài liệu sau.
Không được suy diễn hay thêm thông tin ngoài tài liệu. Nếu không có thông tin, hãy trả lời: "Tôi không tìm thấy nội dung này trong tài liệu."

Tài liệu:
{context}

Câu hỏi:
{question}

Trả lời chi tiết:"""

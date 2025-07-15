import sqlite3
import numpy as np
from config import DB_PATH, model

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_context(question, top_k=12):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    q_vec = model.encode(question, convert_to_numpy=True).astype(np.float32)
    cur.execute("SELECT section, type, content, vector FROM chunks")
    rows = cur.fetchall()
    conn.close()

    results = []
    for section, typ, content, vec_bytes in rows:
        vec = np.frombuffer(vec_bytes, dtype=np.float32)
        sim = cosine_similarity(q_vec, vec)
        results.append((sim, section, typ, content))

    results.sort(key=lambda x: -x[0])
    top = results[:top_k]

    top_filtered = [r for r in top if r[0] > 0.05]

    if not top_filtered:
        print("[⚠️] Không tìm thấy đoạn nào có độ tương đồng đủ cao.")
        return ["[!] Không có đoạn tài liệu nào gần với câu hỏi."]
    
    print(f"[DEBUG] Tổng số đoạn lấy từ DB: {len(rows)}")
    print("=== Các đoạn có độ tương đồng > 0.05:")
    for sim, sec, typ, cont in top_filtered:
        print(f"[SIM {sim:.3f}] [{sec} - {typ}] {cont[:60].strip()}...")

    return [r[3] for r in top_filtered]

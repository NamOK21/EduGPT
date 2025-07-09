import os
from sentence_transformers import SentenceTransformer

DB_PATH = "db/vectors.db"
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
model = SentenceTransformer("all-MiniLM-L6-v2")
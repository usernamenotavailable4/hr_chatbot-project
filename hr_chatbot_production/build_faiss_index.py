import json
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

chunks_file = Path("chatbot/policy_chunks.json")
index_file = Path("chatbot/policy_faiss.index")

if not chunks_file.exists():
    print("Run prepare_chunks.py first.")
    exit()

chunks = json.loads(chunks_file.read_text())
texts = [c["text"] for c in chunks]

model = SentenceTransformer("all-MiniLM-L6-v2")

emb = model.encode(texts, convert_to_numpy=True).astype("float32")
faiss.normalize_L2(emb)

index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)

faiss.write_index(index, str(index_file))
print("Saved index:", index_file)

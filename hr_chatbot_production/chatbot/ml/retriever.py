# chatbot/ml/retriever.py
import json
from pathlib import Path

# try to use sentence-transformers + faiss
try:
    from sentence_transformers import SentenceTransformer, util
    _ST_AVAILABLE = True
except Exception:
    _ST_AVAILABLE = False

POLICY_CHUNKS_PATH = Path(__file__).resolve().parent.parent / "policy_chunks.json"  # chatbot/policy_chunks.json
_index_path = Path(__file__).resolve().parent.parent / "policy_faiss.index"
_model = None
_chunks = None

def _load_chunks():
    global _chunks
    if _chunks is None:
        if POLICY_CHUNKS_PATH.exists():
            _chunks = json.loads(POLICY_CHUNKS_PATH.read_text(encoding="utf-8"))
        else:
            _chunks = []
    return _chunks

def retrieve_policy_context(query: str, top_k=3):
    """
    Returns list of chunk dicts: {"id":..., "text":...}
    """
    chunks = _load_chunks()
    if not chunks:
        return []

    # If sentence-transformers available, do an embedding search
    if _ST_AVAILABLE:
        global _model
        if _model is None:
            try:
                _model = SentenceTransformer("all-MiniLM-L6-v2")  # small and fast
            except Exception as e:
                print("Could not load SBERT model:", e)
                _model = None

        if _model is not None:
            try:
                corpus = [c["text"] for c in chunks]
                corpus_emb = _model.encode(corpus, convert_to_tensor=True)
                q_emb = _model.encode(query, convert_to_tensor=True)
                hits = util.semantic_search(q_emb, corpus_emb, top_k=top_k)[0]
                results = []
                for h in hits:
                    idx = h["corpus_id"]
                    results.append({"id": chunks[idx]["id"], "text": chunks[idx]["text"], "score": float(h["score"])})
                return results
            except Exception as e:
                print("SBERT search failed, fallback to substring:", e)

    # fallback: simple substring + length scoring
    q = query.lower()
    scored = []
    for c in chunks:
        text = c.get("text","")
        score = 0
        if q in text.lower():
            score += 2
        # count keyword overlap
        for w in q.split():
            if w and w in text.lower():
                score += 0.1
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"id": c["id"], "text": c["text"], "score": float(s)} for s, c in scored[:top_k]]

# chatbot/ml/classifier.py
"""
Classifier to decide STATIC vs DYNAMIC queries.
STATIC -> policy lookup (FAISS)
DYNAMIC -> employee-specific data (DB)
This file uses a simple rule-based fallback; if you later train BERT, place the model in
chatbot/ml/model_static_dynamic and the code will attempt to load it.
"""
import os
from pathlib import Path

# optional imports (will be used only if model exists)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    _TRANSFORMERS_AVAILABLE = False

MODEL_DIR = Path(__file__).resolve().parent / "model_static_dynamic"
_tokenizer = None
_model = None

def _maybe_load_model():
    global _tokenizer, _model
    if not _TRANSFORMERS_AVAILABLE:
        return
    if not MODEL_DIR.exists():
        return
    if _tokenizer is not None and _model is not None:
        return
    try:
        _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
        _model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR), local_files_only=True)
    except Exception as e:
        print("Could not load HF classifier model (falling back to rules):", e)
        _tokenizer = None
        _model = None

def classify_static_dynamic(text: str):
    """
    Returns (label: "STATIC"|"DYNAMIC", confidence: float)
    Uses optional HF model when available; else rule-based heuristics.
    """
    # if model folder present, try to use it
    if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
        _maybe_load_model()
        if _model and _tokenizer:
            try:
                inputs = _tokenizer(text, truncation=True, padding=True, return_tensors="pt")
                out = _model(**inputs)
                # take argmax
                scores = out.logits.detach().numpy().tolist()[0]
                import numpy as np
                idx = int(np.argmax(scores))
                label = "DYNAMIC" if idx == 1 else "STATIC"
                # softmax for confidence
                exp = np.exp(scores - np.max(scores))
                probs = exp / exp.sum()
                return label, float(probs[idx])
            except Exception as e:
                print("HF model run failed, fallback to rules:", e)

    # fallback rule-based mapping
    lower = text.lower()
    dynamic_keywords = [
        "balance", "my leave", "how many leaves", "acl", "casual", "sick", "maternity",
        "my balance", "remaining", "entitled", "how many", "my leaves"
    ]
    if any(k in lower for k in dynamic_keywords):
        return "DYNAMIC", 0.98
    return "STATIC", 0.90

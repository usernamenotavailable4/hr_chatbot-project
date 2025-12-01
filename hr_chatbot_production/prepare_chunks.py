from nltk.tokenize import sent_tokenize
from pathlib import Path
import nltk, json

nltk.download("punkt")

policy_file = Path("policies/leave_policy.txt")
if not policy_file.exists():
    print("Put your policy text at: policies/leave_policy.txt")
    exit(1)

text = policy_file.read_text(encoding="utf-8")
sents = sent_tokenize(text)

chunks = []
for i in range(0, len(sents), 5):
    part = " ".join(sents[i:i+5])
    chunks.append({"id": i, "text": part})

Path("chatbot/policy_chunks.json").write_text(json.dumps(chunks, indent=2), encoding="utf-8")
print("Created", len(chunks), "chunks")


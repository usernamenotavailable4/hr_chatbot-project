# chatbot/ml/chat_pipeline.py
from .classifier import classify_static_dynamic
from .retriever import retrieve_policy_context
from ..db_utils import get_employee_leave_balance

def handle_user_query(message: str, employee_id: str = None, employee_type: str = None):
    """
    Returns a dict serializable to JSON:
      {"reply": "...", "mode": "STATIC" or "DYNAMIC", "confidence": 0.9}
    """
    label, confidence = classify_static_dynamic(message)

    if label == "DYNAMIC":
        # fetch employee info and produce a short reply
        bal = get_employee_leave_balance(employee_id) if employee_id else None
        if bal:
            reply = (
                f"Employee {bal.get('employee_id')} ({bal.get('employee_type')})\n"
                f"Casual Leave Remaining: {bal.get('cl_remaining')}\n"
                f"ACL Remaining: {bal.get('acl_remaining')}\n"
                f"Total Entitled: {bal.get('total_entitled')}\n"
                f"Last Updated: {bal.get('last_updated')}\n\n"
                f"Query: {message}"
            )
        else:
            # no employee data; fallback to suggest login or policy lookup
            reply = "I couldn't find your employee data. If you are logged in, contact HR or try a policy query."
        return {"reply": reply, "mode": "DYNAMIC", "confidence": confidence}

    # STATIC -> policy retrieval + short summarization (simple)
    contexts = retrieve_policy_context(message, top_k=2)
    if not contexts:
        # fallback to generic answer if no context found
        return {"reply": "Sorry — I couldn't find a policy about that. Try rephrasing your question.", "mode": "STATIC", "confidence": confidence}

    # combine retrieved chunks into a readable reply
    policy_text = "\n\n".join([c.get("text", "") for c in contexts])
    # include the user's query at the end for traceability
    reply = f"**Policy Information**\n\n{policy_text[:2000]}\n\n*Query:* {message}"
    return {"reply": reply, "mode": "STATIC", "confidence": confidence, "sources": [c["id"] for c in contexts]}

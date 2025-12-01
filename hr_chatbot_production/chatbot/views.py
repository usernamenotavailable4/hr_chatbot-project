# chatbot/views.py
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .db_utils import authenticate_user, get_employee_leave_balance
from .ml.chat_pipeline import handle_user_query

def login_page(request):
    # GET -> show login form
    if request.method == "GET":
        return render(request, "login.html")

    # POST -> attempt login
    if request.method == "POST":
        emp_id = request.POST.get("employee_id") or request.POST.get("employeeId")
        password = request.POST.get("password")
        if not emp_id or not password:
            return HttpResponseBadRequest("Missing credentials")

        ok, emp_type = authenticate_user(emp_id, password)
        if not ok:
            # authentication failed
            context = {"error": "Invalid credentials"}
            return render(request, "login.html", context)

        # store in session
        request.session["employee_id"] = emp_id
        request.session["employee_type"] = emp_type
        return redirect("home")

    return HttpResponseBadRequest("POST only")

def home(request):
    emp = request.session.get("employee_id")
    context = {"employee_id": emp}
    return render(request, "home.html", context)

def chatbot_widget(request):
    """Return the HTML partial used by the floating widget if needed."""
    return render(request, "chatbot_widget.html")

from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("login")

@csrf_exempt
def api_chat(request):
    """
    POST JSON: {"query": "..."}
    Response: JSON with 'reply' field and optional extra metadata.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST.dict() if request.POST else {}
    query = payload.get("query") or payload.get("q") or payload.get("message")
    if not query:
        return JsonResponse({"error": "no query provided"}, status=400)

    employee_id = request.session.get("employee_id")
    employee_type = request.session.get("employee_type")

    # If employee info exists, pass through; else None
    result = handle_user_query(query, employee_id=employee_id, employee_type=employee_type)

    return JsonResponse(result)

# chatbot/db_utils.py
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()  # loads .env at project root

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hr_db")

def get_mysql_connection():
    """Return a mysql.connector connection (caller must close)."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True,
        )
        return conn
    except Error as e:
        # bubble up with clear message
        raise RuntimeError(f"Cannot connect to MySQL: {e}")

def authenticate_user(employee_id: str, password: str):
    """
    Returns (ok: bool, employee_type: str or None)
    If DB not configured, accept a simple default (for local dev).
    """
    # quick dev fallback: if DB credentials are empty, allow EMP001/password123
    if DB_USER == "" and DB_PASSWORD == "":
        if employee_id == "EMP001" and password == "password123":
            return True, "Teaching"
        return False, None

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT employee_id, password, employee_type FROM employee_login WHERE employee_id=%s"
        cursor.execute(sql, (employee_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return False, None
        # NOTE: this example stores plaintext password in DB — replace with hashed checks in prod
        if row["password"] == password:
            return True, row.get("employee_type")
        return False, None
    except Exception as e:
        # if DB errors, deny but log
        print("DB auth error:", e)
        return False, None

def get_employee_leave_balance(employee_id: str):
    """
    Returns dict with leave fields or None.
    Example return:
      {"employee_id":"EMP001","total_entitled":30,"cl_remaining":12,"acl_remaining":5,"last_updated":"2025-02-15","employee_type":"Teaching"}
    """
    if not employee_id:
        return None

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        # join employee_login and leave balances (adjust to your schema)
        sql = """
        SELECT l.employee_id, l.total_entitled, l.cl_remaining, l.acl_remaining, l.last_updated, e.employee_type
        FROM employee_leave_balance l
        LEFT JOIN employee_login e ON e.employee_id = l.employee_id
        WHERE l.employee_id = %s
        """
        cursor.execute(sql, (employee_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        # convert date to string if necessary
        if row.get("last_updated") is not None:
            row["last_updated"] = str(row["last_updated"])
        return row
    except Exception as e:
        print("DB leave balance error:", e)
        return None

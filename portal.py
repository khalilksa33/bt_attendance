import json
import os
import requests
import secrets
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlencode
from http.cookies import SimpleCookie

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

REMOTE_CHECKIN_FILE = BASE_DIR / Path(os.getenv("REMOTE_CHECKIN_FILE", "remote_checkins.json"))
PORT = int(os.getenv("PORT", "5001"))
STATIC_DIR = BASE_DIR / "www"
PORTAL_ACCESS_CODE = os.getenv("PORTAL_ACCESS_CODE", "").strip()

# ERP credentials
ERP_URL = os.getenv("ERP_URL")
ERP_API_KEY = os.getenv("ERP_API_KEY")
ERP_API_SECRET = os.getenv("ERP_API_SECRET")

# Session storage: {session_token: {user_id, employee_id, employee_name, timestamp}}
SESSIONS = {}
SESSION_TIMEOUT = 3600  # 1 hour


def authenticate_erp_user(username, password):
    """
    Validate user credentials against ERP system.
    Returns (success, employee_id, employee_name) tuple.
    """
    try:
        url = f"{ERP_URL}/api/method/frappe.client.get_list"
        response = requests.post(
            url,
            json={
                "doctype": "User",
                "filters": [["User", "username", "=", username]],
                "fields": ["name", "email"],
            },
            timeout=10,
        )
        response.raise_for_status()
        users = response.json().get("message", [])

        if not users:
            return False, None, None

        # Try to authenticate with provided credentials
        auth_url = f"{ERP_URL}/api/resource/User/{username}"
        auth_response = requests.get(
            auth_url,
            auth=(username, password),
            timeout=10,
        )

        if auth_response.status_code != 200:
            return False, None, None

        # Now fetch employee info linked to this user
        user_data = users[0]
        user_email = user_data.get("email", username)

        emp_url = f"{ERP_URL}/api/resource/Employee"
        emp_response = requests.get(
            emp_url,
            headers={"Authorization": f"token {ERP_API_KEY}:{ERP_API_SECRET}"},
            params={
                "filters": [["Employee", "user_id", "=", user_email]],
                "fields": '["name", "employee_name", "attendance_device_id"]',
            },
            timeout=10,
        )

        emp_response.raise_for_status()
        employees = emp_response.json().get("data", [])

        if employees:
            emp = employees[0]
            employee_id = emp.get("attendance_device_id") or emp.get("name")
            employee_name = emp.get("employee_name", username)
            return True, employee_id, employee_name

        # User exists in ERP but no employee record
        return True, username, user_email

    except Exception as exc:
        print(f"ERP authentication error: {exc}")
        return False, None, None


def create_session(employee_id, employee_name, user_id):
    """Create a new session token for authenticated user."""
    token = secrets.token_hex(32)
    SESSIONS[token] = {
        "employee_id": str(employee_id),
        "employee_name": employee_name,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
    }
    return token


def get_session(token):
    """Retrieve session data if valid and not expired."""
    if token not in SESSIONS:
        return None
    session = SESSIONS[token]
    # Check expiration (simplified)
    return session


def set_cookie_header(self, token):
    """Set session cookie in response."""
    cookie = SimpleCookie()
    cookie["auth_token"] = token
    cookie["auth_token"]["path"] = "/"
    cookie["auth_token"]["max-age"] = SESSION_TIMEOUT
    cookie["auth_token"]["httponly"] = True
    self.send_header("Set-Cookie", cookie.output(header="").strip())


def get_session_from_request(self):
    """Extract session token from cookies or headers."""
    cookies = self.headers.get("Cookie", "")
    if "auth_token=" in cookies:
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith("auth_token="):
                return part.split("=", 1)[1]
    return self.headers.get("X-Auth-Token")


def load_static_file(filename):
    """Load static file from www directory."""
    file_path = STATIC_DIR / filename
    if not file_path.exists():
        return None
    return file_path.read_bytes()


def load_checkins():
    if not REMOTE_CHECKIN_FILE.exists():
        return []
    try:
        with REMOTE_CHECKIN_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        if isinstance(payload, list):
            return payload
    except json.JSONDecodeError:
        pass
    return []


def save_checkins(records):
    REMOTE_CHECKIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REMOTE_CHECKIN_FILE.open("w", encoding="utf-8") as f:
        json.dump({"data": records}, f, indent=2, ensure_ascii=False)


def append_checkin(record):
    records = load_checkins()
    records.append(record)
    save_checkins(records)


class CheckinHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def serve_file(self, filename, content_type):
        content = load_static_file(filename)
        if content is None:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found")
            return
        self._set_headers(200, content_type)
        self.wfile.write(content)

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        token_from_url = query_params.get('token', [None])[0]

        if parsed_path.path in ("/", "/index.html"):
            # Check if user is logged in via cookie or URL token
            token = get_session_from_request(self) or token_from_url
            if token and get_session(token):
                return self.serve_file("index.html", "text/html")
            # Not logged in, redirect to login
            return self.serve_file("login.html", "text/html")

        if parsed_path.path == "/login.html":
            return self.serve_file("login.html", "text/html")

        if parsed_path.path.endswith("styles.css"):
            return self.serve_file("styles.css", "text/css")

        if parsed_path.path.endswith("app.js"):
            return self.serve_file("app.js", "application/javascript")

        if parsed_path.path.endswith("login.js"):
            return self.serve_file("login.js", "application/javascript")

        if parsed_path.path == "/logout":
            self._set_headers(200, "text/html")
            self.send_header("Set-Cookie", "auth_token=; path=/; max-age=0")
            html = '<html><body><h1>Logged out</h1><p><a href="/">Back to login</a></p></body></html>'
            self.wfile.write(html.encode("utf-8"))
            return

        if parsed_path.path.startswith("/remote_checkins"):
            # API endpoint: no auth required (for internal polling)
            self._set_headers(200, "application/json")
            data = load_checkins()
            self.wfile.write(json.dumps({"data": data}, indent=2).encode("utf-8"))
            return

        self._set_headers(404, "text/html")
        self.serve_file("404.html", "text/html")


    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.headers.get("Content-Type", "").startswith("application/json"):
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = {k: v[0] for k, v in parse_qs(body).items()}

        # Login endpoint
        if self.path == "/login":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()

            if not username or not password:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Missing username or password"}).encode("utf-8"))
                return

            # Authenticate with ERP
            success, employee_id, employee_name = authenticate_erp_user(username, password)
            if not success:
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode("utf-8"))
                return

            # Create session
            token = create_session(employee_id, employee_name, username)
            
            # Send response with Set-Cookie header
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            cookie = SimpleCookie()
            cookie["auth_token"] = token
            cookie["auth_token"]["path"] = "/"
            cookie["auth_token"]["max-age"] = str(SESSION_TIMEOUT)
            cookie["auth_token"]["httponly"] = True
            self.send_header("Set-Cookie", cookie.output(header="").strip())
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "token": token,
                "employee_id": employee_id,
                "employee_name": employee_name
            }).encode("utf-8"))
            return

        # Check-in endpoint: requires authentication
        if self.path == "/submit_checkin":
            token = get_session_from_request(self)
            session = get_session(token) if token else None

            if not session:
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Not authenticated. Please log in first."}
).encode("utf-8"))
                return

            # Use authenticated employee ID if not provided
            user_id = payload.get("user_id") or session.get("employee_id")
            timestamp = payload.get("timestamp")

            if not user_id:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Missing user_id"}).encode("utf-8"))
                return

            if timestamp:
                try:
                    timestamp_obj = datetime.fromisoformat(timestamp)
                except ValueError:
                    try:
                        timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        timestamp_obj = datetime.now()
                timestamp = timestamp_obj.isoformat()
            else:
                timestamp = datetime.now().isoformat()

            record = {
                "user_id": str(user_id),
                "timestamp": timestamp,
                "submitted_by": session.get("user_id"),
                "employee_name": session.get("employee_name"),
            }
            append_checkin(record)

            self._set_headers(201, "application/json")
            self.wfile.write(json.dumps({"status": "ok", "record": record}).encode("utf-8"))
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))



def run(server_class=HTTPServer, handler_class=CheckinHandler):
    server_address = ("", PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Remote check-in portal starting up...")
    print(f"  - Port: {PORT}")
    print(f"  - Static files: {STATIC_DIR}")
    print(f"  - Remote check-in file: {REMOTE_CHECKIN_FILE}")
    print(f"  - Access code required: {'Yes' if PORTAL_ACCESS_CODE else 'No'}")
    print(f"  - Portal URL: http://localhost:{PORT}/")
    print(f"  - API endpoint: http://localhost:{PORT}/remote_checkins")
    print("Server is running. Press Ctrl+C to stop.")
    httpd.serve_forever()


if __name__ == "__main__":
    run()

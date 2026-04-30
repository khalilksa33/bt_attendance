#!/usr/bin/env python3
import json
import os
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie
from datetime import datetime

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ADMIN_PORT = int(os.getenv("ADMIN_PORTAL_PORT", "5002"))
ADMIN_USERNAME = os.getenv("ADMIN_PORTAL_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PORTAL_PASSWORD", "ChangeMeSecurely")
STATIC_DIR = BASE_DIR / "www"
SETTINGS_FILE = BASE_DIR / "admin_settings.json"

# Session storage
ADMIN_SESSIONS = {}
SESSION_TIMEOUT = 3600


def load_settings():
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {
        "employees": [],
        "locations": ["Office", "Field", "Remote"],
        "default_location": os.getenv("DEFAULT_LOCATION", "Office"),
        "enable_location_tracking": os.getenv("ENABLE_LOCATION_TRACKING", "0") == "1",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }


def save_settings(data):
    data["last_updated"] = datetime.now().isoformat()
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def verify_admin_password(password):
    """Verify admin password (simple hash comparison)."""
    expected = ADMIN_PASSWORD
    return password == expected


def create_admin_session(username):
    """Create a new admin session token."""
    import secrets
    token = secrets.token_hex(32)
    ADMIN_SESSIONS[token] = {
        "username": username,
        "timestamp": datetime.now().isoformat(),
    }
    return token


def get_admin_session(token):
    """Retrieve admin session if valid."""
    if token not in ADMIN_SESSIONS:
        return None
    return ADMIN_SESSIONS[token]


def get_session_from_request(self):
    """Extract session token from cookies or headers."""
    cookies = self.headers.get("Cookie", "")
    if "admin_token=" in cookies:
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith("admin_token="):
                return part.split("=", 1)[1]
    return self.headers.get("X-Admin-Token")


class AdminHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Token")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/admin/login.html" or parsed_path.path == "/admin":
            self._set_headers(200, "text/html")
            html = """<!DOCTYPE html>
<html>
<head>
    <title>IICC Admin Portal - Login</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #333; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; color: #666; }
        input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #c00; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 20px; }
        button:hover { background: #900; }
        .message { text-align: center; margin: 15px 0; padding: 10px; border-radius: 4px; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h2>IICC Admin Portal</h2>
        <form id="loginForm">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
            <div id="message" class="message" style="display:none;"></div>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            
            try {
                const response = await fetch('/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                    credentials: 'include',
                });
                const data = await response.json();
                if (response.ok) {
                    window.location.href = '/admin/dashboard.html?token=' + data.token;
                } else {
                    messageDiv.textContent = data.error || 'Login failed';
                    messageDiv.className = 'message error';
                    messageDiv.style.display = 'block';
                }
            } catch (error) {
                messageDiv.textContent = 'Error: ' + error.message;
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())
            return

        if parsed_path.path == "/admin/dashboard.html":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(302, "text/html")
                self.send_header("Location", "/admin/login.html")
                self.end_headers()
                return

            self._set_headers(200, "text/html")
            html = """<!DOCTYPE html>
<html>
<head>
    <title>IICC Admin Dashboard</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; border-bottom: 2px solid #c00; padding-bottom: 10px; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { padding: 10px 20px; background: #c00; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 10px 5px 10px 0; }
        button:hover { background: #900; }
        .employee-list { list-style: none; padding: 0; }
        .employee-item { background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #c00; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        a { color: #007bff; text-decoration: none; cursor: pointer; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>IICC Admin Dashboard</h1>
        <div id="message"></div>
        
        <div class="card">
            <h2>Location Settings</h2>
            <div class="form-group">
                <label>Locations (comma-separated)</label>
                <textarea id="locations" rows="3"></textarea>
                <button onclick="saveLocations()">Save Locations</button>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="enableTracking"> Enable Location Tracking
                </label>
            </div>
        </div>

        <div class="card">
            <h2>Employee Location Assignment</h2>
            <div class="form-group">
                <label>Employee Name</label>
                <input type="text" id="empName" placeholder="e.g., Khalil Ahmad Yaqoob">
            </div>
            <div class="form-group">
                <label>Employee ID</label>
                <input type="text" id="empId" placeholder="e.g., 5">
            </div>
            <div class="form-group">
                <label>Assigned Location</label>
                <select id="empLocation"></select>
                <button onclick="assignEmployeeLocation()">Assign Location</button>
            </div>
        </div>

        <div class="card">
            <h2>Assigned Employees</h2>
            <ul class="employee-list" id="employeeList"></ul>
        </div>

        <div class="card">
            <button onclick="logout()" style="background: #999;">Logout</button>
        </div>
    </div>

    <script>
        const token = new URLSearchParams(window.location.search).get('token');
        
        async function loadSettings() {
            const response = await fetch('/admin/api/settings', {
                headers: { 'X-Admin-Token': token }
            });
            const settings = await response.json();
            document.getElementById('locations').value = settings.locations.join(', ');
            document.getElementById('enableTracking').checked = settings.enable_location_tracking;
            document.getElementById('empLocation').innerHTML = settings.locations.map(l => `<option>${l}</option>`).join('');
            loadEmployees();
        }

        async function loadEmployees() {
            const response = await fetch('/admin/api/settings', {
                headers: { 'X-Admin-Token': token }
            });
            const settings = await response.json();
            const list = document.getElementById('employeeList');
            list.innerHTML = settings.employees.map(e => `
                <li class="employee-item">
                    <strong>${e.name}</strong> (ID: ${e.employee_id}) → ${e.location}
                    <a onclick="removeEmployee('${e.employee_id}')" style="float: right; color: #c00;">Remove</a>
                </li>
            `).join('');
        }

        function saveLocations() {
            const locations = document.getElementById('locations').value.split(',').map(l => l.trim());
            const enableTracking = document.getElementById('enableTracking').checked;
            fetch('/admin/api/settings', {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Admin-Token': token 
                },
                body: JSON.stringify({ locations, enable_location_tracking: enableTracking })
            }).then(r => r.json()).then(data => {
                showMessage('Locations saved!', 'success');
                loadSettings();
            });
        }

        function assignEmployeeLocation() {
            const name = document.getElementById('empName').value;
            const empId = document.getElementById('empId').value;
            const location = document.getElementById('empLocation').value;
            
            if (!name || !empId || !location) {
                showMessage('Please fill all fields', 'error');
                return;
            }

            fetch('/admin/api/assign-employee', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Admin-Token': token 
                },
                body: JSON.stringify({ name, employee_id: empId, location })
            }).then(r => r.json()).then(data => {
                showMessage('Employee assigned!', 'success');
                document.getElementById('empName').value = '';
                document.getElementById('empId').value = '';
                loadEmployees();
            });
        }

        function removeEmployee(empId) {
            fetch('/admin/api/remove-employee/' + empId, {
                method: 'DELETE',
                headers: { 'X-Admin-Token': token }
            }).then(r => r.json()).then(data => {
                showMessage('Employee removed!', 'success');
                loadEmployees();
            });
        }

        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
        }

        function logout() {
            window.location.href = '/admin/login.html';
        }

        loadSettings();
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())
            return

        if parsed_path.path == "/admin/api/settings":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return

            self._set_headers(200, "application/json")
            settings = load_settings()
            self.wfile.write(json.dumps(settings).encode())
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            payload = json.loads(body)
        except:
            payload = {}

        parsed_path = urlparse(self.path)

        if parsed_path.path == "/admin/login":
            username = payload.get("username", "")
            password = payload.get("password", "")

            if username == ADMIN_USERNAME and verify_admin_password(password):
                token = create_admin_session(username)
                self._set_headers(200, "application/json")
                self.send_header("Set-Cookie", f"admin_token={token}; Path=/; Max-Age={SESSION_TIMEOUT}; HttpOnly")
                self.wfile.write(json.dumps({"status": "ok", "token": token}).encode())
            else:
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())
            return

        if parsed_path.path == "/admin/api/assign-employee":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return

            settings = load_settings()
            name = payload.get("name")
            emp_id = payload.get("employee_id")
            location = payload.get("location")

            if not name or not emp_id or not location:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Missing fields"}).encode())
                return

            settings["employees"] = [e for e in settings["employees"] if e["employee_id"] != emp_id]
            settings["employees"].append({"name": name, "employee_id": emp_id, "location": location})
            save_settings(settings)

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def do_PUT(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(body)

        token = get_session_from_request(self)
        if not token or not get_admin_session(token):
            self._set_headers(401, "application/json")
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        parsed_path = urlparse(self.path)
        if parsed_path.path == "/admin/api/settings":
            settings = load_settings()
            if "locations" in payload:
                settings["locations"] = payload["locations"]
            if "enable_location_tracking" in payload:
                settings["enable_location_tracking"] = payload["enable_location_tracking"]
            save_settings(settings)

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def do_DELETE(self):
        token = get_session_from_request(self)
        if not token or not get_admin_session(token):
            self._set_headers(401, "application/json")
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith("/admin/api/remove-employee/"):
            emp_id = parsed_path.path.split("/")[-1]
            settings = load_settings()
            settings["employees"] = [e for e in settings["employees"] if e["employee_id"] != emp_id]
            save_settings(settings)

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def log_message(self, format, *args):
        pass


def run(server_class=HTTPServer, handler_class=AdminHandler):
    server_address = ("", ADMIN_PORT)
    httpd = server_class(server_address, handler_class)
    print(f"IICC Admin Portal starting...")
    print(f"  - Port: {ADMIN_PORT}")
    print(f"  - Admin URL: http://localhost:{ADMIN_PORT}/admin/login.html")
    print(f"  - Username: {ADMIN_USERNAME}")
    print("Server is running. Press Ctrl+C to stop.")
    httpd.serve_forever()


if __name__ == "__main__":
    run()

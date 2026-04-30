#!/usr/bin/env python3
"""
Enhanced Admin Dashboard for IICC Attendance System
Manages remote field employee locations with real-time tracking
"""
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie
from datetime import datetime, timedelta
import threading

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ADMIN_PORT = int(os.getenv("ADMIN_PORTAL_PORT", "5002"))
ADMIN_USERNAME = os.getenv("ADMIN_PORTAL_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PORTAL_PASSWORD", "ChangeMeSecurely")
STATIC_DIR = BASE_DIR / "www"
SETTINGS_FILE = BASE_DIR / "admin_settings.json"
LOCATIONS_DB = BASE_DIR / "employee_locations.json"

# Session storage
ADMIN_SESSIONS = {}
SESSION_TIMEOUT = 3600


def load_settings():
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {
        "employees": [],
        "locations": ["Office", "Field Site A", "Field Site B", "Remote", "On Leave"],
        "default_location": "Office",
        "enable_location_tracking": True,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }


def save_settings(data):
    data["last_updated"] = datetime.now().isoformat()
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def load_locations():
    if LOCATIONS_DB.exists():
        return json.loads(LOCATIONS_DB.read_text())
    return {
        "employees": {},
        "check_ins": [],
        "last_updated": datetime.now().isoformat(),
    }


def save_locations(data):
    data["last_updated"] = datetime.now().isoformat()
    LOCATIONS_DB.write_text(json.dumps(data, indent=2))


def verify_admin_password(password):
    """Verify admin password."""
    return password == ADMIN_PASSWORD


def create_admin_session(username):
    """Create a new admin session token."""
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


class AdminDashboardHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="text/html"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Token")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def log_message(self, format, *args):
        """Suppress verbose HTTP logging."""
        return

    def do_GET(self):
        parsed_path = urlparse(self.path)

        # Serve login page
        if parsed_path.path in ["/admin", "/admin/", "/admin/login.html"]:
            self._set_headers(200, "text/html")
            self.wfile.write(self._get_login_html().encode())
            return

        # Serve main dashboard
        if parsed_path.path == "/admin/dashboard.html" or parsed_path.path == "/admin/dashboard":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(302)
                self.send_header("Location", "/admin/login.html")
                self.end_headers()
                return
            self._set_headers(200, "text/html")
            self.wfile.write(self._get_dashboard_html().encode())
            return

        # API endpoints
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

        if parsed_path.path == "/admin/api/locations":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return
            self._set_headers(200, "application/json")
            locations = load_locations()
            self.wfile.write(json.dumps(locations).encode())
            return

        if parsed_path.path == "/admin/api/dashboard-stats":
            token = get_session_from_request(self)
            if not token or not get_admin_session(token):
                self._set_headers(401, "application/json")
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return
            self._set_headers(200, "application/json")
            stats = self._get_dashboard_stats()
            self.wfile.write(json.dumps(stats).encode())
            return

        self._set_headers(404)
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        # Login endpoint
        if parsed_path.path == "/admin/login":
            try:
                data = json.loads(body)
                if verify_admin_password(data.get("password")) and data.get("username") == ADMIN_USERNAME:
                    token = create_admin_session(data["username"])
                    self._set_headers(200, "application/json")
                    self.wfile.write(json.dumps({"token": token, "success": True}).encode())
                else:
                    self._set_headers(401, "application/json")
                    self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # API endpoints
        token = get_session_from_request(self)
        if not token or not get_admin_session(token):
            self._set_headers(401, "application/json")
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        if parsed_path.path == "/admin/api/assign-employee":
            try:
                data = json.loads(body)
                settings = load_settings()
                # Add or update employee
                settings["employees"] = [e for e in settings["employees"] if e["employee_id"] != data["employee_id"]]
                settings["employees"].append({
                    "name": data["name"],
                    "employee_id": data["employee_id"],
                    "location": data["location"],
                    "assigned_at": datetime.now().isoformat(),
                })
                save_settings(settings)
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        if parsed_path.path == "/admin/api/check-in":
            try:
                data = json.loads(body)
                locations = load_locations()
                locations["employees"][data["employee_id"]] = {
                    "name": data.get("name", "Unknown"),
                    "location": data["location"],
                    "checked_in_at": datetime.now().isoformat(),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                }
                locations["check_ins"].append({
                    "employee_id": data["employee_id"],
                    "name": data.get("name", "Unknown"),
                    "location": data["location"],
                    "timestamp": datetime.now().isoformat(),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                })
                save_locations(locations)
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self._set_headers(404)
        self.wfile.write(b"Not Found")

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        token = get_session_from_request(self)
        if not token or not get_admin_session(token):
            self._set_headers(401, "application/json")
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        if parsed_path.path == "/admin/api/settings":
            try:
                data = json.loads(body)
                settings = load_settings()
                settings.update(data)
                save_settings(settings)
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self._set_headers(404)
        self.wfile.write(b"Not Found")

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        token = get_session_from_request(self)
        if not token or not get_admin_session(token):
            self._set_headers(401, "application/json")
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        if parsed_path.path == "/admin/api/employee":
            try:
                emp_id = query_params.get("id", [""])[0]
                settings = load_settings()
                settings["employees"] = [e for e in settings["employees"] if e["employee_id"] != emp_id]
                save_settings(settings)
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self._set_headers(404)
        self.wfile.write(b"Not Found")

    def _get_login_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IICC Admin Dashboard - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            width: 100%;
            max-width: 400px;
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #333; font-size: 24px; }
        .logo p { color: #666; font-size: 14px; margin-top: 5px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #333; font-weight: 600; margin-bottom: 8px; }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .message {
            margin-top: 15px;
            padding: 12px;
            border-radius: 5px;
            text-align: center;
            display: none;
        }
        .error { background: #fee; color: #c33; }
        .success { background: #efe; color: #3c3; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>IICC Admin</h1>
            <p>Employee Location Dashboard</p>
        </div>
        <form id="loginForm">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">Login to Dashboard</button>
            <div id="message" class="message"></div>
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
                });
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem('adminToken', data.token);
                    window.location.href = '/admin/dashboard?token=' + data.token;
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

    def _get_dashboard_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IICC Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        header h1 { font-size: 24px; }
        .logout-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid white;
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .logout-btn:hover { background: rgba(255, 255, 255, 0.3); }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        .stat-card h3 { color: #667eea; font-size: 14px; text-transform: uppercase; margin-bottom: 10px; }
        .stat-card .number { font-size: 32px; font-weight: bold; color: #333; }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 6px;
        }
        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .employee-list {
            list-style: none;
            max-height: 300px;
            overflow-y: auto;
        }
        .employee-item {
            background: #f9f9f9;
            padding: 12px;
            margin: 8px 0;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .employee-item strong { color: #333; }
        .employee-item .location { color: #666; font-size: 13px; }
        .remove-btn {
            background: #ff6b6b;
            padding: 5px 10px;
            font-size: 12px;
        }
        .remove-btn:hover { background: #ff5252; }
        .message {
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 15px;
            display: none;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
            header { flex-direction: column; gap: 15px; text-align: center; }
        }
    </style>
</head>
<body>
    <header>
        <h1>🎯 IICC Employee Location Dashboard</h1>
        <button class="logout-btn" onclick="logout()">Logout</button>
    </header>
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Employees</h3>
                <div class="number" id="totalEmployees">0</div>
            </div>
            <div class="stat-card">
                <h3>Checked In Today</h3>
                <div class="number" id="checkedInToday">0</div>
            </div>
            <div class="stat-card">
                <h3>Field Locations</h3>
                <div class="number" id="fieldLocations">0</div>
            </div>
            <div class="stat-card">
                <h3>Last Update</h3>
                <div class="number" id="lastUpdate" style="font-size: 14px;">--:--</div>
            </div>
        </div>

        <div class="main-grid">
            <div class="card">
                <h2>📍 Assign Employee Location</h2>
                <div id="assignMessage" class="message"></div>
                <div class="form-group">
                    <label>Employee Name</label>
                    <input type="text" id="empName" placeholder="e.g., Ahmed Hassan">
                </div>
                <div class="form-group">
                    <label>Employee ID</label>
                    <input type="text" id="empId" placeholder="e.g., 5">
                </div>
                <div class="form-group">
                    <label>Primary Location</label>
                    <select id="empLocation"></select>
                </div>
                <button onclick="assignEmployee()" style="width: 100%;">Assign Location</button>
            </div>

            <div class="card">
                <h2>⚙️ Location Settings</h2>
                <div id="settingsMessage" class="message"></div>
                <div class="form-group">
                    <label>Available Locations</label>
                    <textarea id="locations" rows="4" placeholder="One location per line"></textarea>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="enableTracking">
                        Enable Real-time Location Tracking
                    </label>
                </div>
                <button onclick="saveSettings()" style="width: 100%;">Save Settings</button>
            </div>
        </div>

        <div class="card" style="margin-top: 20px;">
            <h2>👥 Assigned Employees</h2>
            <ul class="employee-list" id="employeeList">
                <li class="employee-item">Loading...</li>
            </ul>
        </div>
    </div>

    <script>
        const token = new URLSearchParams(window.location.search).get('token') || localStorage.getItem('adminToken');
        
        if (!token) {
            window.location.href = '/admin/login.html';
        }

        async function loadSettings() {
            try {
                const response = await fetch('/admin/api/settings', {
                    headers: { 'X-Admin-Token': token }
                });
                const settings = await response.json();
                document.getElementById('locations').value = settings.locations.join('\\n');
                document.getElementById('enableTracking').checked = settings.enable_location_tracking || false;
                document.getElementById('empLocation').innerHTML = settings.locations.map(l => `<option>${l}</option>`).join('');
                document.getElementById('totalEmployees').textContent = settings.employees.length;
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }

        async function loadLocations() {
            try {
                const response = await fetch('/admin/api/locations', {
                    headers: { 'X-Admin-Token': token }
                });
                const data = await response.json();
                
                const now = new Date(data.last_updated);
                document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
                
                const list = document.getElementById('employeeList');
                const employees = Object.values(data.employees || {});
                
                if (employees.length === 0) {
                    list.innerHTML = '<li class="employee-item">No check-ins yet</li>';
                } else {
                    list.innerHTML = employees.map(e => `
                        <li class="employee-item">
                            <div>
                                <strong>${e.name}</strong>
                                <div class="location">📍 ${e.location}</div>
                            </div>
                            <div style="text-align: right; font-size: 12px; color: #999;">
                                ${new Date(e.checked_in_at).toLocaleTimeString()}
                            </div>
                        </li>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading locations:', error);
            }
        }

        async function assignEmployee() {
            const name = document.getElementById('empName').value;
            const empId = document.getElementById('empId').value;
            const location = document.getElementById('empLocation').value;
            const messageDiv = document.getElementById('assignMessage');
            
            if (!name || !empId || !location) {
                showMessage(messageDiv, 'Please fill all fields', 'error');
                return;
            }

            try {
                const response = await fetch('/admin/api/assign-employee', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Admin-Token': token
                    },
                    body: JSON.stringify({ name, employee_id: empId, location })
                });
                if (response.ok) {
                    showMessage(messageDiv, 'Employee assigned successfully!', 'success');
                    document.getElementById('empName').value = '';
                    document.getElementById('empId').value = '';
                    loadSettings();
                } else {
                    showMessage(messageDiv, 'Failed to assign employee', 'error');
                }
            } catch (error) {
                showMessage(messageDiv, 'Error: ' + error.message, 'error');
            }
        }

        async function saveSettings() {
            const locations = document.getElementById('locations').value.split('\\n').map(l => l.trim()).filter(l => l);
            const enableTracking = document.getElementById('enableTracking').checked;
            const messageDiv = document.getElementById('settingsMessage');

            try {
                const response = await fetch('/admin/api/settings', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Admin-Token': token
                    },
                    body: JSON.stringify({ locations, enable_location_tracking: enableTracking })
                });
                if (response.ok) {
                    showMessage(messageDiv, 'Settings saved successfully!', 'success');
                    loadSettings();
                } else {
                    showMessage(messageDiv, 'Failed to save settings', 'error');
                }
            } catch (error) {
                showMessage(messageDiv, 'Error: ' + error.message, 'error');
            }
        }

        function showMessage(element, text, type) {
            element.textContent = text;
            element.className = 'message ' + type;
            element.style.display = 'block';
            setTimeout(() => {
                element.style.display = 'none';
            }, 4000);
        }

        function logout() {
            localStorage.removeItem('adminToken');
            window.location.href = '/admin/login.html';
        }

        // Initial load
        loadSettings();
        loadLocations();
        
        // Refresh data every 30 seconds
        setInterval(loadLocations, 30000);
    </script>
</body>
</html>"""

    def _get_dashboard_stats(self):
        try:
            settings = load_settings()
            locations = load_locations()
            today = datetime.now().date()
            
            today_checkins = [
                c for c in locations.get("check_ins", [])
                if datetime.fromisoformat(c["timestamp"]).date() == today
            ]
            
            return {
                "total_employees": len(settings.get("employees", [])),
                "checked_in_today": len(set(c["employee_id"] for c in today_checkins)),
                "total_locations": len(settings.get("locations", [])),
                "check_ins_today": len(today_checkins),
                "active_employees": len(locations.get("employees", {})),
                "last_updated": locations.get("last_updated"),
            }
        except Exception as e:
            return {"error": str(e)}


def run_server():
    """Run the admin dashboard server."""
    server = HTTPServer(("0.0.0.0", ADMIN_PORT), AdminDashboardHandler)
    print(f"🚀 IICC Admin Dashboard running on http://0.0.0.0:{ADMIN_PORT}")
    print(f"📍 Access at http://localhost:{ADMIN_PORT}/admin")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n✋ Server stopped")
        server.shutdown()


if __name__ == "__main__":
    run_server()

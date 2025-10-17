
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import cgi
import os
import pandas as pd
from datetime import datetime, timedelta
import signal
import sys
import time
import csv
import shutil
import io
import math
import threading
import uuid

# -------------------------
# Helper functions (global)
# -------------------------

REMINDERS_FILE = "reminders.json"
MOTIVATION_FILE = "motivation.json"
NOTIFICATION_SETTINGS_FILE = "notification_settings.json"
REMINDER_CHECK_INTERVAL = 30  # seconds


def load_json_file(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return default
    except Exception:
        return default


def save_json_file(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save {path}: {e}")
        return False


def send_notification(title, text):
    """
    Try to send a notification using termux-notification, else notify-send, else print.
    """
    # Check if notifications are enabled
    settings = load_json_file(NOTIFICATION_SETTINGS_FILE, {"enabled": True})
    if not settings.get("enabled", True):
        print(f"Notifications disabled - would send: {title}: {text}")
        return False
        
    try:
        # Termux notification
        cmd = ["termux-notification", "--title", title, "--content", text]
        subprocess.run(cmd, capture_output=True, timeout=8)
        return True
    except Exception:
        try:
            # Linux notify-send (common on desktops)
            cmd = ["notify-send", title, text]
            subprocess.run(cmd, capture_output=True, timeout=8)
            return True
        except Exception:
            # Fallback: print (server log)
            print(f"NOTIFICATION - {title}: {text}")
            return False


def parse_date_time(date_str, time_str):
    """
    Parse date in YYYY-MM-DD and time in HH:MM and return a datetime.
    """
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        return dt
    except Exception:
        return None


def next_weekly_run(from_dt, weekday_target, hour_minute):
    """
    Compute next datetime for weekly recurrence.
    weekday_target: 0=Monday .. 6=Sunday (as Python weekday)
    hour_minute: "HH:MM"
    """
    try:
        h, m = map(int, hour_minute.split(":"))
        # start from midnight of current day (keep time)
        base = from_dt.replace(hour=h, minute=m, second=0, microsecond=0)
        days_ahead = (weekday_target - base.weekday() + 7) % 7
        if days_ahead == 0 and base <= from_dt:
            days_ahead = 7
        return base + timedelta(days=days_ahead)
    except Exception:
        return None


def get_next_occurrence(reminder):
    """
    Compute next occurrence datetime for a reminder dict.
    reminder keys: id, title, message, date (YYYY-MM-DD) or empty, time (HH:MM), recurrence (once/daily/weekly),
    weekday (0..6) for weekly, last_sent (iso) optional.
    Returns a datetime or None if not computable.
    """
    now = datetime.now()
    recurrence = reminder.get("recurrence", "once")
    time_str = reminder.get("time", "09:00")
    if recurrence == "once":
        date_str = reminder.get("date")
        if not date_str:
            return None
        dt = parse_date_time(date_str, time_str)
        return dt
    elif recurrence == "daily":
        # next today at time if still in future, else tomorrow
        try:
            h, m = map(int, time_str.split(":"))
            candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        except Exception:
            return None
    elif recurrence == "weekly":
        # if weekday provided, compute next weekly occurrence
        weekday = reminder.get("weekday")
        if weekday is None:
            return None
        try:
            weekday = int(weekday)
            return next_weekly_run(now, weekday, time_str)
        except Exception:
            return None
    else:
        return None


def should_send_reminder(reminder):
    """
    Determine if reminder should be sent now.
    Uses last_sent to avoid repeats within 60 seconds.
    """
    try:
        next_dt = get_next_occurrence(reminder)
        if not next_dt:
            return False
        now = datetime.now()
        # Allow small window: send if next_dt <= now < next_dt + 60s
        if next_dt <= now <= (next_dt + timedelta(seconds=60)):
            last_sent = reminder.get("last_sent")
            if last_sent:
                try:
                    last_dt = datetime.fromisoformat(last_sent)
                    # if already sent within the last minute, skip
                    if (now - last_dt).total_seconds() < 60:
                        return False
                except Exception:
                    pass
            return True
        return False
    except Exception:
        return False


def mark_reminder_sent(reminder):
    reminder["last_sent"] = datetime.now().isoformat()


def reminders_loop_stop_flag():
    # Small helper to check if server stopped: file-based sentinel not used here.
    return False


def reminders_background_loop():
    """
    Background thread: loops and checks reminders and motivation triggers.
    """
    while True:
        try:
            reminders = load_json_file(REMINDERS_FILE, [])
            changed = False
            for r in reminders:
                try:
                    if should_send_reminder(r):
                        title = r.get("title", "Reminder")
                        message = r.get("message", "")
                        send_notification(title, message)
                        mark_reminder_sent(r)
                        changed = True
                        # For 'once' reminders, mark as sent (we keep it but set sent=True to avoid repetition)
                        if r.get("recurrence", "once") == "once":
                            r["sent"] = True
                except Exception as e:
                    print(f"Error handling reminder {r.get('id')}: {e}")
            if changed:
                save_json_file(REMINDERS_FILE, reminders)
        except Exception as e:
            print("Reminders loop error:", e)

        # Motivation engine
        try:
            config = load_json_file(MOTIVATION_FILE, {"enabled": False, "interval_minutes": 240, "messages": [], "last_sent": None})
            if config.get("enabled"):
                last = config.get("last_sent")
                interval_min = int(config.get("interval_minutes", 240) or 240)
                now = datetime.now()
                send_now = False
                if last:
                    try:
                        last_dt = datetime.fromisoformat(last)
                        if (now - last_dt).total_seconds() >= interval_min * 60:
                            send_now = True
                    except Exception:
                        send_now = True
                else:
                    send_now = True
                if send_now:
                    msgs = config.get("messages", [])
                    if msgs:
                        # Pick next message in rotation
                        idx = config.get("last_index", 0)
                        message = msgs[idx % len(msgs)]
                        title = "Motivation"
                        send_notification(title, message)
                        config["last_sent"] = now.isoformat()
                        config["last_index"] = idx + 1
                        save_json_file(MOTIVATION_FILE, config)
        except Exception as e:
            print("Motivation loop error:", e)

        time.sleep(REMINDER_CHECK_INTERVAL)


# start background thread
bg_thread = threading.Thread(target=reminders_background_loop, daemon=True)
bg_thread.start()

# -------------------------
# HTTP Handler (main)
# -------------------------

class LifeTrackerHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/get_reminders':
            self.get_reminders()
            return
        elif self.path == '/get_motivation_settings':
            self.get_motivation_settings()
            return
        elif self.path == '/get_notification_settings':
            self.get_notification_settings()
            return
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        # New endpoints for reminders and motivation
        if self.path == '/save_reminder':
            self.save_reminder()
        elif self.path == '/delete_reminder':
            self.delete_reminder()
        elif self.path == '/save_motivation_settings':
            self.save_motivation_settings()
        elif self.path == '/trigger_test_notification':
            self.trigger_test_notification()
        elif self.path == '/save_notification_settings':
            self.save_notification_settings()
        else:
            self.send_error(404, "Endpoint not found")
    
    # -----------------------
    # Reminder & Motivation handlers
    # -----------------------
    
    def get_reminders(self):
        try:
            reminders = load_json_file(REMINDERS_FILE, [])
            # Return reminders JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "reminders": reminders}).encode())
        except Exception as e:
            self.send_error_response(f"Failed to load reminders: {e}")
    
    def save_reminder(self):
        """
        POST expects JSON body with fields:
        id (optional) - to update existing
        title
        message
        date YYYY-MM-DD (for once) - optional for recurring
        time HH:MM
        recurrence: once/daily/weekly
        weekday: 0-6 if weekly (optional)
        """
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            reminders = load_json_file(REMINDERS_FILE, [])
            
            rid = data.get('id')
            if rid:
                # update existing
                found = False
                for i, r in enumerate(reminders):
                    if r.get('id') == rid:
                        reminders[i].update(data)
                        reminders[i].pop('sent', None)  # reset sent flag if changed
                        found = True
                        break
                if not found:
                    reminders.append(data)
            else:
                data['id'] = str(uuid.uuid4())
                data.setdefault('time', '09:00')
                data.setdefault('recurrence', 'once')
                data['created_at'] = datetime.now().isoformat()
                reminders.append(data)
            
            save_json_file(REMINDERS_FILE, reminders)
            self.send_success_response("Reminder saved successfully")
        except Exception as e:
            self.send_error_response(f"Error saving reminder: {e}")
    
    def delete_reminder(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            rid = data.get('id')
            if not rid:
                self.send_error_response("Missing reminder id")
                return
            reminders = load_json_file(REMINDERS_FILE, [])
            reminders = [r for r in reminders if r.get('id') != rid]
            save_json_file(REMINDERS_FILE, reminders)
            self.send_success_response("Reminder deleted")
        except Exception as e:
            self.send_error_response(f"Error deleting reminder: {e}")
    
    def get_motivation_settings(self):
        try:
            config = load_json_file(MOTIVATION_FILE, {"enabled": False, "interval_minutes": 240, "messages": []})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "config": config}).encode())
        except Exception as e:
            self.send_error_response(f"Failed to load motivation settings: {e}")
    
    def save_motivation_settings(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            # Expected: enabled (bool), interval_minutes (int), messages (list of strings)
            cfg = {
                "enabled": bool(data.get("enabled", False)),
                "interval_minutes": int(data.get("interval_minutes", 240) or 240),
                "messages": data.get("messages", []),
                "last_sent": None,
                "last_index": 0
            }
            save_json_file(MOTIVATION_FILE, cfg)
            self.send_success_response("Motivation settings saved")
        except Exception as e:
            self.send_error_response(f"Error saving motivation settings: {e}")
    
    def trigger_test_notification(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            title = data.get('title', 'Test Notification')
            message = data.get('message', 'This is a test')
            ok = send_notification(title, message)
            if ok:
                self.send_success_response("Test notification sent")
            else:
                self.send_error_response("Notification command not available; check Termux or system tools")
        except Exception as e:
            self.send_error_response(f"Error sending test notification: {e}")
    
    def get_notification_settings(self):
        try:
            settings = load_json_file(NOTIFICATION_SETTINGS_FILE, {"enabled": True})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "settings": settings}).encode())
        except Exception as e:
            self.send_error_response(f"Failed to load notification settings: {e}")
    
    def save_notification_settings(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            settings = {
                "enabled": bool(data.get("enabled", True))
            }
            save_json_file(NOTIFICATION_SETTINGS_FILE, settings)
            self.send_success_response("Notification settings saved")
        except Exception as e:
            self.send_error_response(f"Error saving notification settings: {e}")
    
    # -----------------------
    # Utility response helpers
    # -----------------------
    def send_success_response(self, message):
        """Helper method for sending success responses"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "success",
            "message": message
        }).encode())
    
    def send_error_response(self, error_message):
        """Helper method for sending error responses"""
        self.send_response(200)  # Using 200 to handle errors in frontend
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "error",
            "message": error_message
        }).encode())

# -------------------------
# HTML UI - Only Notification, Reminders, and Motivation sections
# -------------------------
html_content = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Notification Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --primary-color: #007AFF;
            --primary-dark: #0056CC;
            --secondary-color: #5856D6;
            --danger-color: #FF3B30;
            --success-color: #34C759;
            --gray-color: #8E8E93;
            --radius: 12px;
            --card-bg: rgba(255,255,255,0.9);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: rgba(255,255,255,0.85);
            padding: 24px;
            border-radius: var(--radius);
        }
        h1 { text-align: center; color: #1D1D1F; margin-bottom: 12px; }
        .section { 
            background: var(--card-bg); 
            padding: 18px; 
            border-radius: 10px; 
            margin: 18px 0; 
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .section.collapsed {
            max-height: 70px;
            padding: 15px 18px;
        }
        .section-content {
            transition: all 0.3s ease;
        }
        .section.collapsed .section-content {
            display: none;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding-bottom: 12px;
            margin-bottom: 15px;
            border-bottom: 2px solid rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 1.3em;
            font-weight: 600;
            color: #1D1D1F;
        }
        .collapse-btn {
            background: var(--gray-color);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 12px;
        }
        .centered-controls { display:flex; gap:12px; flex-wrap:wrap; justify-content:center; }
        input, select, button, textarea { 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid rgba(0,0,0,0.08); 
            font-size: 16px;
            width: 100%;
            box-sizing: border-box;
        }
        button { 
            background: var(--primary-color); 
            color: white; 
            border: none; 
            cursor: pointer; 
            transition: background 0.3s;
        }
        button:hover { background: var(--primary-dark); }
        .button-muted { background: #6c757d; }
        .button-muted:hover { background: #5a6268; }
        .small { padding:8px 10px; font-size:14px; }
        .list { margin-top:12px; }
        .list-item { 
            padding:10px; 
            border-radius:8px; 
            background:white; 
            margin-bottom:8px; 
            display:flex; 
            justify-content:space-between; 
            align-items:center;
            flex-wrap: wrap;
        }
        .list-actions { 
            display: flex; 
            gap: 8px; 
            margin-top: 8px;
            width: 100%;
        }
        .list-actions button { margin-left:0; }
        .result { 
            margin-top:10px; 
            padding:12px; 
            border-radius:8px; 
            background:white; 
            border-left: 4px solid var(--primary-color);
        }
        .notification-card { 
            background: white; 
            padding: 16px; 
            border-radius: 12px; 
            margin: 12px 0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid var(--primary-color);
        }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .toggle-slider {
            background-color: var(--success-color);
        }
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .card-title {
            font-weight: 600;
            font-size: 16px;
            color: #1D1D1F;
        }
        .card-description {
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
        }
        .button-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .button-row button {
            flex: 1;
            min-width: 120px;
        }
        .form-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        .form-row input, .form-row select {
            flex: 1;
            min-width: 150px;
        }
        .mobile-full {
            width: 100%;
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            .section {
                padding: 15px;
                margin: 12px 0;
            }
            .section.collapsed {
                padding: 12px 15px;
                max-height: 60px;
            }
            .form-row {
                flex-direction: column;
            }
            .form-row input, .form-row select {
                min-width: 100%;
            }
            .button-row {
                flex-direction: column;
            }
            .button-row button {
                min-width: 100%;
            }
            .list-item {
                flex-direction: column;
                align-items: flex-start;
            }
            .list-actions {
                justify-content: flex-start;
            }
        }

        @media (max-width: 480px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 12px;
            }
            .section {
                padding: 12px;
            }
            .section.collapsed {
                padding: 10px 12px;
                max-height: 55px;
            }
            h1 {
                font-size: 1.5em;
            }
            .section-title {
                font-size: 1.1em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Notification Manager</h1>

        <!-- Global Controls -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">Quick Actions</div>
            </div>
            <div class="section-content">
                <div class="button-row">
                    <button onclick="expandAllSections()">Expand All</button>
                    <button onclick="collapseAllSections()" class="button-muted">Collapse All</button>
                </div>
            </div>
        </div>

        <!-- Notification Settings Card -->
        <div class="section" id="notificationSettingsSection">
            <div class="section-header" onclick="toggleSection('notificationSettingsSection')">
                <div class="section-title">Notification Settings</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <div class="notification-card">
                    <div class="card-header">
                        <div class="card-title">Enable Notifications</div>
                        <label class="toggle-switch">
                            <input type="checkbox" id="notificationToggle">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="card-description">
                        Turn on/off all notifications including reminders and motivational messages. 
                        When disabled, no notifications will be sent to your device.
                    </div>
                    <button onclick="saveNotificationSettings()" class="small mobile-full">Save Settings</button>
                </div>
                <div id="notificationResult" class="result" style="display:none;"></div>
            </div>
        </div>

        <!-- Reminders Section -->
        <div class="section" id="remindersSection">
            <div class="section-header" onclick="toggleSection('remindersSection')">
                <div class="section-title">Reminders</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <div class="form-row">
                    <input type="text" id="remTitle" placeholder="Reminder title" class="mobile-full">
                    <input type="date" id="remDate" placeholder="Date (for once)" class="mobile-full">
                    <input type="time" id="remTime" value="09:00" class="mobile-full">
                </div>
                <div class="form-row">
                    <select id="remRecurrence" class="mobile-full">
                        <option value="once">Once</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                    </select>
                    <select id="remWeekday" style="display:none;" class="mobile-full">
                        <option value="0">Monday</option>
                        <option value="1">Tuesday</option>
                        <option value="2">Wednesday</option>
                        <option value="3">Thursday</option>
                        <option value="4">Friday</option>
                        <option value="5">Saturday</option>
                        <option value="6">Sunday</option>
                    </select>
                </div>
                <div class="form-row">
                    <input type="text" id="remMessage" placeholder="Message" class="mobile-full">
                </div>
                
                <div class="button-row">
                    <button onclick="saveReminder()" class="small mobile-full">Save Reminder</button>
                    <button onclick="loadReminders()" class="small button-muted mobile-full">Refresh List</button>
                    <button onclick="testNotification()" class="small mobile-full">Test Notification</button>
                </div>

                <div id="remindersList" class="list"></div>
                <div id="remindersResult" class="result" style="display:none;"></div>
            </div>
        </div>

        <!-- Motivation Section -->
        <div class="section" id="motivationSection">
            <div class="section-header" onclick="toggleSection('motivationSection')">
                <div class="section-title">Motivational Notifications</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <div class="form-row">
                    <label style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" id="motEnable">
                        Enable Motivational Messages
                    </label>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>Interval:</span>
                        <input type="number" id="motInterval" min="10" value="240" style="width: 80px;">
                        <span>minutes</span>
                    </div>
                </div>

                <div style="margin-top:8px;">
                    <textarea id="motMessages" rows="4" style="width:100%; padding: 10px;" placeholder="Enter motivational messages, one per line"></textarea>
                </div>
                
                <div class="button-row">
                    <button onclick="saveMotivationSettings()" class="small mobile-full">Save Settings</button>
                    <button onclick="loadMotivationSettings()" class="small button-muted mobile-full">Load Settings</button>
                    <button onclick="sendImmediateMotivation()" class="small mobile-full">Send Now</button>
                </div>
                
                <div id="motivationResult" class="result" style="display:none;"></div>
            </div>
        </div>

    </div>

<script>
    // Section collapse functionality
    function toggleSection(sectionId) {
        const section = document.getElementById(sectionId);
        section.classList.toggle('collapsed');
    }

    function expandAllSections() {
        document.querySelectorAll('.section.collapsed').forEach(section => {
            section.classList.remove('collapsed');
        });
    }

    function collapseAllSections() {
        document.querySelectorAll('.section:not(.collapsed)').forEach(section => {
            section.classList.add('collapsed');
        });
    }

    // Auto-collapse all sections on load
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            collapseAllSections();
        }, 100);
    });

    // Notification Settings Functions
    async function loadNotificationSettings() {
        try {
            const resp = await fetch('/get_notification_settings');
            const j = await resp.json();
            if (j.status === 'success') {
                const settings = j.settings || {};
                document.getElementById('notificationToggle').checked = settings.enabled !== false;
            }
        } catch (e) {
            console.error('Error loading notification settings:', e);
        }
    }

    async function saveNotificationSettings() {
        const enabled = document.getElementById('notificationToggle').checked;
        try {
            const resp = await fetch('/save_notification_settings', {
                method: 'POST',
                body: JSON.stringify({ enabled })
            });
            const j = await resp.json();
            const res = document.getElementById('notificationResult');
            res.style.display = 'block';
            res.textContent = j.message || (j.status === 'success' ? 'Settings saved' : 'Failed to save');
            res.style.backgroundColor = j.status === 'success' ? '#d4edda' : '#f8d7da';
            res.style.color = j.status === 'success' ? '#155724' : '#721c24';
            setTimeout(() => res.style.display = 'none', 3000);
        } catch (e) {
            console.error('Error saving notification settings:', e);
        }
    }

    // Reminder Functions
    async function loadReminders(){
        try {
            const resp = await fetch('/get_reminders');
            const j = await resp.json();
            if (j.status === 'success') {
                const list = document.getElementById('remindersList');
                list.innerHTML = '';
                (j.reminders || []).forEach(r => {
                    const el = document.createElement('div');
                    el.className = 'list-item';
                    el.innerHTML = `
                        <div style="flex:1;">
                            <div><strong>${r.title || '(no title)'}</strong> ${r.recurrence === 'once' && r.date ? ('on ' + r.date) : ''}</div>
                            <div style="font-size:13px; color:#666;">${r.time || ''} • ${r.recurrence || ''}${r.weekday !== undefined ? ' • ' + ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][r.weekday] : ''}</div>
                            <div style="font-size:14px; margin-top:6px;">${r.message || ''}</div>
                        </div>
                        <div class="list-actions">
                            <button onclick="editReminder('${r.id}')" class="small button-muted">Edit</button>
                            <button onclick="deleteReminder('${r.id}')" class="small" style="background:${'#FF3B30'}">Delete</button>
                        </div>
                    `;
                    list.appendChild(el);
                });
            }
        } catch (e) {
            console.error(e);
        }
    }

    document.getElementById('remRecurrence').addEventListener('change', function() {
        const val = this.value;
        const weekday = document.getElementById('remWeekday');
        if (val === 'weekly') {
            weekday.style.display = 'block';
            weekday.classList.add('mobile-full');
        } else {
            weekday.style.display = 'none';
        }
    });

    async function saveReminder(){
        const title = document.getElementById('remTitle').value;
        const date = document.getElementById('remDate').value;
        const time = document.getElementById('remTime').value;
        const recurrence = document.getElementById('remRecurrence').value;
        const weekday = document.getElementById('remWeekday').value;
        const message = document.getElementById('remMessage').value;

        const payload = {
            title, date, time, recurrence, message
        };
        if (recurrence === 'weekly') payload.weekday = parseInt(weekday);

        try {
            const resp = await fetch('/save_reminder', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            const j = await resp.json();
            const res = document.getElementById('remindersResult');
            res.style.display = 'block';
            if (j.status === 'success') {
                res.textContent = j.message;
                res.style.backgroundColor = '#d4edda';
                res.style.color = '#155724';
                loadReminders();
                // Clear form
                document.getElementById('remTitle').value = '';
                document.getElementById('remDate').value = '';
                document.getElementById('remMessage').value = '';
            } else {
                res.textContent = j.message || 'Failed';
                res.style.backgroundColor = '#f8d7da';
                res.style.color = '#721c24';
            }
            setTimeout(()=>res.style.display='none', 4000);
        } catch (e) {
            console.error(e);
        }
    }

    async function deleteReminder(id){
        if (!confirm('Delete this reminder?')) return;
        try {
            const resp = await fetch('/delete_reminder', {
                method: 'POST',
                body: JSON.stringify({id})
            });
            const j = await resp.json();
            if (j.status === 'success') {
                loadReminders();
            } else {
                alert('Failed: ' + (j.message || ''));
            }
        } catch (e) { console.error(e); }
    }

    async function editReminder(id){
        try {
            const resp = await fetch('/get_reminders');
            const j = await resp.json();
            if (j.status === 'success') {
                const r = (j.reminders || []).find(x=>x.id===id);
                if (!r) return;
                document.getElementById('remTitle').value = r.title || '';
                document.getElementById('remDate').value = r.date || '';
                document.getElementById('remTime').value = r.time || '09:00';
                document.getElementById('remRecurrence').value = r.recurrence || 'once';
                if (r.recurrence === 'weekly') {
                    document.getElementById('remWeekday').style.display = 'block';
                    document.getElementById('remWeekday').classList.add('mobile-full');
                    document.getElementById('remWeekday').value = r.weekday || 0;
                } else {
                    document.getElementById('remWeekday').style.display = 'none';
                }
                document.getElementById('remMessage').value = r.message || '';
                document.getElementById('remindersList').setAttribute('data-edit-id', id);
            }
        } catch (e) { console.error(e); }
    }

    async function testNotification(){
        const title = document.getElementById('remTitle').value || 'Test';
        const message = document.getElementById('remMessage').value || 'This is a test notification';
        try {
            const resp = await fetch('/trigger_test_notification', {
                method: 'POST',
                body: JSON.stringify({title, message})
            });
            const j = await resp.json();
            const res = document.getElementById('remindersResult');
            res.style.display = 'block';
            res.textContent = j.message || (j.status === 'success' ? 'Test notification sent' : 'Failed to send');
            res.style.backgroundColor = j.status === 'success' ? '#d4edda' : '#f8d7da';
            res.style.color = j.status === 'success' ? '#155724' : '#721c24';
            setTimeout(()=>res.style.display='none', 3500);
        } catch (e) { console.error(e); }
    }

    // Motivation UI
    async function loadMotivationSettings(){
        try {
            const resp = await fetch('/get_motivation_settings');
            const j = await resp.json();
            if (j.status === 'success') {
                const cfg = j.config || {};
                document.getElementById('motEnable').checked = !!cfg.enabled;
                document.getElementById('motInterval').value = cfg.interval_minutes || 240;
                document.getElementById('motMessages').value = (cfg.messages || []).join('\n');
            }
        } catch (e) { console.error(e); }
    }

    async function saveMotivationSettings(){
        const enabled = document.getElementById('motEnable').checked;
        const interval_minutes = parseInt(document.getElementById('motInterval').value || 240);
        const messages_raw = document.getElementById('motMessages').value || '';
        const messages = messages_raw.split('\n').map(s=>s.trim()).filter(Boolean);
        try {
            const resp = await fetch('/save_motivation_settings', {
                method: 'POST',
                body: JSON.stringify({enabled, interval_minutes, messages})
            });
            const j = await resp.json();
            const res = document.getElementById('motivationResult');
            res.style.display = 'block';
            res.textContent = j.message || (j.status === 'success' ? 'Settings saved' : 'Failed to save');
            res.style.backgroundColor = j.status === 'success' ? '#d4edda' : '#f8d7da';
            res.style.color = j.status === 'success' ? '#155724' : '#721c24';
            setTimeout(()=>res.style.display='none', 3000);
        } catch (e) { console.error(e); }
    }

    async function sendImmediateMotivation(){
        const messages_raw = document.getElementById('motMessages').value || '';
        const messages = messages_raw.split('\n').map(s=>s.trim()).filter(Boolean);
        const msg = messages.length ? messages[0] : 'Keep going! You are doing great!';
        try {
            const resp = await fetch('/trigger_test_notification', {
                method: 'POST',
                body: JSON.stringify({title: 'Motivation', message: msg})
            });
            const j = await resp.json();
            const res = document.getElementById('motivationResult');
            res.style.display = 'block';
            res.textContent = j.message || (j.status === 'success' ? 'Motivation sent' : 'Failed to send');
            res.style.backgroundColor = j.status === 'success' ? '#d4edda' : '#f8d7da';
            res.style.color = j.status === 'success' ? '#155724' : '#721c24';
            setTimeout(()=>res.style.display='none', 3000);
        } catch (e) { console.error(e); }
    }

    // Auto-load on startup
    window.addEventListener('DOMContentLoaded', function(){
        loadNotificationSettings();
        loadReminders();
        loadMotivationSettings();
    });

</script>
</body>
</html>
"""

# Save the index.html
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# -------------------------
# Server startup
# -------------------------

def signal_handler(sig, frame):
    print("\nShutting down server...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('', port), LifeTrackerHandler)
    print(f"Starting Notification Manager on port {port}...")
    print("Open http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


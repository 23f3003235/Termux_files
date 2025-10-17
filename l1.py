
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
        # preserve existing behavior; add new GET endpoints for reminders/motivation
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/get_categories':
            self.get_categories()
            return
        elif self.path == '/get_all_data':
            self.get_all_data()
            return
        elif self.path.startswith('/export_data'):
            self.export_data()
            return
        elif self.path == '/get_analytics':
            self.get_analytics()
            return
        elif self.path == '/get_goals':
            self.get_goals()
            return
        elif self.path == '/get_performance_data':
            self.get_performance_data()
            return
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
    
    # -----------------------
    # Existing methods (unchanged)
    # -----------------------
    
    def get_categories(self):
        """Get all categories from the data file"""
        categories = []
        try:
            if os.path.exists("lifetracker.csv"):
                df = pd.read_csv("lifetracker.csv", header=None)
                if len(df.columns) >= 4:
                    categories = df[3].unique().tolist()
        except Exception as e:
            print(f"Error loading categories: {e}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(categories).encode())

    def get_all_data(self):
        """Get all data from the CSV file"""
        try:
            if os.path.exists("lifetracker.csv"):
                with open("lifetracker.csv", "r") as f:
                    reader = csv.reader(f)
                    data = list(reader)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "data": data
                }).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "CSV file not found"
                }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode())

    def do_POST(self):
        if self.path == '/add_entry':
            self.add_entry()
        elif self.path == '/run_report':
            self.run_report()
        elif self.path == '/update_entry':
            self.update_entry()
        elif self.path == '/delete_entry':
            self.delete_entry()
        elif self.path == '/create_backup':
            self.create_backup()
        elif self.path == '/validate_data':
            self.validate_data()
        elif self.path == '/get_advanced_analytics':
            self.get_advanced_analytics()
        elif self.path == '/save_goal':
            self.save_goal()
        elif self.path == '/delete_goal':
            self.delete_goal()
        elif self.path == '/update_goal_progress':
            self.update_goal_progress()
        # New endpoints for reminders and motivation
        elif self.path == '/save_reminder':
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

    # -----------------------
    # The rest of your original methods should follow here (unchanged).
    # For safety I re-use the same functions you already have (add_entry, run_report, update_entry, delete_entry,
    # create_backup, validate_data, get_analytics, get_advanced_analytics, get_goals, save_goal, delete_goal,
    # update_goal_progress, get_performance_data, export_data, etc.)
    # In this combined file these methods remain exactly as they were in your original lt5.py.
    # -----------------------

    # All the existing methods from your original file go here...
    # (I'm including the key ones for context, but you should keep all your original methods)

    def validate_date_format(self, date_str):
        """Validate date format DD-MM-YYYY and check if it's a valid date"""
        try:
            parts = date_str.split('-')
            if len(parts) != 3:
                return False, "Date must be in DD-MM-YYYY format"
            
            day, month, year = parts
            if len(day) != 2 or len(month) != 2 or len(year) != 4:
                return False, "Date must be in DD-MM-YYYY format (2-digit day, 2-digit month, 4-digit year)"
            
            # Check if all parts are numeric
            if not (day.isdigit() and month.isdigit() and year.isdigit()):
                return False, "Date components must be numeric"
            
            day_int, month_int, year_int = int(day), int(month), int(year)
            
            # Check date validity
            if month_int < 1 or month_int > 12:
                return False, "Month must be between 01 and 12"
            
            if year_int < 2000 or year_int > 2100:
                return False, "Year must be between 2000 and 2100"
            
            # Check day validity based on month
            days_in_month = [31, 29 if year_int % 4 == 0 and (year_int % 100 != 0 or year_int % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if day_int < 1 or day_int > days_in_month[month_int - 1]:
                return False, f"Invalid day for {month_int:02d}/{year_int}"
            
            return True, "Valid date"
            
        except Exception as e:
            return False, f"Date validation error: {str(e)}"
    
    def validate_entry_data(self, date, activity, minutes, category):
        """Validate all entry data before processing"""
        errors = []
        
        # Validate date
        is_valid_date, date_error = self.validate_date_format(date)
        if not is_valid_date:
            errors.append(date_error)
        
        # Validate activity
        if not activity or not activity.strip():
            errors.append("Activity cannot be empty")
        elif len(activity.strip()) > 100:
            errors.append("Activity name too long (max 100 characters)")
        
        # Validate minutes
        try:
            minutes_int = int(minutes)
            if minutes_int <= 0:
                errors.append("Minutes must be a positive number")
            elif minutes_int > 1440:  # 24 hours in minutes
                errors.append("Minutes cannot exceed 1440 (24 hours)")
        except ValueError:
            errors.append("Minutes must be a valid number")
        
        # Validate category
        if not category or not category.strip():
            errors.append("Category cannot be empty")
        elif len(category.strip()) > 50:
            errors.append("Category name too long (max 50 characters)")
        
        return errors
    
    def create_backup(self):
        """Create a backup of the data file"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found to backup")
                return
            
            # Create backups directory if it doesn't exist
            os.makedirs("backups", exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backups/lifetracker_backup_{timestamp}.csv"
            shutil.copy2("lifetracker.csv", backup_file)
            
            # Clean up old backups (keep last 10)
            self.cleanup_old_backups()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": f"Backup created successfully: {backup_file}",
                "backup_file": backup_file
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Backup failed: {str(e)}")
    
    def cleanup_old_backups(self, keep_count=10):
        """Keep only the most recent backup files"""
        try:
            if not os.path.exists("backups"):
                return
            
            backup_files = []
            for file in os.listdir("backups"):
                if file.startswith("lifetracker_backup_") and file.endswith(".csv"):
                    file_path = os.path.join("backups", file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for file_path, _ in backup_files[keep_count:]:
                os.remove(file_path)
                
        except Exception as e:
            print(f"Backup cleanup warning: {str(e)}")
    
    def add_entry(self):
        """Enhanced add_entry with validation and backup"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            date = form.getvalue('date')
            activity = form.getvalue('activity')
            minutes = form.getvalue('minutes')
            category = form.getvalue('category')
            
            # Validate data before processing
            validation_errors = self.validate_entry_data(date, activity, minutes, category)
            if validation_errors:
                self.send_error_response("Validation errors: " + "; ".join(validation_errors))
                return
            
            # Create backup before making changes
            backup_result = self.create_backup_silent()
            
            # Proceed with adding entry
            with open("lifetracker.csv", "a") as f:
                f.write(f"{date},{activity},{minutes},{category}\n")
            
            self.send_success_response("Entry added successfully")
            
        except Exception as e:
            self.send_error_response(f"Error adding entry: {str(e)}")
    
    def create_backup_silent(self):
        """Create backup without sending response (for internal use)"""
        try:
            if not os.path.exists("lifetracker.csv"):
                return False
            
            os.makedirs("backups", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backups/lifetracker_backup_{timestamp}.csv"
            shutil.copy2("lifetracker.csv", backup_file)
            self.cleanup_old_backups()
            return True
        except:
            return False
    
    def run_report(self):
        """Enhanced report generation with validation"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            report_type = form.getvalue('report_type')
            month = form.getvalue('month')
            year = form.getvalue('year')
            
            # Validate report parameters
            if not report_type or report_type not in ['daily', 'category', 'activity', 'cattree']:
                self.send_error_response("Invalid report type")
                return
            
            try:
                month_int = int(month)
                if month_int < 1 or month_int > 12:
                    self.send_error_response("Month must be between 1 and 12")
                    return
            except (ValueError, TypeError):
                self.send_error_response("Month must be a valid number")
                return
            
            try:
                year_int = int(year)
                if year_int < 2000 or year_int > 2100:
                    self.send_error_response("Year must be between 2000 and 2100")
                    return
            except (ValueError, TypeError):
                self.send_error_response("Year must be a valid number")
                return
            
            scripts = {
                'daily': './daily2.awk',
                'category': './category2.awk', 
                'activity': './activity2.awk',
                'cattree': './cattree.awk'
            }
            
            image_files = {
                'daily': 'reports/daily_activity_plot.png',
                'category': 'reports/category_plot.png',
                'activity': 'reports/activity_checklist.png',
                'cattree': 'reports/cattree.png'
            }
            
            if report_type in scripts:
                try:
                    # Run the script with both month and year parameters
                    result = subprocess.run(
                        [scripts[report_type], month, year], 
                        capture_output=True, 
                        text=True,
                        timeout=30
                    )
                    
                    # Filter out AM intent lines from summary
                    summary_lines = []
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if not line.strip().startswith('am start'):
                                summary_lines.append(line)
                    clean_summary = '\n'.join(summary_lines)
                    
                    if result.returncode == 0:
                        status = "success"
                        image_path = image_files[report_type]
                        if not os.path.exists(image_path):
                            status = "error"
                            output = "Report image not found"
                        else:
                            output = image_path
                    else:
                        status = "error"
                        output = result.stderr
                except subprocess.TimeoutExpired:
                    status = "error"
                    output = "Report generation timed out"
                    clean_summary = ""
                except Exception as e:
                    status = "error"
                    output = str(e)
                    clean_summary = ""
            else:
                status = "error"
                output = "Invalid report type"
                clean_summary = ""
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": status, 
                "output": output,
                "summary": clean_summary
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Report generation error: {str(e)}")
    
    def update_entry(self):
        """Enhanced update_entry with validation and backup"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        try:
            index = data['index']
            new_date = data['date']
            new_activity = data['activity']
            new_minutes = data['minutes']
            new_category = data['category']
            
            # Validate data before processing
            validation_errors = self.validate_entry_data(new_date, new_activity, new_minutes, new_category)
            if validation_errors:
                self.send_error_response("Validation errors: " + "; ".join(validation_errors))
                return
            
            # Create backup before making changes
            self.create_backup_silent()
            
            with open("lifetracker.csv", "r") as f:
                lines = f.readlines()
            
            if 0 <= index < len(lines):
                lines[index] = f"{new_date},{new_activity},{new_minutes},{new_category}\n"
                
                with open("lifetracker.csv", "w") as f:
                    f.writelines(lines)
                
                self.send_success_response("Entry updated successfully")
            else:
                self.send_error_response("Invalid entry index")
                
        except Exception as e:
            self.send_error_response(f"Error updating entry: {str(e)}")
    
    def delete_entry(self):
        """Enhanced delete_entry with backup"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        try:
            index = data['index']
            
            # Create backup before making changes
            self.create_backup_silent()
            
            with open("lifetracker.csv", "r") as f:
                lines = f.readlines()
            
            if 0 <= index < len(lines):
                # Remove the line at the specified index
                del lines[index]
                
                with open("lifetracker.csv", "w") as f:
                    f.writelines(lines)
                
                self.send_success_response("Entry deleted successfully")
            else:
                self.send_error_response("Invalid entry index")
                
        except Exception as e:
            self.send_error_response(f"Error deleting entry: {str(e)}")
    
    def validate_data(self):
        """Validate entire dataset for integrity"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            issues = []
            with open("lifetracker.csv", "r") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(',')
                    if len(parts) != 4:
                        issues.append(f"Line {i}: Incorrect number of fields (expected 4, got {len(parts)})")
                        continue
                    
                    date, activity, minutes, category = parts
                    
                    # Validate each field
                    is_valid_date, date_error = self.validate_date_format(date)
                    if not is_valid_date:
                        issues.append(f"Line {i}: {date_error}")
                    
                    if not activity.strip():
                        issues.append(f"Line {i}: Empty activity")
                    
                    try:
                        min_val = int(minutes)
                        if min_val <= 0:
                            issues.append(f"Line {i}: Invalid minutes value: {minutes}")
                    except ValueError:
                        issues.append(f"Line {i}: Minutes not a number: {minutes}")
                    
                    if not category.strip():
                        issues.append(f"Line {i}: Empty category")
            
            if issues:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "warning",
                    "message": f"Found {len(issues)} data integrity issues",
                    "issues": issues
                }).encode())
            else:
                self.send_success_response("Data validation passed - no issues found")
                
        except Exception as e:
            self.send_error_response(f"Data validation error: {str(e)}")
    
    def export_data(self):
        """Export data in various formats"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            # Parse query parameters
            query_parts = self.path.split('?')
            format_type = 'csv'
            if len(query_parts) > 1:
                params = query_parts[1].split('&')
                for param in params:
                    if '=' in param:
                        key, value = param.split('=')
                        if key == 'format':
                            format_type = value
            
            # Read data
            with open("lifetracker.csv", "r") as f:
                reader = csv.reader(f)
                data = list(reader)
            
            if format_type == 'json':
                # Convert to JSON
                json_data = []
                for row in data:
                    if len(row) >= 4:
                        json_data.append({
                            'date': row[0],
                            'activity': row[1],
                            'minutes': row[2],
                            'category': row[3]
                        })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Disposition', 'attachment; filename="lifetracker_data.json"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(json_data, indent=2).encode())
                
            elif format_type == 'excel':
                # Convert to Excel (simulated with CSV for now)
                self.send_response(200)
                self.send_header('Content-type', 'text/csv')
                self.send_header('Content-Disposition', 'attachment; filename="lifetracker_data.csv"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['Date', 'Activity', 'Minutes', 'Category'])
                for row in data:
                    writer.writerow(row)
                
                self.wfile.write(output.getvalue().encode())
                
            else:  # CSV format
                self.send_response(200)
                self.send_header('Content-type', 'text/csv')
                self.send_header('Content-Disposition', 'attachment; filename="lifetracker_data.csv"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                with open("lifetracker.csv", "r") as f:
                    self.wfile.write(f.read().encode())
                    
        except Exception as e:
            self.send_error_response(f"Export error: {str(e)}")
    
    def get_analytics(self):
        """Get basic analytics data"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            
            # Convert minutes to numeric
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            df = df.dropna(subset=['minutes'])
            
            # Basic stats
            total_minutes = df['minutes'].sum()
            total_hours = total_minutes / 60
            total_entries = len(df)
            avg_minutes_per_entry = df['minutes'].mean()
            
            # Category breakdown
            category_totals = df.groupby('category')['minutes'].sum().sort_values(ascending=False)
            category_data = {
                'labels': category_totals.index.tolist(),
                'data': category_totals.values.tolist()
            }
            
            # Recent activity
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df = df.dropna(subset=['date'])
            recent_activity = df.sort_values('date', ascending=False).head(10)[['date', 'activity', 'minutes', 'category']]
            
            # Convert dates back to string for JSON serialization
            recent_activity['date'] = recent_activity['date'].dt.strftime('%d-%m-%Y')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "analytics": {
                    "total_minutes": total_minutes,
                    "total_hours": round(total_hours, 2),
                    "total_entries": total_entries,
                    "avg_minutes_per_entry": round(avg_minutes_per_entry, 2),
                    "category_breakdown": category_data,
                    "recent_activity": recent_activity.to_dict('records')
                }
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Analytics error: {str(e)}")
    
    def get_advanced_analytics(self):
        """Get advanced analytics with trends and patterns"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            
            # Data cleaning
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            df = df.dropna(subset=['minutes'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df = df.dropna(subset=['date'])
            
            # Monthly trends
            df['month'] = df['date'].dt.to_period('M')
            monthly_totals = df.groupby('month')['minutes'].sum()
            
            # Weekly patterns
            df['day_of_week'] = df['date'].dt.day_name()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_patterns = df.groupby('day_of_week')['minutes'].sum().reindex(day_order, fill_value=0)
            
            # Productivity metrics
            total_days = (df['date'].max() - df['date'].min()).days + 1
            avg_daily_minutes = df.groupby('date')['minutes'].sum().mean()
            
            # Most productive categories
            productive_categories = df.groupby('category')['minutes'].sum().nlargest(5)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "advanced_analytics": {
                    "monthly_trends": {
                        "months": monthly_totals.index.astype(str).tolist(),
                        "minutes": monthly_totals.values.tolist()
                    },
                    "weekly_patterns": {
                        "days": weekly_patterns.index.tolist(),
                        "minutes": weekly_patterns.values.tolist()
                    },
                    "productivity_metrics": {
                        "total_tracking_days": total_days,
                        "avg_daily_minutes": round(avg_daily_minutes, 2),
                        "most_productive_categories": {
                            "labels": productive_categories.index.tolist(),
                            "data": productive_categories.values.tolist()
                        }
                    }
                }
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Advanced analytics error: {str(e)}")
    
    def get_goals(self):
        """Get saved goals"""
        try:
            goals_file = "goals.json"
            if os.path.exists(goals_file):
                with open(goals_file, "r") as f:
                    goals = json.load(f)
            else:
                goals = []
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "goals": goals
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Error loading goals: {str(e)}")
    
    def save_goal(self):
        """Save a new goal"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            goals_file = "goals.json"
            goals = []
            
            if os.path.exists(goals_file):
                with open(goals_file, "r") as f:
                    goals = json.load(f)
            
            goal_id = str(len(goals) + 1)
            new_goal = {
                "id": goal_id,
                "title": data['title'],
                "target_minutes": data['target_minutes'],
                "current_progress": 0,
                "category": data['category'],
                "deadline": data.get('deadline', ''),
                "created_at": datetime.now().isoformat()
            }
            
            goals.append(new_goal)
            
            with open(goals_file, "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_success_response("Goal saved successfully")
            
        except Exception as e:
            self.send_error_response(f"Error saving goal: {str(e)}")
    
    def delete_goal(self):
        """Delete a goal"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            goals_file = "goals.json"
            if not os.path.exists(goals_file):
                self.send_error_response("No goals found")
                return
            
            with open(goals_file, "r") as f:
                goals = json.load(f)
            
            goal_id = data['id']
            goals = [goal for goal in goals if goal['id'] != goal_id]
            
            with open(goals_file, "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_success_response("Goal deleted successfully")
            
        except Exception as e:
            self.send_error_response(f"Error deleting goal: {str(e)}")
    
    def update_goal_progress(self):
        """Update goal progress"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            goals_file = "goals.json"
            if not os.path.exists(goals_file):
                self.send_error_response("No goals found")
                return
            
            with open(goals_file, "r") as f:
                goals = json.load(f)
            
            goal_id = data['id']
            progress = data['progress']
            
            for goal in goals:
                if goal['id'] == goal_id:
                    goal['current_progress'] = progress
                    break
            
            with open(goals_file, "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_success_response("Goal progress updated")
            
        except Exception as e:
            self.send_error_response(f"Error updating goal: {str(e)}")
    
    def get_performance_data(self):
        """Get performance metrics and insights"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            
            # Data cleaning
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            df = df.dropna(subset=['minutes'])
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df = df.dropna(subset=['date'])
            
            # Performance metrics
            total_minutes = df['minutes'].sum()
            total_entries = len(df)
            avg_session_length = df['minutes'].mean()
            
            # Consistency score (days with activity vs total days)
            total_days = (df['date'].max() - df['date'].min()).days + 1
            active_days = df['date'].nunique()
            consistency_score = (active_days / total_days) * 100 if total_days > 0 else 0
            
            # Progress over time (last 30 days)
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_data = df[df['date'] >= recent_cutoff]
            recent_daily = recent_data.groupby('date')['minutes'].sum()
            
            # Category efficiency (minutes per session by category)
            category_efficiency = df.groupby('category')['minutes'].mean().sort_values(ascending=False)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "performance": {
                    "total_minutes": total_minutes,
                    "total_entries": total_entries,
                    "avg_session_length": round(avg_session_length, 2),
                    "consistency_score": round(consistency_score, 2),
                    "active_days": active_days,
                    "total_days_tracked": total_days,
                    "recent_trend": {
                        "dates": recent_daily.index.strftime('%Y-%m-%d').tolist(),
                        "minutes": recent_daily.values.tolist()
                    },
                    "category_efficiency": {
                        "categories": category_efficiency.index.tolist(),
                        "avg_minutes": category_efficiency.values.tolist()
                    }
                }
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Performance data error: {str(e)}")

# -------------------------
# HTML UI (index.html) - updated with improved mobile layout and collapse functionality
# -------------------------
html_content = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Life Tracker</title>
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
            max-width: 1200px;
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
        input, select, button { 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid rgba(0,0,0,0.08); 
            font-size: 16px;
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
        <h1>Life Tracker</h1>

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

        <!-- Add other existing sections here with the same collapse structure -->
        <!-- Add New Entry Section -->
        <div class="section" id="addEntrySection">
            <div class="section-header" onclick="toggleSection('addEntrySection')">
                <div class="section-title">Add New Entry</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <!-- Your existing add entry form content -->
            </div>
        </div>

        <!-- Generate Reports Section -->
        <div class="section" id="reportsSection">
            <div class="section-header" onclick="toggleSection('reportsSection')">
                <div class="section-title">Generate Reports</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <!-- Your existing reports content -->
            </div>
        </div>

        <!-- Analytics Dashboard Section -->
        <div class="section" id="analyticsSection">
            <div class="section-header" onclick="toggleSection('analyticsSection')">
                <div class="section-title">Analytics Dashboard</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <!-- Your existing analytics content -->
            </div>
        </div>

        <!-- Goals System Section -->
        <div class="section" id="goalsSection">
            <div class="section-header" onclick="toggleSection('goalsSection')">
                <div class="section-title">Goals System</div>
                <button class="collapse-btn">Toggle</button>
            </div>
            <div class="section-content">
                <!-- Your existing goals content -->
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

# Save the index.html now (this will overwrite the older UI file)
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
    print(f"Starting LifeTracker server on port {port}...")
    print("Open http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

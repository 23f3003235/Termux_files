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
import uuid
import threading
import subprocess
import requests
import random
import re

class LifeTrackerHandler(SimpleHTTPRequestHandler):
    
    def handle_ai_chat(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        user_message = form.getvalue("message", "").lower().strip()
        
        def generate_response(message):
            if not message:
                return "Hello! I'm your Life Tracker assistant. How can I help you today?"
            
            # Feature: Add New Entry
            if any(word in message for word in ['add new entry', 'track', 'tracking', 'log', 'logging', 'activity', 'activities', 'time tracking']):
                return self.get_add_entry_info()
            
            # Feature: Generate Reports
            if any(word in message for word in ['generate reports', 'report', 'reports', 'daily report', 'category report', 'activity report']):
                return self.get_reports_info()
            
            # Feature: Analytics Dashboard
            if any(word in message for word in ['analytics', 'analytics dashboard', 'statistics', 'data analysis', 'insights']):
                return self.get_analytics_info()
            
            # Feature: Performance Overview
            if any(word in message for word in ['performance', 'performance overview', 'charts', 'graphs', 'trends']):
                return self.get_performance_info()
            
            # Feature: Goals System
            if any(word in message for word in ['goals', 'goals system', 'target', 'objective', 'progress']):
                return self.get_goals_info()
            
            # Feature: Query & Manage Data
            if any(word in message for word in ['query', 'manage data', 'search', 'filter', 'edit', 'delete', 'data management']):
                return self.get_data_management_info()
            
            # Feature: Data Management
            if any(word in message for word in ['backup', 'export', 'data backup', 'validate data', 'data integrity']):
                return self.get_backup_info()
            
            # Feature: To-Do List Manager
            if any(word in message for word in ['todo', 'todos', 'tasks', 'to-do list', 'reminder', 'task management']):
                return self.get_todo_info()
            
            # Feature: Notification Settings
            if any(word in message for word in ['notification', 'notifications', 'alert', 'remind', 'notify']):
                return self.get_notification_info()
            
            # Status inquiries
            if any(word in message for word in ['status', 'how many', 'current', 'progress', 'summary', 'overview']):
                return self.get_current_status(message)
            
            # Greeting patterns
            if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
                greetings = [
                    "Hello! I'm your Life Tracker assistant. Ready to help you track and optimize your time!",
                    "Hi there! How can I help you with your life tracking today?",
                    "Hey! Great to see you working on self-improvement. What can I assist with?",
                    "Greetings! I'm here to help you make the most of your Life Tracker app."
                ]
                return random.choice(greetings)
            
            # How are you patterns
            if re.search(r'how.*you|how.*going|how.*doing', message):
                responses = [
                    "I'm doing great! Ready to help you track your activities and achieve your goals.",
                    "I'm functioning perfectly! How's your tracking going today?",
                    "Doing well! It's always exciting to see people working on self-improvement.",
                    "All systems go! Ready to help you analyze your time and productivity."
                ]
                return random.choice(responses)
            
            # Name patterns
            if re.search(r'what.*your.*name|who.*you', message):
                names = [
                    "I'm Life Tracker Assistant! Your companion for time tracking and productivity.",
                    "You can call me TrackerBot! I'm here to help you make the most of your time.",
                    "I'm your Life Tracker AI assistant! Here to help you track, analyze, and improve.",
                    "I go by LifeTracker AI! What should I call you?"
                ]
                return random.choice(names)
            
            # Help patterns
            if 'help' in message:
                return self.get_help_info()
            
            # Question patterns
            if re.search(r'^what|^when|^where|^why|^how|^can you', message):
                question_responses = [
                    "That's an interesting question about life tracking! What specific aspect would you like to know more about?",
                    "I'd love to help you understand that better. Which Life Tracker feature are you curious about?",
                    "That's a great thing to explore in time management! Could you tell me which part of the app you're interested in?",
                    "I find that topic fascinating in productivity! Would you like to know more about tracking, reports, or goals?"
                ]
                return random.choice(question_responses)
            
            # Feeling/emotion patterns
            if any(word in message for word in ['sad', 'happy', 'excited', 'tired', 'bored', 'angry']):
                if 'sad' in message:
                    return "I'm sorry you're feeling down. Tracking your activities can help bring structure and accomplishment. Would you like to log something positive?"
                elif 'happy' in message:
                    return "That's wonderful! Perfect time to track your productive activities and build on that positive energy!"
                elif 'excited' in message:
                    return "Exciting times! What activities are you excited about? Let's track them!"
                elif 'tired' in message:
                    return "I understand feeling tired. Maybe track some rest activities? Balance is important in life tracking."
                elif 'bored' in message:
                    return "Let's find something engaging to track! What new activity or hobby would you like to start monitoring?"
                elif 'angry' in message:
                    return "I'm here to help if you want to channel that energy into productive tracking or goal setting."
            
            # Joke request patterns
            if any(word in message for word in ['joke', 'funny', 'laugh']):
                jokes = [
                    "Why did the time tracker get promoted? Because it always made every second count!",
                    "Why was the calendar such a good employee? It always took its work one day at a time!",
                    "What do you call a productive ghost? A time-sheet!",
                    "Why did the goal cross the road? To get to the other side of the progress bar!",
                    "What's a todo list's favorite type of music? Rock and roll-call!"
                ]
                return random.choice(jokes)
            
            # Time/date patterns
            if any(word in message for word in ['time', 'date', 'day']):
                current_time = time.strftime("%I:%M %p")
                current_date = time.strftime("%A, %B %d, %Y")
                return f"The current time is {current_time} and today is {current_date}. Perfect time to track your activities!"
            
            # Thank you patterns
            if any(word in message for word in ['thank', 'thanks', 'appreciate']):
                thank_responses = [
                    "You're very welcome! Happy to help you with your life tracking journey.",
                    "My pleasure! Is there anything else I can help you track or analyze?",
                    "Anytime! I enjoy helping people make the most of their time.",
                    "Glad I could assist! Don't hesitate to ask for more tracking help."
                ]
                return random.choice(thank_responses)
            
            # Goodbye patterns
            if any(word in message for word in ['bye', 'goodbye', 'see you', 'farewell']):
                goodbye_responses = [
                    "Goodbye! Keep up the great work with your life tracking!",
                    "See you later! Don't forget to log your activities!",
                    "Farewell! Looking forward to helping you track more progress next time!",
                    "Bye! Have a productive day and happy tracking!"
                ]
                return random.choice(goodbye_responses)
            
            # Default intelligent responses for anything else
            default_responses = [
                "That's interesting! How does that relate to your life tracking goals?",
                "I see what you mean. Have you considered tracking that in your activities?",
                "Fascinating! Would you like to set a goal or track this in your daily activities?",
                "That's a great point! How can we incorporate this into your productivity tracking?",
                "I understand. Tracking your activities might give you better insights into this.",
                "That's really thought-provoking! What would you like to achieve with your time tracking?",
                "Interesting perspective! How does this align with your life tracking objectives?",
                "I appreciate you sharing that with me. Would tracking related activities be helpful?",
                "That's wonderful! Perfect opportunity to track your progress and build on it.",
                "I see! Have you checked your analytics dashboard for insights on this topic?",
                "That's a good question for productivity! What do your tracking patterns show about this?",
                "I'm following along! Would you like help setting up tracking for this?",
                "That sounds important to you. Would you like to create a goal around this?",
                "I'm listening! What tracking metrics would help you understand this better?",
                "That's quite insightful! How can we measure this in your daily activities?"
            ]
            
            return random.choice(default_responses)

        # Generate the response
        reply = generate_response(user_message)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"reply": reply}).encode())

    # Add these new methods to your LifeTrackerHandler class:

    def get_add_entry_info(self):
        """Get detailed info about Add New Entry feature"""
        try:
            total_entries = 0
            if os.path.exists("lifetracker.csv"):
                with open("lifetracker.csv", "r") as f:
                    total_entries = sum(1 for line in f if line.strip())
            
            return f"""ADD NEW ENTRY FEATURE

    Description: Log your daily activities with time tracking. Record what you do, how long it takes, and categorize everything for better organization.

    Features:
    - Track activities with timestamps
    - Categorize your time usage
    - Set duration in minutes
    - Date-based organization

    Current Status: {total_entries} activities tracked so far

    How to use: Go to 'Add New Entry' section, fill in date, activity, minutes, and category, then click 'Add Entry'."""
        
        except Exception as e:
            return "The Add New Entry feature lets you track your daily activities with time duration and categories."

    def get_reports_info(self):
        """Get detailed info about Generate Reports feature"""
        return """GENERATE REPORTS FEATURE

    Description: Create comprehensive reports to analyze your time utilization patterns across different time periods and categories.

    Available Reports:
    - Daily Time Utilization - See how you spend time each day
    - Category-wise Time - Analyze time by categories
    - Activity Statistics - Detailed activity breakdown
    - Category Tree Summary - Hierarchical category analysis

    Features:
    - Monthly and yearly reporting
    - Visual charts and graphs
    - Summary statistics
    - Export capabilities

    How to use: Go to 'Generate Reports', select report type, month, and year, then click 'Generate Report'."""

    def get_analytics_info(self):
        """Get detailed info about Analytics Dashboard"""
        try:
            total_minutes = 0
            total_categories = 0
            if os.path.exists("lifetracker.csv"):
                df = pd.read_csv("lifetracker.csv", header=None)
                if len(df.columns) >= 4:
                    total_minutes = df[2].sum() if pd.to_numeric(df[2], errors='coerce').notna().any() else 0
                    total_categories = df[3].nunique()
            
            return f"""ANALYTICS DASHBOARD

    Description: Get deep insights into your time usage patterns with advanced analytics and filtering options.

    Features:
    - Basic analytics (total entries, minutes, categories)
    - Advanced filtered analytics
    - Date range analysis
    - Category and activity filtering
    - Productivity metrics

    Current Status:
    - Total tracked time: {int(total_minutes)} minutes ({int(total_minutes/60)} hours)
    - Unique categories: {total_categories}

    How to use: Go to 'Analytics Dashboard' and click 'Basic Analytics' for overview or 'Advanced Analytics' for detailed filtering."""

        except Exception as e:
            return "The Analytics Dashboard provides detailed insights into your time tracking data with various metrics and filters."

    def get_performance_info(self):
        """Get detailed info about Performance Overview"""
        return """PERFORMANCE OVERVIEW FEATURE

    Description: Visualize your productivity trends with interactive charts and performance metrics.

    Features:
    - Daily activity trends (last 30 days)
    - Category distribution pie charts
    - Weekly performance graphs
    - Progress tracking over time
    - Visual data representation

    Metrics Shown:
    - Total tracked days
    - Category distribution
    - Weekly averages
    - Activity patterns

    How to use: Go to 'Performance Overview' and click 'Refresh' to update the charts with latest data."""

    def get_goals_info(self):
        """Get detailed info about Goals System"""
        try:
            goals = []
            if os.path.exists("goals.json"):
                with open("goals.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        goals = json.loads(content)
            
            active_goals = len(goals)
            completed_goals = sum(1 for goal in goals if goal.get('progress_percentage', 0) >= 100)
            
            return f"""GOALS SYSTEM FEATURE

    Description: Set and track progress towards your time management and productivity goals.

    Goal Types:
    - Category Minutes - Target time for specific categories
    - Total Minutes - Overall time tracking goals
    - Consistency - Daily activity streak goals

    Tracking Periods: Daily, Weekly, Monthly, Yearly

    Current Status:
    - Active goals: {active_goals}
    - Completed goals: {completed_goals}

    Features:
    - Progress tracking with percentage
    - Automatic progress updates
    - Visual progress bars
    - Goal management (create, edit, delete)

    How to use: Go to 'Goals System', click 'New' to create goals, and 'Update' to refresh progress."""

        except Exception as e:
            return "The Goals System helps you set and track progress towards your time management objectives."

    def get_data_management_info(self):
        """Get detailed info about Query & Manage Data"""
        try:
            total_entries = 0
            if os.path.exists("lifetracker.csv"):
                with open("lifetracker.csv", "r") as f:
                    total_entries = sum(1 for line in f if line.strip())
            
            return f"""QUERY & MANAGE DATA FEATURE

    Description: Search, filter, and manage your tracked activities with powerful query capabilities.

    Features:
    - Search activities and categories
    - Date range filtering
    - Bulk data viewing
    - Edit and delete entries
    - Real-time data statistics

    Current Status: {total_entries} entries available for search and management

    Operations:
    - Search by keyword in activities/categories
    - Filter by date ranges
    - Edit existing entries
    - Delete unwanted entries
    - View summary statistics

    How to use: Go to 'Query & Manage Data', use search box or date filters to find entries, then use action buttons to manage them."""

        except Exception as e:
            return "The Query & Manage Data feature lets you search, filter, and edit your tracked activities."

    def get_backup_info(self):
        """Get detailed info about Data Management"""
        try:
            backup_count = 0
            if os.path.exists("backups"):
                backup_count = len([f for f in os.listdir("backups") if f.startswith("lifetracker_backup_")])
            
            return f"""DATA MANAGEMENT FEATURE

    Description: Protect your data with backup systems and ensure data integrity with validation tools.

    Features:
    - Automatic Backups - Created before data modifications
    - Manual Backups - On-demand backup creation
    - Data Validation - Check data integrity and format
    - Export Options - CSV, JSON, Excel formats
    - Backup Management - Keeps last 10 backups automatically

    Current Status: {backup_count} backup files available

    How to use: Go to 'Data Management' and use 'Create Backup', 'Validate Data', or 'Data Integrity Info' buttons."""

        except Exception as e:
            return "The Data Management feature provides backup, validation, and export capabilities for your data."

    def get_todo_info(self):
        """Get detailed info about To-Do List Manager"""
        try:
            todos = self.load_todo_data()
            total_todos = len(todos)
            pending_todos = len([t for t in todos if t.get('status') == 'pending'])
            completed_todos = len([t for t in todos if t.get('status') == 'completed'])
            
            return f"""TO-DO LIST MANAGER FEATURE

    Description: Manage your tasks and reminders alongside time tracking for complete productivity management.

    Features:
    - Create todos with categories and due dates
    - Track completion status
    - Search and filter todos
    - Category-based organization
    - Due date tracking

    Current Status:
    - Total todos: {total_todos}
    - Pending: {pending_todos}
    - Completed: {completed_todos}

    Operations:
    - Add new todos with target dates
    - Mark todos as completed
    - Search and filter by various criteria
    - Edit or delete todos

    How to use: Go to 'To-Do List Manager', click 'New' to add todos, or use search filters to manage existing ones."""

        except Exception as e:
            return "The To-Do List Manager helps you track tasks and reminders alongside your time tracking."

    def get_notification_info(self):
        """Get detailed info about Notification Settings"""
        try:
            settings = {}
            if os.path.exists("notifications.json"):
                with open("notifications.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        settings = json.loads(content)
            
            enabled_notifications = sum([
                settings.get('daily_report_enabled', False),
                settings.get('todo_reminder_enabled', False),
                settings.get('goal_reminder_enabled', False),
                settings.get('consistency_reminder_enabled', False),
                settings.get('specific_date_enabled', False)
            ])
            
            return f"""NOTIFICATION SETTINGS FEATURE

    Description: Configure automated reminders and notifications to stay on track with your goals and activities.

    Notification Types:
    - Daily Reports - Time utilization summaries
    - Todo Reminders - Pending task notifications
    - Goal Progress - Goal achievement updates
    - Consistency Reminders - Daily activity prompts
    - Specific Date - Custom date-based reminders
    - Custom Notifications - Instant manual notifications

    Current Status: {enabled_notifications} notification types enabled

    Requirements: Termux API must be installed on your device

    How to use: Go to 'Notification Settings', configure your preferences, and click 'Save Notification Settings'."""

        except Exception as e:
            return "The Notification Settings feature lets you configure automated reminders and alerts."

    def get_help_info(self):
        """Get comprehensive help information"""
        return """LIFE TRACKER HELP GUIDE

    Available Features:

    1. Add New Entry - Track daily activities with time and categories
    2. Generate Reports - Create time utilization reports and charts
    3. Analytics Dashboard - Get insights with basic and advanced analytics
    4. Performance Overview - View trends with interactive charts
    5. Goals System - Set and track productivity goals
    6. Query & Manage Data - Search, filter, and edit your entries
    7. Data Management - Backup, validate, and export your data
    8. To-Do List Manager - Manage tasks and reminders
    9. Notification Settings - Configure automated reminders

    Ask me about:
    - Any specific feature (e.g., 'tell me about goals')
    - Current status (e.g., 'how many activities tracked')
    - How to use features
    - Setting up notifications
    - Creating reports

    Examples:
    - "What can I do with analytics?"
    - "Show me my current status"
    - "How do I set up goals?"
    - "Tell me about notifications" """

    def get_current_status(self, message):
        """Get current status of various features"""
        try:
            # Activity tracking status
            total_entries = 0
            total_minutes = 0
            total_categories = 0
            if os.path.exists("lifetracker.csv"):
                df = pd.read_csv("lifetracker.csv", header=None)
                if len(df.columns) >= 4:
                    total_entries = len(df)
                    total_minutes = df[2].sum() if pd.to_numeric(df[2], errors='coerce').notna().any() else 0
                    total_categories = df[3].nunique()
            
            # Goals status
            goals = []
            if os.path.exists("goals.json"):
                with open("goals.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        goals = json.loads(content)
            
            # Todos status
            todos = self.load_todo_data()
            
            # Backups status
            backup_count = 0
            if os.path.exists("backups"):
                backup_count = len([f for f in os.listdir("backups") if f.startswith("lifetracker_backup_")])
            
            status_report = f"""CURRENT LIFE TRACKER STATUS

    Activity Tracking:
    - Total entries: {total_entries}
    - Total time tracked: {int(total_minutes)} minutes ({int(total_minutes/60)} hours)
    - Unique categories: {total_categories}

    Goals System:
    - Active goals: {len(goals)}
    - Completed goals: {sum(1 for g in goals if g.get('progress_percentage', 0) >= 100)}

    To-Do List:
    - Total todos: {len(todos)}
    - Pending: {len([t for t in todos if t.get('status') == 'pending'])}
    - Completed: {len([t for t in todos if t.get('status') == 'completed'])}

    Data Protection:
    - Available backups: {backup_count}

    Last Updated: {time.strftime('%Y-%m-%d %I:%M %p')}

    Keep up the great work!"""
            
            return status_report
        
        except Exception as e:
            return "I'm having trouble retrieving the current status. Please try again later."
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/get_categories':
            self.get_categories()
            return
        elif self.path == '/get_all_data':
            self.get_all_data()
            return
        
        elif self.path == '/get_todo_categories':
            self.get_todo_categories_endpoint()
            return
        elif self.path == '/get_all_todos':
            self.get_all_todos()
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
        elif self.path == '/open_clock':
            self.open_clock()
            return
        elif self.path == '/get_notification_settings':
            self.get_notification_settings()
            return
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def get_todo_categories(self):
        """Get unique categories from todo data"""
        try:
            todos = self.load_todo_data()
            categories = set()
            for todo in todos:
                if 'category' in todo:
                    categories.add(todo['category'])
            return list(categories)
        except:
            return []
    
    def load_todo_data(self):
        """Load todo data from JSON file"""
        try:
            if os.path.exists("todo.json"):
                with open("todo.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            return []
        except:
            return []
    
    def save_todo_data(self, todos):
        """Save todo data to JSON file"""
        try:
            with open("todo.json", "w") as f:
                json.dump(todos, f, indent=2)
            return True
        except:
            return False
    
    def get_todo_categories_endpoint(self):
        """API endpoint for todo categories"""
        categories = self.get_todo_categories()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(categories).encode())
    
    def get_all_todos(self):
        """Get all todo items"""
        try:
            todos = self.load_todo_data()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "todos": todos
            }).encode())
        except Exception as e:
            self.send_error_response(f"Error loading todos: {str(e)}")

    

    def open_clock(self):
        """Open Android Clock app using am intent (for Termux environment)"""

        try:
        # Simply run the command and don't capture output at all
            subprocess.run(
                ["am", "start", "-a", "android.intent.action.SET_ALARM"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        # Assume it worked - the am command usually does
            return "success", "Clock app opened"
        
        except Exception as e:
            return "error", f"Failed to execute command: {str(e)}"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": status, "output": output}).encode())

    
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
        elif self.path == '/add_todo':
            self.add_todo()
        elif self.path == '/update_todo':
            self.update_todo()
        elif self.path == '/delete_todo':
            self.delete_todo()
        elif self.path == '/search_todos':
            self.search_todos()
        elif self.path == '/save_notification_settings':
            self.save_notification_settings()
        elif self.path == '/test_notification':
            self.test_notification()
        elif self.path == '/send_custom_notification':
            self.send_custom_notification()
        elif self.path == '/reset_notification_settings':
            self.reset_notification_settings()
        elif self.path == "/ai_chat":
            self.handle_ai_chat()
        else:
            self.send_error(404, "Endpoint not found")
    
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
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "No data file found"
                }).encode())
                return
            
            # Read data with proper error handling
            data = []
            with open("lifetracker.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:  # Ensure we have all required columns
                        data.append(row)
            
            if not data:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "analytics": {
                        "total_entries": 0,
                        "total_minutes": 0,
                        "total_categories": 0,
                        "total_activities": 0,
                        "date_range": {"start": "N/A", "end": "N/A"},
                        "top_categories": {},
                        "top_activities": {},
                        "recent_activity": {}
                    }
                }).encode())
                return
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data, columns=['date', 'activity', 'minutes', 'category'])
            
            # Basic analytics
            total_entries = len(df)
            
            # Handle minutes conversion safely
            total_minutes = 0
            try:
                df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
                total_minutes = df['minutes'].sum()
            except:
                total_minutes = 0
            
            total_categories = df['category'].nunique()
            total_activities = df['activity'].nunique()
            
            # Date range
            date_range = {"start": "N/A", "end": "N/A"}
            try:
                df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                valid_dates = df[df['date_obj'].notna()]
                if not valid_dates.empty:
                    date_range = {
                        'start': valid_dates['date_obj'].min().strftime('%Y-%m-%d'),
                        'end': valid_dates['date_obj'].max().strftime('%Y-%m-%d')
                    }
            except:
                pass
            
            # Top categories
            top_categories = {}
            try:
                category_stats = df.groupby('category')['minutes'].sum().sort_values(ascending=False).head(10)
                top_categories = category_stats.to_dict()
            except:
                pass
            
            # Top activities
            top_activities = {}
            try:
                activity_stats = df.groupby('activity')['minutes'].sum().sort_values(ascending=False).head(10)
                top_activities = activity_stats.to_dict()
            except:
                pass
            
            # Recent activity
            recent_days_formatted = {}
            try:
                recent_days = df.groupby('date_obj')['minutes'].sum().sort_index(ascending=False).head(7)
                recent_days_formatted = {k.strftime('%Y-%m-%d'): int(v) for k, v in recent_days.items()}
            except:
                pass
            
            analytics_data = {
                "status": "success",
                "analytics": {
                    "total_entries": int(total_entries),
                    "total_minutes": int(total_minutes),
                    "total_categories": int(total_categories),
                    "total_activities": int(total_activities),
                    "date_range": date_range,
                    "top_categories": top_categories,
                    "top_activities": top_activities,
                    "recent_activity": recent_days_formatted
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(analytics_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Analytics error: {str(e)}"
            }).encode())
    
    def get_advanced_analytics(self):
        """Get advanced analytics with filters"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            # Read data
            csv_data = []
            with open("lifetracker.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        csv_data.append(row)
            
            if not csv_data:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "No data available",
                    "analytics": {}
                }).encode())
                return
            
            df = pd.DataFrame(csv_data, columns=['date', 'activity', 'minutes', 'category'])
            
            # Convert data types safely
            try:
                df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
                df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            except:
                pass
            
            # Apply filters
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            category_filter = data.get('category')
            activity_filter = data.get('activity')
            
            filtered_df = df.copy()
            
            if start_date:
                try:
                    start_date_obj = pd.to_datetime(start_date)
                    filtered_df = filtered_df[filtered_df['date_obj'] >= start_date_obj]
                except:
                    pass
            
            if end_date:
                try:
                    end_date_obj = pd.to_datetime(end_date)
                    filtered_df = filtered_df[filtered_df['date_obj'] <= end_date_obj]
                except:
                    pass
            
            if category_filter:
                filtered_df = filtered_df[filtered_df['category'].str.contains(category_filter, case=False, na=False)]
            
            if activity_filter:
                filtered_df = filtered_df[filtered_df['activity'].str.contains(activity_filter, case=False, na=False)]
            
            # Advanced analytics
            if len(filtered_df) == 0:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "No data matching filters",
                    "analytics": {}
                }).encode())
                return
            
            # Time trends
            daily_trends_formatted = {}
            try:
                daily_trends = filtered_df.groupby('date_obj')['minutes'].sum().sort_index().tail(30)
                daily_trends_formatted = {k.strftime('%Y-%m-%d'): int(v) for k, v in daily_trends.items()}
            except:
                pass
            
            # Category distribution
            category_distribution = {}
            try:
                cat_dist = filtered_df.groupby('category')['minutes'].sum().sort_values(ascending=False)
                category_distribution = {k: int(v) for k, v in cat_dist.items()}
            except:
                pass
            
            # Activity patterns
            activity_patterns = {}
            try:
                act_patterns = filtered_df.groupby('activity')['minutes'].sum().sort_values(ascending=False).head(20)
                activity_patterns = {k: int(v) for k, v in act_patterns.items()}
            except:
                pass
            
            # Productivity metrics
            total_days = 0
            avg_daily_minutes = 0
            max_daily_minutes = 0
            
            try:
                total_days = filtered_df['date_obj'].nunique()
                daily_stats = filtered_df.groupby('date_obj')['minutes'].sum()
                avg_daily_minutes = daily_stats.mean()
                max_daily_minutes = daily_stats.max()
            except:
                pass
            
            advanced_analytics = {
                "status": "success",
                "analytics": {
                    "filtered_entries": int(len(filtered_df)),
                    "filtered_minutes": int(filtered_df['minutes'].sum()),
                    "daily_trends": daily_trends_formatted,
                    "category_distribution": category_distribution,
                    "activity_patterns": activity_patterns,
                    "productivity_metrics": {
                        "total_days": int(total_days),
                        "avg_daily_minutes": round(float(avg_daily_minutes), 2),
                        "max_daily_minutes": int(max_daily_minutes)
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(advanced_analytics).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Advanced analytics error: {str(e)}"
            }).encode())
    
    def get_goals(self):
        """Get all goals from the goals file"""
        try:
            goals = []
            if os.path.exists("goals.json"):
                with open("goals.json", "r") as f:
                    content = f.read().strip()
                    if content:  # Only parse if file is not empty
                        goals = json.loads(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "goals": goals
            }).encode())
            
        except Exception as e:
            print(f"Error loading goals: {e}")
            # Return empty goals list if there's an error
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "goals": []
            }).encode())
    
    def save_goal(self):
        """Save a new goal or update existing goal"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            goals = []
            if os.path.exists("goals.json"):
                try:
                    with open("goals.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            goals = json.loads(content)
                except json.JSONDecodeError:
                    # If file is corrupted, start with empty goals
                    goals = []
            
            # Add or update goal
            goal_id = data.get('id')
            if goal_id:
                # Update existing goal
                for i, goal in enumerate(goals):
                    if goal.get('id') == goal_id:
                        goals[i] = data
                        break
            else:
                # Add new goal
                data['id'] = str(int(datetime.now().timestamp() * 1000))
                data['created_at'] = datetime.now().isoformat()
                data['current_progress'] = 0
                data['progress_percentage'] = 0
                goals.append(data)
            
            # Save goals
            with open("goals.json", "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Goal saved successfully",
                "goal": data
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error saving goal: {str(e)}"
            }).encode())
    
    def delete_goal(self):
        """Delete a goal"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            goal_id = data.get('id')
            
            goals = []
            if os.path.exists("goals.json"):
                try:
                    with open("goals.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            goals = json.loads(content)
                except json.JSONDecodeError:
                    goals = []
            
            # Remove goal
            goals = [goal for goal in goals if goal.get('id') != goal_id]
            
            # Save updated goals
            with open("goals.json", "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Goal deleted successfully"
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error deleting goal: {str(e)}"
            }).encode())
    
    def update_goal_progress(self):
        """Update goal progress based on current data"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_success_response("No tracking data available")
                return
            
            # Read goals with error handling
            goals = []
            if os.path.exists("goals.json"):
                try:
                    with open("goals.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            goals = json.loads(content)
                except json.JSONDecodeError as e:
                    self.send_error_response(f"Corrupted goals file: {str(e)}")
                    return
            
            if not goals:
                self.send_success_response("No goals to update")
                return
                
            # Read tracking data
            try:
                df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
                df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
                # Remove rows with invalid dates or minutes
                df = df[df['date_obj'].notna() & df['minutes'].notna()]
            except Exception as e:
                self.send_error_response(f"Error reading tracking data: {str(e)}")
                return
            
            updated_goals = []
            for goal in goals:
                try:
                    goal_type = goal.get('type', 'category')
                    target = float(goal.get('target', 0))
                    category = goal.get('category', '')
                    period = goal.get('period', 'weekly')
                    
                    # Calculate progress based on goal type and period
                    progress = self.calculate_goal_progress(df, goal_type, target, category, period)
                    goal['current_progress'] = float(progress)
                    goal['progress_percentage'] = min(100, (progress / target * 100) if target > 0 else 0)
                    goal['last_updated'] = datetime.now().isoformat()
                    
                    updated_goals.append(goal)
                except Exception as e:
                    print(f"Error updating goal {goal.get('id', 'unknown')}: {e}")
                    # Keep the goal as is if there's an error updating it
                    updated_goals.append(goal)
            
            # Save updated goals with progress
            with open("goals.json", "w") as f:
                json.dump(updated_goals, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Goal progress updated successfully",
                "goals": updated_goals
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error updating goal progress: {str(e)}"
            }).encode())
    
    def calculate_goal_progress(self, df, goal_type, target, category, period):
        """Calculate progress for a specific goal"""
        try:
            if df.empty:
                return 0.0
                
            # Filter by period
            now = datetime.now()
            if period == 'daily':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'weekly':
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'monthly':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # yearly
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Convert start_date to pandas Timestamp for proper comparison
            start_date_ts = pd.Timestamp(start_date)
            
            # Filter data by date range
            period_data = df[df['date_obj'] >= start_date_ts]
            
            if period_data.empty:
                return 0.0
                
            if goal_type == 'category':
                # Category-based goal
                if category:
                    category_data = period_data[period_data['category'] == category]
                    return float(category_data['minutes'].sum())
            elif goal_type == 'total_minutes':
                # Total minutes goal
                return float(period_data['minutes'].sum())
            elif goal_type == 'consistency':
                # Consistency goal (days with activity)
                return float(period_data['date_obj'].nunique())
            
            return 0.0
        except Exception as e:
            print(f"Error calculating goal progress: {e}")
            return 0.0
    def add_todo(self):
        """Add a new todo item"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            # Validate required fields
            required_fields = ['activity', 'target_date', 'category']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    self.send_error_response(f"Missing required field: {field}")
                    return
            
            # Load existing todos
            todos = self.load_todo_data()
            
            # Create new todo
            new_todo = {
                'id': str(uuid.uuid4()),
                'date_created': datetime.now().strftime('%d-%m-%Y'),
                'activity': data['activity'].strip(),
                'target_date': data['target_date'],
                'category': data['category'].strip(),
                'status': data.get('status', 'pending'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add and save
            todos.append(new_todo)
            if self.save_todo_data(todos):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Todo added successfully",
                    "todo": new_todo
                }).encode())
            else:
                self.send_error_response("Failed to save todo")
                
        except Exception as e:
            self.send_error_response(f"Error adding todo: {str(e)}")
    
    def update_todo(self):
        """Update an existing todo item"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            if 'id' not in data:
                self.send_error_response("Todo ID is required")
                return
            
            # Load existing todos
            todos = self.load_todo_data()
            
            # Find and update todo
            updated = False
            for i, todo in enumerate(todos):
                if todo['id'] == data['id']:
                    # Update fields
                    if 'activity' in data:
                        todos[i]['activity'] = data['activity']
                    if 'target_date' in data:
                        todos[i]['target_date'] = data['target_date']
                    if 'category' in data:
                        todos[i]['category'] = data['category']
                    if 'status' in data:
                        todos[i]['status'] = data['status']
                    
                    todos[i]['updated_at'] = datetime.now().isoformat()
                    updated = True
                    break
            
            if updated and self.save_todo_data(todos):
                self.send_success_response("Todo updated successfully")
            else:
                self.send_error_response("Todo not found or update failed")
                
        except Exception as e:
            self.send_error_response(f"Error updating todo: {str(e)}")
    
    def delete_todo(self):
        """Delete a todo item"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            if 'id' not in data:
                self.send_error_response("Todo ID is required")
                return
            
            # Load existing todos
            todos = self.load_todo_data()
            
            # Filter out the todo to delete
            original_count = len(todos)
            todos = [todo for todo in todos if todo['id'] != data['id']]
            
            if len(todos) < original_count and self.save_todo_data(todos):
                self.send_success_response("Todo deleted successfully")
            else:
                self.send_error_response("Todo not found or delete failed")
                
        except Exception as e:
            self.send_error_response(f"Error deleting todo: {str(e)}")
    
    def search_todos(self):
        """Search todos with filters"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            # Load all todos
            todos = self.load_todo_data()
            
            # Apply filters
            filtered_todos = todos
            
            # Activity filter
            if data.get('activity'):
                activity_filter = data['activity'].lower()
                filtered_todos = [todo for todo in filtered_todos 
                                if activity_filter in todo['activity'].lower()]
            
            # Category filter
            if data.get('category'):
                category_filter = data['category'].lower()
                filtered_todos = [todo for todo in filtered_todos 
                                if 'category' in todo and category_filter in todo['category'].lower()]
            
            # Status filter
            if data.get('status'):
                status_filter = data['status'].lower()
                filtered_todos = [todo for todo in filtered_todos 
                                if status_filter == todo['status'].lower()]
            
            # Date range filter for target date
            if data.get('target_date_from') or data.get('target_date_to'):
                filtered_todos = self.filter_todos_by_date_range(filtered_todos, data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "todos": filtered_todos,
                "total_count": len(filtered_todos)
            }).encode())
            
        except Exception as e:
            self.send_error_response(f"Error searching todos: {str(e)}")
    
    def filter_todos_by_date_range(self, todos, filters):
        """Filter todos by target date range"""
        try:
            filtered = []
            
            for todo in todos:
                if 'target_date' not in todo:
                    continue
                
                todo_date = datetime.strptime(todo['target_date'], '%Y-%m-%d')
                include = True
                
                if filters.get('target_date_from'):
                    from_date = datetime.strptime(filters['target_date_from'], '%Y-%m-%d')
                    if todo_date < from_date:
                        include = False
                
                if include and filters.get('target_date_to'):
                    to_date = datetime.strptime(filters['target_date_to'], '%Y-%m-%d')
                    if todo_date > to_date:
                        include = False
                
                if include:
                    filtered.append(todo)
            
            return filtered
        except:
            return todos
    
    # Replace ALL notification-related methods with these:

    def send_termux_notification(self, title, message, urgency='default'):
        """Send notification using Termux API with subprocess"""
        try:
            # Use subprocess.run with proper error handling
            result = subprocess.run([
                'termux-notification',
                '--title', title,
                '--content', message
            ], 
            capture_output=True, 
            text=True,
            timeout=10
            )
            
            if result.returncode == 0:
                print(f"Notification sent: {title}")
                return True
            else:
                print(f"Termux notification failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Termux notification timed out")
            return False
        except FileNotFoundError:
            print("Termux API not found. Make sure 'pkg install termux-api' is run.")
            return False
        except Exception as e:
            print(f"Error sending Termux notification: {e}")
            return False

    def get_notification_settings(self):
        """Get current notification settings"""
        try:
            settings = {}
            if os.path.exists("notifications.json"):
                with open("notifications.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        settings = json.loads(content)
            
            # Set default values for any missing settings
            default_settings = {
                'daily_report_enabled': False,
                'daily_report_time': '09:00',
                'todo_reminder_enabled': False,
                'todo_reminder_time': '18:00',
                'goal_reminder_enabled': False,
                'goal_reminder_time': '20:00',
                'specific_date_enabled': False,
                'specific_date': '',
                'specific_date_time': '10:00',
                'specific_date_title': '',
                'specific_date_message': '',
                'consistency_reminder_enabled': False,
                'consistency_reminder_time': '21:00'
            }
            
            # Merge with defaults
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "settings": settings
            }).encode())
            
        except Exception as e:
            print(f"Error loading notification settings: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error loading notification settings: {str(e)}"
            }).encode())

    def save_notification_settings(self):
        """Save notification settings to file"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            # Validate and set default values for required fields
            required_fields = {
                'daily_report_enabled': False,
                'daily_report_time': '09:00',
                'todo_reminder_enabled': False,
                'todo_reminder_time': '18:00',
                'goal_reminder_enabled': False,
                'goal_reminder_time': '20:00',
                'specific_date_enabled': False,
                'specific_date': '',
                'specific_date_time': '10:00',
                'specific_date_title': '',
                'specific_date_message': '',
                'consistency_reminder_enabled': False,
                'consistency_reminder_time': '21:00'
            }
            
            # Ensure all required fields are present
            for field, default_value in required_fields.items():
                if field not in data:
                    data[field] = default_value
            
            # Save to file
            with open("notifications.json", "w") as f:
                json.dump(data, f, indent=2)
            
            print(f"Notification settings saved successfully")
            
            # Start/stop notification scheduler based on settings
            self.manage_notification_scheduler(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Notification settings saved successfully"
            }).encode())
            
        except Exception as e:
            print(f"Error saving notification settings: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error saving notification settings: {str(e)}"
            }).encode())

    def manage_notification_scheduler(self, settings):
        """Manage the notification scheduler thread"""
        try:
            # Check if any notifications are enabled
            notifications_enabled = any([
                settings.get('daily_report_enabled', False),
                settings.get('todo_reminder_enabled', False),
                settings.get('goal_reminder_enabled', False),
                settings.get('consistency_reminder_enabled', False)
            ])
            
            if notifications_enabled:
                # Start scheduler if not already running
                if not hasattr(self, 'scheduler_running') or not self.scheduler_running:
                    self.start_notification_scheduler()
                    print("Notification scheduler started")
            else:
                # Stop scheduler if running
                if hasattr(self, 'scheduler_running') and self.scheduler_running:
                    self.stop_notification_scheduler()
                    print("Notification scheduler stopped")
                        
        except Exception as e:
            print(f"Error managing notification scheduler: {e}")

    def start_notification_scheduler(self):
        """Start the notification scheduler in a separate thread"""
        try:
            self.scheduler_running = True
            scheduler_thread = threading.Thread(target=self.notification_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            print("Notification scheduler thread started")
        except Exception as e:
            print(f"Error starting notification scheduler: {e}")

    def stop_notification_scheduler(self):
        """Stop the notification scheduler"""
        try:
            self.scheduler_running = False
            print("Notification scheduler stopped")
        except Exception as e:
            print(f"Error stopping notification scheduler: {e}")

    def notification_scheduler(self):
        """Background thread to check and send notifications"""
        print("Notification scheduler started - checking every 60 seconds")
        
        while getattr(self, 'scheduler_running', False):
            try:
                # Load current settings
                if os.path.exists("notifications.json"):
                    with open("notifications.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            settings = json.loads(content)
                            
                            current_time = datetime.now().strftime("%H:%M")
                            current_date = datetime.now().strftime("%Y-%m-%d")
                            
                            print(f"Scheduler check - Current time: {current_time}")
                            
                            # Check daily report notification
                            if (settings.get('daily_report_enabled') and 
                                settings.get('daily_report_time') == current_time):
                                print("Triggering daily report notification")
                                self.send_daily_report_notification()
                            
                            # Check todo reminder notification
                            if (settings.get('todo_reminder_enabled') and 
                                settings.get('todo_reminder_time') == current_time):
                                print("Triggering todo reminder notification")
                                self.send_todo_reminder_notification()
                            
                            # Check goal reminder notification
                            if (settings.get('goal_reminder_enabled') and 
                                settings.get('goal_reminder_time') == current_time):
                                print("Triggering goal reminder notification")
                                self.send_goal_reminder_notification()
                            
                            # Check specific date notifications
                            specific_date = settings.get('specific_date')
                            if (specific_date and 
                                settings.get('specific_date_enabled') and
                                specific_date == current_date and
                                settings.get('specific_date_time') == current_time):
                                print("Triggering specific date notification")
                                self.send_specific_date_notification(settings)
                            
                            # Check consistency reminder
                            if (settings.get('consistency_reminder_enabled') and 
                                settings.get('consistency_reminder_time') == current_time):
                                print("Triggering consistency reminder")
                                self.send_consistency_reminder()
                
                # Sleep for 60 seconds before checking again
                time.sleep(60)
                
            except Exception as e:
                print(f"Error in notification scheduler: {e}")
                time.sleep(60)

    def send_daily_report_notification(self):
        """Send daily time utilization report notification"""
        try:
            if not os.path.exists("lifetracker.csv"):
                print("No data file for daily report")
                return
            
            # Get current month and year
            now = datetime.now()
            month = now.month
            year = now.year
            
            print(f"Generating daily report for {month}/{year}")
            
            # Generate daily report summary using subprocess
            try:
                result = subprocess.run(
                    ['./daily2.awk', str(month), str(year)], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Filter out AM intent lines and get summary
                    summary_lines = []
                    for line in result.stdout.split('\n'):
                        if not line.strip().startswith('am start') and line.strip():
                            summary_lines.append(line.strip())
                    
                    if summary_lines:
                        # Take last few lines as summary
                        summary = '\n'.join(summary_lines[-5:])
                        title = "Daily Time Report"
                        message = f"Monthly Summary for {month}/{year}:\n{summary}"
                        
                        print(f"Sending daily report: {message[:50]}...")
                        self.send_termux_notification(title, message)
                    else:
                        print("No summary generated for daily report")
                else:
                    print(f"Daily report generation failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("Daily report generation timed out")
            except Exception as e:
                print(f"Error generating daily report: {e}")
                
        except Exception as e:
            print(f"Error in daily report notification: {e}")

    def send_todo_reminder_notification(self):
        """Send pending todos reminder notification"""
        try:
            todos = self.load_todo_data()
            pending_todos = [todo for todo in todos if todo.get('status') == 'pending']
            
            print(f"Found {len(pending_todos)} pending todos")
            
            if pending_todos:
                title = "Pending Todos Reminder"
                message = f"You have {len(pending_todos)} pending todos:\n"
                
                # Add first few todos to message
                for i, todo in enumerate(pending_todos[:3]):
                    message += f"• {todo.get('activity', 'Unknown')}\n"
                
                if len(pending_todos) > 3:
                    message += f"... and {len(pending_todos) - 3} more"
                
                self.send_termux_notification(title, message)
            else:
                title = "All Done!"
                message = "Great job! You have no pending todos."
                self.send_termux_notification(title, message)
                
        except Exception as e:
            print(f"Error in todo reminder notification: {e}")

    def send_goal_reminder_notification(self):
        """Send goal progress reminder notification"""
        try:
            if not os.path.exists("goals.json"):
                print("No goals file found")
                return
                
            with open("goals.json", "r") as f:
                content = f.read().strip()
                if not content:
                    print("Empty goals file")
                    return
                goals = json.loads(content)
            
            print(f"Found {len(goals)} goals")
            
            if goals:
                title = "Goals Progress Reminder"
                message = "Your goals progress:\n"
                
                for goal in goals[:3]:  # Show first 3 goals
                    progress = goal.get('current_progress', 0)
                    target = goal.get('target', 1)
                    percentage = min(100, (progress / target * 100)) if target > 0 else 0
                    message += f"• {goal.get('title', 'Unknown')}: {percentage:.1f}%\n"
                
                self.send_termux_notification(title, message)
            else:
                print("No goals to notify about")
                
        except Exception as e:
            print(f"Error in goal reminder notification: {e}")

    def send_specific_date_notification(self, settings):
        """Send notification for specific date"""
        try:
            title = settings.get('specific_date_title', 'Reminder')
            message = settings.get('specific_date_message', 'Custom notification')
            print(f"Sending specific date notification: {title}")
            self.send_termux_notification(title, message)
        except Exception as e:
            print(f"Error in specific date notification: {e}")

    def send_consistency_reminder(self):
        """Send consistency reminder if no activity logged today"""
        try:
            if not os.path.exists("lifetracker.csv"):
                # No data at all - send encouragement
                title = "Start Tracking!"
                message = "Start tracking your activities today to build better habits!"
                print("Sending start tracking reminder")
                self.send_termux_notification(title, message)
                return
            
            # Check if activity was logged today
            today = datetime.now().strftime("%d-%m-%Y")
            with open("lifetracker.csv", "r") as f:
                reader = csv.reader(f)
                has_today_activity = any(row[0] == today for row in reader)
            
            print(f"Today {today} - Activity logged: {has_today_activity}")
            
            if not has_today_activity:
                title = "Activity Reminder"
                message = "Don't forget to log your activities for today!"
                self.send_termux_notification(title, message)
            else:
                print("Activity already logged today")
                
        except Exception as e:
            print(f"Error in consistency reminder: {e}")

    def test_notification(self):
        """Test notification endpoint"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            notification_type = data.get('type', 'test')
            title = data.get('title', 'Test Notification')
            message = data.get('message', 'This is a test notification from Life Tracker')
            
            print(f"Testing notification: {title} - {message}")
            
            success = self.send_termux_notification(title, message)
            
            if success:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Test notification sent successfully"
                }).encode())
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Failed to send test notification. Make sure Termux API is installed and accessible."
                }).encode())
                
        except Exception as e:
            print(f"Error in test notification: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error sending test notification: {str(e)}"
            }).encode())

    def send_custom_notification(self):
        """Send custom notification immediately"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            title = data.get('title', 'Life Tracker')
            message = data.get('message', 'Custom notification')
            
            print(f"Sending custom notification: {title} - {message}")
            
            success = self.send_termux_notification(title, message)
            
            if success:
                self.send_success_response("Custom notification sent successfully")
            else:
                self.send_error_response("Failed to send custom notification. Check Termux API installation.")
                
        except Exception as e:
            print(f"Error in custom notification: {e}")
            self.send_error_response(f"Error sending custom notification: {str(e)}")

    def reset_notification_settings(self):
        """Reset notification settings to defaults"""
        try:
            default_settings = {
                'daily_report_enabled': False,
                'daily_report_time': '09:00',
                'todo_reminder_enabled': False,
                'todo_reminder_time': '18:00',
                'goal_reminder_enabled': False,
                'goal_reminder_time': '20:00',
                'specific_date_enabled': False,
                'specific_date': '',
                'specific_date_time': '10:00',
                'specific_date_title': '',
                'specific_date_message': '',
                'consistency_reminder_enabled': False,
                'consistency_reminder_time': '21:00'
            }
            
            with open("notifications.json", "w") as f:
                json.dump(default_settings, f, indent=2)
            
            # Stop scheduler since all notifications are disabled
            self.stop_notification_scheduler()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Notification settings reset to defaults"
            }).encode())
            
        except Exception as e:
            print(f"Error resetting notification settings: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error resetting notification settings: {str(e)}"
            }).encode())


    def get_performance_data(self):
        """Get performance data for charts"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            # Read data
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            
            # Last 30 days data for trends
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            recent_data = df[(df['date_obj'] >= start_date) & (df['date_obj'] <= end_date)]
            
            # Daily trends
            daily_trends = recent_data.groupby('date_obj')['minutes'].sum()
            daily_labels = [date.strftime('%Y-%m-%d') for date in daily_trends.index]
            daily_values = [int(val) for val in daily_trends.values]
            
            # Category distribution for pie chart
            category_dist = df.groupby('category')['minutes'].sum().sort_values(ascending=False).head(8)
            category_labels = list(category_dist.index)
            category_values = [int(val) for val in category_dist.values]
            
            # Weekly performance
            df['week'] = df['date_obj'].dt.to_period('W')
            weekly_performance = df.groupby('week')['minutes'].sum().tail(12)
            weekly_labels = [f"Week {i+1}" for i in range(len(weekly_performance))]
            weekly_values = [int(val) for val in weekly_performance.values]
            
            performance_data = {
                "status": "success",
                "charts": {
                    "daily_trends": {
                        "labels": daily_labels,
                        "values": daily_values
                    },
                    "category_distribution": {
                        "labels": category_labels,
                        "values": category_values
                    },
                    "weekly_performance": {
                        "labels": weekly_labels,
                        "values": weekly_values
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(performance_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error getting performance data: {str(e)}"
            }).encode())
    
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

# HTML UI with all functionality restored and improved collapsible sections
html_content = """
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
            --danger-dark: #D70015;
            --warning-color: #FF9500;
            --warning-dark: #CC7A00;
            --success-color: #34C759;
            --success-dark: #00A729;
            --gray-color: #8E8E93;
            --gray-dark: #6C6C70;
            --light-bg: rgba(255, 255, 255, 0.8);
            --card-bg: rgba(255, 255, 255, 0.9);
            --border-color: rgba(0, 0, 0, 0.1);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            --radius: 12px;
            --blur: blur(20px);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            background-attachment: fixed;
        }
        
        .container {
            background: var(--light-bg);
            backdrop-filter: var(--blur);
            -webkit-backdrop-filter: var(--blur);
            padding: 30px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }
        
        .section { 
            margin: 20px 0; 
            padding: 20px; 
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .section.collapsed {
            padding: 15px 20px;
            max-height: 70px;
            overflow: hidden;
        }
        
        .section.collapsed .section-content {
            display: none;
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding-bottom: 15px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }
        
        .section-actions {
            display: flex;
            gap: 8px;
        }
        
        .toggle-btn {
            background: var(--gray-color);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 3px 12px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
            align-self: flex-start;
            #margin-top: 0;
        }
        
        .toggle-btn:hover {
            background: var(--gray-dark);
        }
        
        .section:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }
        
        input, select, button { 
            padding: 14px 16px; 
            margin: 8px 0; 
            width: 100%; 
            border: 1px solid var(--border-color);
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
            background: white;
        }
        
        button { 
            background: var(--primary-color); 
            color: white; 
            border: none; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.2px;
            transition: all 0.3s ease;
        }
        
        button:hover { 
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 122, 255, 0.3);
        }
        
        .result { 
            padding: 16px; 
            margin: 12px 0; 
            border-radius: 10px; 
            font-size: 14px;
            border-left: 4px solid transparent;
            background: white;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .success { 
            background: rgba(52, 199, 89, 0.1); 
            color: #1F7D36; 
            border-left-color: var(--success-color);
        }
        
        .error { 
            background: rgba(255, 59, 48, 0.1); 
            color: #D70015; 
            border-left-color: var(--danger-color);
        }
        
        .warning { 
            background: rgba(255, 149, 0, 0.1); 
            color: #CC7A00; 
            border-left-color: var(--warning-color);
        }
        
        .info { 
            background: rgba(0, 122, 255, 0.1); 
            color: #0056CC; 
            border-left-color: var(--primary-color);
        }
        
        .summary { 
            background: rgba(88, 86, 214, 0.05); 
            color: #38376B; 
            border-left: 4px solid var(--secondary-color);
            white-space: pre-wrap;
            font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            padding: 16px;
        }
        
        h1 { 
            color: #1D1D1F; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.4em;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        h2 { 
            color: #1D1D1F; 
            padding-bottom: 12px; 
            margin-bottom: 20px;
            font-weight: 600;
            font-size: 1.4em;
        }
        
        h3 {
            color: #1D1D1F;
            margin-bottom: 15px;
            font-weight: 600;
            font-size: 1.2em;
        }
        
        .new-category { display: none; margin-top: 10px; }
        
        .today-btn { 
            background: var(--secondary-color); 
            padding: 12px 20px; 
            margin: 8px 0; 
            font-size: 14px; 
            width: auto; 
            border-radius: 10px;
        }
        
        .today-btn:hover {
            background: #4746B3;
        }
        
        .preview-btn {
            background: var(--secondary-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 10px 18px;
            border-radius: 8px;
        }
        
        .summary-btn {
            background: var(--gray-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 10px 18px;
            border-radius: 8px;
        }
        
        .summary-btn:hover { background: var(--gray-dark); }
        
        .minimize-btn {
            background: var(--danger-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 10px 18px;
            border-radius: 8px;
        }
        
        .minimize-btn:hover { background: var(--danger-dark); }
        
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
            justify-content: center;
        }
        
        .summary-section {
            margin-top: 20px;
            display: none;
        }
        
        .data-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            font-size: 14px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .data-table th, .data-table td {
            border: none;
            padding: 14px 12px;
            text-align: left;
            background: white;
        }
        
        .data-table th {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
        
        .data-table tr:nth-child(even) td {
            background: rgba(0, 0, 0, 0.02);
        }
        
        .data-table tr:hover td {
            background: rgba(0, 122, 255, 0.05);
        }
        
        .action-btn {
            padding: 8px 14px;
            margin: 0 4px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .edit-btn {
            background: var(--warning-color);
            color: white;
        }
        
        .edit-btn:hover {
            background: var(--warning-dark);
            transform: translateY(-1px);
        }
        
        .delete-btn-sm {
            background: var(--danger-color);
            color: white;
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            margin-left: 5px;
        }
        
        .delete-btn-sm:hover {
            background: var(--danger-dark);
            transform: translateY(-1px);
        }
        
        .stats-card {
            background: linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, rgba(88, 86, 214, 0.1) 100%);
            padding: 20px;
            border-radius: var(--radius);
            margin-bottom: 20px;
            border-left: 4px solid var(--primary-color);
            font-size: 14px;
            text-align: center;
        }
        
        .filter-section {
            background: var(--card-bg);
            padding: 24px;
            border-radius: var(--radius);
            margin-bottom: 24px;
            border: 1px solid var(--border-color);
        }
        
        .centered-form {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            width: 100%;
        }
        
        .centered-controls {
            display: flex;
            gap: 16px;
            justify-content: center;
            align-items: end;
            flex-wrap: wrap;
            width: 100%;
            max-width: 600px;
        }
        
        .centered-controls .filter-group {
            flex: 1;
            min-width: 160px;
            max-width: 280px;
            text-align: center;
        }
        
        .centered-controls button {
            width: auto;
            min-width: 130px;
            flex-shrink: 0;
        }
        
        .filter-label {
            font-size: 13px;
            color: var(--gray-dark);
            margin-bottom: 8px;
            display: block;
            font-weight: 500;
        }
        
        .date-filter-buttons {
            display: flex;
            gap: 16px;
            margin-top: 20px;
            justify-content: center;
            width: 100%;
            max-width: 600px;
        }
        
        .date-filter-buttons button {
            flex: 1;
            max-width: 200px;
        }
        
        .date-input-group {
            display: flex;
            gap: 12px;
            align-items: center;
            justify-content: center;
            width: 100%;
            max-width: 600px;
        }
        
        .date-input-group input {
            flex: 1;
            max-width: 400px;
        }
        
        .table-hidden {
            display: none;
        }
        
        .table-visible {
            display: table;
        }
        
        #noDataMessage {
            text-align: center;
            padding: 60px 20px;
            color: var(--gray-color);
            background: var(--light-bg);
            border-radius: var(--radius);
            border: 2px dashed var(--border-color);
        }
        
        #noDataMessage div:first-child {
            font-size: 48px;
            margin-bottom: 15px;
            opacity: 0.3;
        }
        
        #noDataMessage div:nth-child(2) {
            font-size: 18px;
            margin-bottom: 10px;
            font-weight: 500;
            color: var(--gray-dark);
        }
        
        #noDataMessage div:last-child {
            font-size: 14px;
            opacity: 0.7;
        }
        
        #searchPrompt {
            text-align: center;
            padding: 50px 20px;
            color: var(--gray-color);
            background: var(--light-bg);
            border-radius: var(--radius);
            border: 2px dashed var(--border-color);
        }
        
        #searchPrompt div:first-child {
            font-size: 36px;
            margin-bottom: 15px;
            opacity: 0.4;
        }
        
        #searchPrompt div:nth-child(2) {
            font-size: 16px;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        #searchPrompt div:last-child {
            font-size: 13px;
            opacity: 0.7;
        }
        
        .validation-issues {
            max-height: 200px;
            overflow-y: auto;
            background: var(--light-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
        }
        
        .validation-issue {
            font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
            font-size: 11px;
            padding: 6px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }
        
        .analytics-card {
            background: white;
            padding: 20px;
            border-radius: var(--radius);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            text-align: center;
            border-top: 4px solid var(--primary-color);
        }
        
        .analytics-value {
            font-size: 2em;
            font-weight: 700;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        .analytics-label {
            font-size: 0.9em;
            color: var(--gray-dark);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: var(--radius);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin: 20px 0;
        }
        
        .chart-placeholder {
            height: 200px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--gray-color);
            font-size: 14px;
            padding: 20px;
            overflow-y: auto;
        }
        
        .chart-placeholder div {
            margin: 2px 0;
            padding: 2px 0;
        }
        
        .export-options {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
            margin: 20px 0;
        }
        
        .export-btn {
            background: var(--success-color);
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-family: inherit;
            font-size: 14px;
        }
        
        .export-btn:hover {
            background: var(--success-dark);
            transform: translateY(-2px);
        }
        
        .advanced-filter-section {
            background: var(--light-bg);
            padding: 20px;
            border-radius: var(--radius);
            margin: 20px 0;
            border: 1px solid var(--border-color);
        }
        
        .goals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .goal-card {
            background: white;
            padding: 20px;
            border-radius: var(--radius);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border-left: 4px solid var(--primary-color);
        }
        
        .goal-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        
        .goal-title {
            flex: 1;
            font-weight: 600;
            font-size: 1.1em;
            color: #1D1D1F;
        }
        
        .goal-type {
            background: var(--gray-color);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        
        .goal-progress {
            margin: 15px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--success-color);
            transition: width 0.3s ease;
        }
        
        .progress-text {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: var(--gray-dark);
            margin-top: 5px;
        }
        
        .goal-actions {
            display: flex;
            gap: 8px;
            margin-top: 15px;
        }
        
        .chart-canvas {
            width: 100%;
            height: 200px;
            background: white;
            border-radius: 8px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: var(--radius);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: var(--gray-dark);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-change {
            font-size: 0.8em;
            margin-top: 5px;
        }
        
        .positive {
            color: var(--success-color);
        }
        
        .negative {
            color: var(--danger-color);
        }
        
        .global-controls {
            display: none !important;
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background: var(--card-bg);
            border-radius: var(--radius);
            border: 1px solid var(--border-color);
        }
        
        .global-controls button {
            width: auto;
            min-width: 140px;
            padding: 12px 20px;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 15px;
            }
            
            .container {
                padding: 20px;
            }
            
            .section {
                margin: 15px 0;
                padding: 15px;
            }
            
            .section.collapsed {
                padding: 12px 15px;
                max-height: 60px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            h2 {
                font-size: 1.3em;
            }
            
            .centered-controls {
                flex-direction: column;
                gap: 12px;
            }
            
            .centered-controls .filter-group {
                max-width: none;
                width: 100%;
            }
            
            .centered-controls button {
                width: 100%;
                min-width: auto;
            }
            
            .date-filter-buttons {
                flex-direction: column;
                gap: 12px;
            }
            
            .date-filter-buttons button {
                max-width: none;
                width: 100%;
            }
            
            .date-input-group {
                flex-direction: column;
            }
            
            .date-input-group input {
                max-width: none;
            }
            
            .date-input-group .today-btn {
                width: 100%;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .data-table {
                font-size: 12px;
            }
            
            .data-table th, .data-table td {
                padding: 12px 8px;
            }
            
            input, select, button {
                padding: 16px;
            }
            
            .stats-card {
                padding: 16px;
            }
            
            .analytics-grid {
                grid-template-columns: 1fr;
            }
            
            .export-options {
                flex-direction: column;
            }
            
            .goals-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .global-controls {
                display: none !important;
                flex-direction: column;
                gap: 10px;
            }
            
            .global-controls button {
                width: 100%;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 15px;
            }
            
            .section {
                padding: 12px;
            }
            
            .section.collapsed {
                padding: 10px 12px;
                max-height: 55px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .data-table {
                font-size: 11px;
            }
            
            .action-btn, .delete-btn-sm {
                padding: 6px 10px;
                font-size: 11px;
                margin: 2px;
            }
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .section-content {
            transition: all 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Life Tracker</h1>
        <div id="ai-chat-section">
            <form id="aiChatForm">
                <input type="text" id="aiChatInput" placeholder="Ask Life Tracker anything..." />
                <button type="submit">Send</button>
            </form>
            <div id="aiChatReply"></div>
        </div>
        <script>
        document.getElementById('aiChatForm').onsubmit = async function(e){
            e.preventDefault();
            const message = document.getElementById('aiChatInput').value;
            const resp = await fetch('/ai_chat', {
            method: 'POST',
            body: new URLSearchParams({message}),
            });
            const result = await resp.json();
            document.getElementById('aiChatReply').innerText = result.reply;
        }
        </script>

        <button onclick="openClockApp()">Open Clock</button>
        <script>
            function openClockApp() {
    // Fire and forget - don't wait for response
                 fetch('/open_clock')
                    .then(res => res.json())
                    .then(data => {
            // Optional: log success but don't show to user
                    console.log('Clock app status:', data.status);
                    })
                    .catch(err => {
            // Silently ignore network errors
                        console.log('Background request failed:', err);
        });
    
    // Always show success message immediately
            alert('Opening clock app...');
    
    // Optional: Show final confirmation after delay
            setTimeout(() => {
               alert('Clock app should be open now!');
            }, 1000);
        }
        </script>
        <!-- Global Controls -->
        <div class="global-controls">
            <button onclick="expandAllSections()" style="background: var(--success-color);">Expand All Sections</button>
            <button onclick="collapseAllSections()" style="background: var(--gray-color);">Collapse All Sections</button>
        </div>
        
        <!-- Add New Entry Section -->
        <div class="section" id="addEntrySection">
            <div class="section-header" onclick="toggleSection('addEntrySection')">
                <div class="section-title">
                    <h2>Add New Entry</h2>
                </div>
            </div>
            <div class="section-content">
                <form onsubmit="addEntry(event)" class="centered-form">
                    <div class="date-input-group">
                        <input type="date" id="dateInput" required>
                        <button type="button" class="today-btn" onclick="setToday()">Today</button>
                    </div>
                    <input type="text" name="activity" placeholder="Activity" required style="max-width: 600px;">
                    <input type="number" name="minutes" placeholder="Minutes" required style="max-width: 600px;">
                    
                    <select id="categorySelect" onchange="handleCategoryChange()" required style="max-width: 600px;">
                        <option value="">Select Category</option>
                    </select>
                    
                    <div id="newCategoryDiv" class="new-category" style="max-width: 600px; width: 100%;">
                        <input type="text" id="newCategoryInput" placeholder="Enter new category">
                    </div>
                    
                    <button type="submit" style="max-width: 600px;">Add Entry</button>
                </form>
                <div id="addResult"></div>
            </div>
        </div>
        
        <!-- Generate Reports Section -->
        <div class="section" id="reportsSection">
            <div class="section-header" onclick="toggleSection('reportsSection')">
                <div class="section-title">
                    <h2>Generate Reports</h2>
                </div>
            </div>
            <div class="section-content">
                <form class="centered-form">
                    <select id="reportType" style="max-width: 600px;">
                        <option value="daily">Daily Time Utilization</option>
                        <option value="category">Category-wise Time</option>
                        <option value="activity">Activity Statistics</option>
                        <option value="cattree">Category Tree Summary</option>
                    </select>
                    <div class="centered-controls">
                        <div class="filter-group">
                            <span class="filter-label">Month</span>
                            <input type="number" id="month" placeholder="Month (1-12)" min="1" max="12" required>
                        </div>
                        <div class="filter-group">
                            <span class="filter-label">Year</span>
                            <input type="number" id="year" placeholder="Year" min="2000" max="2100" required>
                        </div>
                    </div>
                    <button type="button" onclick="generateReport()" style="max-width: 600px;">Generate Report</button>
                </form>
                
                <div id="reportResult"></div>
                
                <div id="summarySection" class="summary-section">
                    <h3>Report Summary</h3>
                    <div id="summaryContent" class="result summary"></div>
                </div>
            </div>
        </div>
        
        <!-- Analytics Dashboard Section -->
        <div class="section" id="analyticsSection">
            <div class="section-header" onclick="toggleSection('analyticsSection')">
                <div class="section-title">
                    <h2>Analytics Dashboard</h2>
                </div>
            </div>
            <div class="section-content">
                <div class="button-group">
                    <button onclick="loadBasicAnalytics()">Basic Analytics</button>
                    <button onclick="showAdvancedAnalytics()" style="background: var(--secondary-color);">Advanced Analytics</button>
                    <button onclick="showExportSection()" style="background: var(--success-color);">Export Data</button>
                </div>
                
                <div id="analyticsResult"></div>
                <div id="analyticsDashboard"></div>
                
                <div id="advancedAnalyticsSection" style="display: none;">
                    <div class="advanced-filter-section">
                        <h3>Advanced Analytics Filters</h3>
                        <div class="centered-form">
                            <div class="centered-controls">
                                <div class="filter-group">
                                    <span class="filter-label">Start Date</span>
                                    <input type="date" id="analyticsStartDate">
                                </div>
                                <div class="filter-group">
                                    <span class="filter-label">End Date</span>
                                    <input type="date" id="analyticsEndDate">
                                </div>
                            </div>
                            <div class="centered-controls">
                                <div class="filter-group">
                                    <span class="filter-label">Category Filter</span>
                                    <input type="text" id="analyticsCategory" placeholder="Filter by category">
                                </div>
                                <div class="filter-group">
                                    <span class="filter-label">Activity Filter</span>
                                    <input type="text" id="analyticsActivity" placeholder="Filter by activity">
                                </div>
                            </div>
                            <button type="button" onclick="loadAdvancedAnalytics()" style="max-width: 400px;">Generate Advanced Analytics</button>
                        </div>
                    </div>
                    <div id="advancedAnalyticsResult"></div>
                </div>
                
                <div id="exportSection" style="display: none;">
                    <div class="advanced-filter-section">
                        <h3>Export Data</h3>
                        <p>Choose your preferred export format:</p>
                        <div class="export-options">
                            <button onclick="exportData('csv')" class="export-btn">Export as CSV</button>
                            <button onclick="exportData('json')" class="export-btn">Export as JSON</button>
                            <button onclick="exportData('excel')" class="export-btn">Export as Excel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Performance Overview Section -->
        <div class="section" id="performanceSection">
            <div class="section-header" onclick="toggleSection('performanceSection')">
                <div class="section-title">
                    <h2>Performance Overview</h2>
                </div>
                <div class="section-actions">
                    <button class="toggle-btn" onclick="event.stopPropagation(); loadPerformanceData()">Refresh</button>
                </div>
            </div>
            <div class="section-content">
                <div id="performanceResult"></div>
                <div id="performanceDashboard"></div>
            </div>
        </div>
        
        <!-- Goals System Section -->
        <div class="section" id="goalsSection">
            <div class="section-header" onclick="toggleSection('goalsSection')">
                <div class="section-title">
                    <h2>Goals System</h2>
                </div>
                <div class="section-actions">
                    <button class="toggle-btn" onclick="event.stopPropagation(); showGoalForm()">New</button>
                    <button class="toggle-btn" onclick="event.stopPropagation(); updateAllGoalProgress()">Update</button>
                </div>
            </div>
            <div class="section-content">
                <div id="goalsResult"></div>
                <div id="goalsDashboard"></div>
                
                <div id="goalFormSection" style="display: none;">
                    <div class="advanced-filter-section">
                        <h3>Create New Goal</h3>
                        <form id="goalForm" class="centered-form">
                            <input type="hidden" id="goalId">
                            <input type="text" id="goalTitle" placeholder="Goal Title" required style="max-width: 400px;">
                            <select id="goalType" required style="max-width: 400px;">
                                <option value="">Select Goal Type</option>
                                <option value="category">Category Minutes</option>
                                <option value="total_minutes">Total Minutes</option>
                                <option value="consistency">Consistency (Days)</option>
                            </select>
                            <select id="goalCategory" style="max-width: 400px; display: none;">
                                <option value="">Select Category</option>
                            </select>
                            <select id="goalPeriod" required style="max-width: 400px;">
                                <option value="">Select Period</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                            <input type="number" id="goalTarget" placeholder="Target Value" required style="max-width: 400px;">
                            <div style="display: flex; gap: 12px; width: 100%; max-width: 400px;">
                                <button type="submit" style="flex: 1;">Save Goal</button>
                                <button type="button" onclick="hideGoalForm()" style="flex: 1; background: var(--gray-color);">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Manage Data Section -->
        <div class="section" id="manageDataSection">
            <div class="section-header" onclick="toggleSection('manageDataSection')">
                <div class="section-title">
                    <h2>Query & Manage Data</h2>
                </div>
            </div>
            <div class="section-content">
                <div class="filter-section">
                    <div class="centered-form">
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Search Activities & Categories</span>
                                <input type="text" id="searchInput" placeholder="Enter activity or category name">
                            </div>
                            <button type="button" onclick="searchData()">Search</button>
                            <button type="button" onclick="loadAllData()" style="background: var(--gray-color);">Show All</button>
                        </div>
                    </div>
                    
                    <div class="centered-form">
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">From Date</span>
                                <input type="date" id="filterDateFrom">
                            </div>
                            <div class="filter-group">
                                <span class="filter-label">To Date</span>
                                <input type="date" id="filterDateTo">
                            </div>
                        </div>
                        
                        <div class="date-filter-buttons">
                            <button type="button" onclick="filterByDateRange()">Filter by Date Range</button>
                            <button type="button" onclick="clearDateFilters()" style="background: var(--danger-color);">Clear Filters</button>
                        </div>
                    </div>
                </div>
                
                <div id="statsSummary" class="stats-card" style="display: none;">
                    <strong>Summary:</strong> 
                    <span id="totalEntries">0 entries</span> | 
                    <span id="totalMinutes">0 minutes</span> | 
                    <span id="dateRange">All dates</span>
                </div>
                
                <div id="tableContainer" style="overflow-x: auto; max-height: 500px; overflow-y: auto;">
                    <div id="searchPrompt">
                        <div>Search</div>
                        <div>Search or filter to view data</div>
                        <div>Use the search box or date filters above to display entries</div>
                    </div>
                    
                    <div id="noDataMessage" style="display: none;">
                        <div>No Data</div>
                        <div>No matching entries found</div>
                        <div>Try different search terms or date range</div>
                    </div>
                    
                    <table id="dataTable" class="data-table table-hidden">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Activity</th>
                                <th>Minutes</th>
                                <th>Category</th>
                                <th style="text-align: center; width: 140px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="tableBody">
                        </tbody>
                    </table>
                </div>
                
                <div id="editModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center;">
                    <div style="background: white; padding: 30px; border-radius: var(--radius); width: 95%; max-width: 500px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); backdrop-filter: var(--blur);">
                        <h3 style="margin-bottom: 25px; color: #1D1D1F; text-align: center; font-size: 1.3em;">Edit Entry</h3>
                        <form id="editForm" class="centered-form">
                            <input type="hidden" id="editIndex">
                            <input type="date" id="editDate" required style="max-width: 400px;">
                            <input type="text" id="editActivity" placeholder="Activity" required style="max-width: 400px;">
                            <input type="number" id="editMinutes" placeholder="Minutes" required style="max-width: 400px;">
                            <input type="text" id="editCategory" placeholder="Category" required style="max-width: 400px;">
                            <div style="display: flex; gap: 12px; margin-top: 25px; width: 100%; max-width: 400px;">
                                <button type="submit" style="flex: 1; background: var(--primary-color); padding: 14px;">Save Changes</button>
                                <button type="button" onclick="closeEditModal()" style="flex: 1; background: var(--gray-color); padding: 14px;">Cancel</button>
                                <button type="button" onclick="deleteEntry()" style="flex: 1; background: var(--danger-color); padding: 14px;">Delete Entry</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Data Management Section -->
        <div class="section" id="dataManagementSection">
            <div class="section-header" onclick="toggleSection('dataManagementSection')">
                <div class="section-title">
                    <h2>Data Management</h2>
                </div>
            </div>
            <div class="section-content">
                <div class="button-group">
                    <button onclick="createBackup()" style="background: var(--secondary-color);">Create Backup</button>
                    <button onclick="validateData()" style="background: var(--warning-color);">Validate Data</button>
                    <button onclick="showDataIntegrityInfo()" style="background: var(--gray-color);">Data Integrity Info</button>
                </div>
                <div id="dataManagementResult"></div>
            </div>
        </div>
                <!-- To-Do List Section -->
        <div class="section" id="todoSection">
            <div class="section-header" onclick="toggleSection('todoSection')">
                <div class="section-title">
                    <h2>To-Do List Manager</h2>
                </div>
                <div class="section-actions">
                    <button class="toggle-btn" onclick="event.stopPropagation(); showTodoForm()">New</button>
                    <button class="toggle-btn" onclick="event.stopPropagation(); loadAllTodos()">Refresh</button>
                </div>
            </div>
            <div class="section-content">
                <!-- Option 1: Data Entry Form -->
                <div id="todoFormSection" style="display: none;">
                    <div class="advanced-filter-section">
                        <h3>Add New Todo</h3>
                        <form id="todoForm" class="centered-form">
                            <input type="hidden" id="todoId">
                            <input type="text" id="todoActivity" placeholder="Activity/Description" required style="max-width: 400px;">
                            <input type="date" id="todoTargetDate" required style="max-width: 400px;">
                            <input type="text" id="todoCategory" placeholder="Category" required style="max-width: 400px;">
                            <select id="todoStatus" required style="max-width: 400px;">
                                <option value="pending">Pending</option>
                                <option value="completed">Completed</option>
                            </select>
                            <div style="display: flex; gap: 12px; width: 100%; max-width: 400px;">
                                <button type="submit" style="flex: 1;">Save Todo</button>
                                <button type="button" onclick="hideTodoForm()" style="flex: 1; background: var(--gray-color);">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Option 2: Query/Search Interface -->
                <div class="filter-section">
                    <h3>Search & Filter Todos</h3>
                    <div class="centered-form">
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Search Activity</span>
                                <input type="text" id="todoSearchActivity" placeholder="Enter activity name">
                            </div>
                            <div class="filter-group">
                                <span class="filter-label">Category</span>
                                <input type="text" id="todoSearchCategory" placeholder="Enter category">
                            </div>
                        </div>
                        
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Status</span>
                                <select id="todoSearchStatus" style="max-width: 200px;">
                                    <option value="">All Status</option>
                                    <option value="pending">Pending</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                            <button type="button" onclick="searchTodos()">Search Todos</button>
                            <button type="button" onclick="clearTodoFilters()" style="background: var(--gray-color);">Clear Filters</button>
                        </div>
                        
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Target Date From</span>
                                <input type="date" id="todoDateFrom">
                            </div>
                            <div class="filter-group">
                                <span class="filter-label">Target Date To</span>
                                <input type="date" id="todoDateTo">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Option 3: CRUD Operations Display -->
                <div id="todoStats" class="stats-card" style="display: none;">
                    <strong>Summary:</strong> 
                    <span id="totalTodos">0 todos</span> | 
                    <span id="pendingTodos">0 pending</span> | 
                    <span id="completedTodos">0 completed</span>
                </div>
                
                <div id="todoTableContainer" style="overflow-x: auto; max-height: 500px; overflow-y: auto;">
                    <div id="todoSearchPrompt">

                    </div>
                    
                    <div id="noTodosMessage" style="display: none;">
                        <div>No Todos</div>
                        <div>No matching todos found</div>
                        <div>Try different search terms or create a new todo</div>
                    </div>
                    
                    <table id="todoTable" class="data-table table-hidden">
                        <thead>
                            <tr>
                                <th>Date Created</th>
                                <th>Activity</th>
                                <th>Target Date</th>
                                <th>Category</th>
                                <th>Status</th>
                                <th style="text-align: center; width: 160px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="todoTableBody">
                        </tbody>
                    </table>
                </div>
                
                <div id="todoEditModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center;">
                    <div style="background: white; padding: 30px; border-radius: var(--radius); width: 95%; max-width: 500px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); backdrop-filter: var(--blur);">
                        <h3 style="margin-bottom: 25px; color: #1D1D1F; text-align: center; font-size: 1.3em;">Edit Todo</h3>
                        <form id="todoEditForm" class="centered-form">
                            <input type="hidden" id="editTodoId">
                            <input type="text" id="editTodoActivity" placeholder="Activity" required style="max-width: 400px;">
                            <input type="date" id="editTodoTargetDate" required style="max-width: 400px;">
                            <input type="text" id="editTodoCategory" placeholder="Category" required style="max-width: 400px;">
                            <select id="editTodoStatus" required style="max-width: 400px;">
                                <option value="pending">Pending</option>
                                <option value="completed">Completed</option>
                            </select>
                            <div style="display: flex; gap: 12px; margin-top: 25px; width: 100%; max-width: 400px;">
                                <button type="submit" style="flex: 1; background: var(--primary-color); padding: 14px;">Save Changes</button>
                                <button type="button" onclick="closeTodoEditModal()" style="flex: 1; background: var(--gray-color); padding: 14px;">Cancel</button>
                                <button type="button" onclick="deleteTodo()" style="flex: 1; background: var(--danger-color); padding: 14px;">Delete Todo</button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <div id="todoResult"></div>
            </div>
        </div>
        

        <!-- Notification Settings Section -->
        <div class="section" id="notificationSection">
            <div class="section-header" onclick="toggleSection('notificationSection')">
                <div class="section-title">
                    <h2>Notification Settings</h2>
                </div>
                <div class="section-actions">
                    <button class="toggle-btn" onclick="event.stopPropagation(); testNotification()">Test</button>
                </div>
            </div>
            <div class="section-content">
                <div id="notificationResult"></div>
                
                <div class="advanced-filter-section">
                    <h3>Daily Report Notifications</h3>
                    <div class="centered-form">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <input type="checkbox" id="dailyReportEnabled" style="width: auto;">
                            <label for="dailyReportEnabled">Enable Daily Time Utilization Report</label>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Notification Time</span>
                                <input type="time" id="dailyReportTime" value="09:00">
                            </div>
                        </div>
                        <div class="result info">
                            Sends monthly summary of your time utilization from generated reports
                        </div>
                    </div>
                </div>

                <div class="advanced-filter-section">
                    <h3>Todo Reminder Notifications</h3>
                    <div class="centered-form">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <input type="checkbox" id="todoReminderEnabled" style="width: auto;">
                            <label for="todoReminderEnabled">Enable Daily Todo Reminders</label>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Reminder Time</span>
                                <input type="time" id="todoReminderTime" value="18:00">
                            </div>
                        </div>
                        <div class="result info">
                            Daily reminder of pending todos with count and top items
                        </div>
                    </div>
                </div>

                <div class="advanced-filter-section">
                    <h3>Goal Progress Notifications</h3>
                    <div class="centered-form">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <input type="checkbox" id="goalReminderEnabled" style="width: auto;">
                            <label for="goalReminderEnabled">Enable Goal Progress Updates</label>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Reminder Time</span>
                                <input type="time" id="goalReminderTime" value="20:00">
                            </div>
                        </div>
                        <div class="result info">
                            Daily progress update on your active goals
                        </div>
                    </div>
                </div>

                <div class="advanced-filter-section">
                    <h3>Specific Date Notification</h3>
                    <div class="centered-form">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <input type="checkbox" id="specificDateEnabled" style="width: auto;">
                            <label for="specificDateEnabled">Enable Specific Date Reminder</label>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Notification Date</span>
                                <input type="date" id="specificDate">
                            </div>
                            <div class="filter-group">
                                <span class="filter-label">Notification Time</span>
                                <input type="time" id="specificDateTime" value="10:00">
                            </div>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group" style="flex: 2;">
                                <span class="filter-label">Notification Title</span>
                                <input type="text" id="specificDateTitle" placeholder="Reminder Title">
                            </div>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group" style="flex: 2;">
                                <span class="filter-label">Notification Message</span>
                                <input type="text" id="specificDateMessage" placeholder="Reminder Message">
                            </div>
                        </div>
                        <div class="result info">
                            One-time notification on a specific date and time
                        </div>
                    </div>
                </div>

                <div class="advanced-filter-section">
                    <h3>Consistency Reminder</h3>
                    <div class="centered-form">
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <input type="checkbox" id="consistencyReminderEnabled" style="width: auto;">
                            <label for="consistencyReminderEnabled">Enable Daily Activity Reminder</label>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group">
                                <span class="filter-label">Reminder Time</span>
                                <input type="time" id="consistencyReminderTime" value="21:00">
                            </div>
                        </div>
                        <div class="result info">
                            Reminds you to log activities if none recorded for the day
                        </div>
                    </div>
                </div>

                <div class="advanced-filter-section">
                    <h3>Custom Notification</h3>
                    <div class="centered-form">
                        <div class="centered-controls">
                            <div class="filter-group" style="flex: 2;">
                                <span class="filter-label">Title</span>
                                <input type="text" id="customNotificationTitle" placeholder="Notification Title" value="Life Tracker">
                            </div>
                        </div>
                        <div class="centered-controls">
                            <div class="filter-group" style="flex: 2;">
                                <span class="filter-label">Message</span>
                                <input type="text" id="customNotificationMessage" placeholder="Notification Message">
                            </div>
                        </div>
                        <button type="button" onclick="sendCustomNotification()" style="max-width: 300px;">
                            Send Custom Notification Now
                        </button>
                        <div class="result info">
                            Send an immediate custom notification (for testing or quick reminders)
                        </div>
                    </div>
                </div>

                <div class="button-group">
                    <button onclick="saveNotificationSettings()" style="background: var(--success-color);">
                        Save Notification Settings
                    </button>
                    <button onclick="loadNotificationSettings()" style="background: var(--secondary-color);">
                        Load Settings
                    </button>
                    <button onclick="resetNotificationSettings()" style="background: var(--warning-color);">
                        Reset to Defaults
                    </button>
                </div>

                <div class="result warning">
                    <strong>Requirements:</strong> Termux API must be installed and notifications permission granted.
                    Make sure to run: <code>pkg install termux-api</code> and enable notification permissions.
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentData = [];
        let filteredData = [];
        let currentDisplayedData = [];
        let hasSearched = false;
        let goals = [];
        
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            setToday();
            setCurrentYear();
            showSearchPrompt();
            loadGoals();
            loadPerformanceData();
            
            // Collapse all sections by default
            setTimeout(() => {
                collapseAllSections();
            }, 100);
        });
        
        // Section toggle functionality
        function toggleSection(sectionId) {
            const section = document.getElementById(sectionId);
            section.classList.toggle('collapsed');
        }
        
        function expandAllSections() {
            const sections = document.querySelectorAll('.section.collapsed');
            sections.forEach(section => {
                section.classList.remove('collapsed');
            });
        }
        
        function collapseAllSections() {
            const sections = document.querySelectorAll('.section:not(.collapsed)');
            sections.forEach(section => {
                section.classList.add('collapsed');
            });
        }
        
        // All original functionality restored
        function setToday() {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            document.getElementById('dateInput').value = formattedDate;
        }
        
        function setCurrentYear() {
            const currentYear = new Date().getFullYear();
            document.getElementById('year').value = currentYear;
        }
        
        function formatDateForCSV(dateString) {
            const parts = dateString.split('-');
            if (parts.length === 3) {
                return `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            return dateString;
        }
        
        function showSearchPrompt() {
            document.getElementById('searchPrompt').style.display = 'block';
            document.getElementById('noDataMessage').style.display = 'none';
            document.getElementById('dataTable').classList.remove('table-visible');
            document.getElementById('dataTable').classList.add('table-hidden');
            document.getElementById('statsSummary').style.display = 'none';
        }
        
        function showNoDataMessage() {
            document.getElementById('searchPrompt').style.display = 'none';
            document.getElementById('noDataMessage').style.display = 'block';
            document.getElementById('dataTable').classList.remove('table-visible');
            document.getElementById('dataTable').classList.add('table-hidden');
            document.getElementById('statsSummary').style.display = 'none';
        }
        
        function showDataTable() {
            document.getElementById('searchPrompt').style.display = 'none';
            document.getElementById('noDataMessage').style.display = 'none';
            document.getElementById('dataTable').classList.remove('table-hidden');
            document.getElementById('dataTable').classList.add('table-visible');
        }
        
        async function loadCategories() {
            try {
                const response = await fetch('/get_categories');
                const categories = await response.json();
                const select = document.getElementById('categorySelect');
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }
                categories.forEach(cat => {
                    const option = new Option(cat, cat);
                    select.appendChild(option);
                });
                const newOption = new Option("+ Add New Category", "new");
                select.appendChild(newOption);
            } catch (error) {
                console.error('Error loading categories:', error);
            }
        }
        
        function handleCategoryChange() {
            const select = document.getElementById('categorySelect');
            const newCategoryDiv = document.getElementById('newCategoryDiv');
            const newCategoryInput = document.getElementById('newCategoryInput');
            if (select.value === 'new') {
                newCategoryDiv.style.display = 'block';
                newCategoryInput.required = true;
            } else {
                newCategoryDiv.style.display = 'none';
                newCategoryInput.required = false;
            }
        }
        
        async function addEntry(event) {
            event.preventDefault();
            
            const dateInput = document.getElementById('dateInput');
            const activity = document.querySelector('input[name="activity"]').value;
            const minutes = document.querySelector('input[name="minutes"]').value;
            
            if (!dateInput.value) {
                alert('Please select a date');
                return;
            }
            
            if (!activity.trim()) {
                alert('Please enter an activity');
                return;
            }
            
            if (!minutes || parseInt(minutes) <= 0) {
                alert('Please enter valid minutes');
                return;
            }
            
            const formattedDate = formatDateForCSV(dateInput.value);
            const formData = new FormData();
            formData.append('date', formattedDate);
            formData.append('activity', activity);
            formData.append('minutes', minutes);
            const categorySelect = document.getElementById('categorySelect');
            const newCategoryInput = document.getElementById('newCategoryInput');
            let category;
            if (categorySelect.value === 'new') {
                category = newCategoryInput.value.trim();
                if (!category) {
                    alert('Please enter a new category');
                    return;
                }
            } else {
                category = categorySelect.value;
            }
            formData.append('category', category);
            
            try {
                const response = await fetch('/add_entry', { method: 'POST', body: formData });
                const result = await response.json();
                const resultDiv = document.getElementById('addResult');
                if (result.status === 'success') {
                    resultDiv.innerHTML = '<div class="result success">' + result.message + '</div>';
                    document.querySelector('input[name="activity"]').value = '';
                    document.querySelector('input[name="minutes"]').value = '';
                    document.getElementById('newCategoryDiv').style.display = 'none';
                    categorySelect.value = '';
                    loadCategories();
                    // Clear current data to force refresh on next view
                    currentData = [];
                    filteredData = [];
                    showSearchPrompt();
                } else {
                    resultDiv.innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch {
                document.getElementById('addResult').innerHTML = '<div class="result error">Network error</div>';
            }
        }
        
        async function generateReport() {
            const reportType = document.getElementById('reportType').value;
            const month = document.getElementById('month').value;
            const year = document.getElementById('year').value;
            
            if (!month) {
                alert('Please enter a month');
                return;
            }
            if (!year) {
                alert('Please enter a year');
                return;
            }
            
            const monthInt = parseInt(month);
            const yearInt = parseInt(year);
            
            if (monthInt < 1 || monthInt > 12) {
                alert('Month must be between 1 and 12');
                return;
            }
            
            if (yearInt < 2000 || yearInt > 2100) {
                alert('Year must be between 2000 and 2100');
                return;
            }
            
            const formData = new FormData();
            formData.append('report_type', reportType);
            formData.append('month', month);
            formData.append('year', year);
            
            const button = document.querySelector('button[onclick="generateReport()"]');
            const originalText = button.textContent;
            button.textContent = 'Generating...';
            button.disabled = true;
            
            document.getElementById('summarySection').style.display = 'none';
            
            try {
                const response = await fetch('/run_report', { method: 'POST', body: formData });
                const result = await response.json();
                const resultDiv = document.getElementById('reportResult');
                const summarySection = document.getElementById('summarySection');
                const summaryContent = document.getElementById('summaryContent');
                
                if (result.status === 'success') {
                    resultDiv.innerHTML = 
                        '<div class="result success">Report generated successfully for ' + month + '/' + year + '!</div>' +
                        '<div class="button-group">' +
                        '<a href="' + result.output + '" target="_blank">' +
                        '<button class="preview-btn">Preview Chart</button></a>';
                    
                    if (result.summary && result.summary.trim()) {
                        resultDiv.innerHTML += 
                            '<button class="summary-btn" onclick="toggleSummary()">View Summary</button>' +
                            '<button class="minimize-btn" onclick="minimizeSummary()">Minimize</button>';
                        summaryContent.textContent = result.summary;
                        summarySection.style.display = 'block';
                    }
                    
                    resultDiv.innerHTML += '</div>';
                } else {
                    resultDiv.innerHTML = '<div class="result error">Error: ' + result.output + '</div>';
                    if (result.summary && result.summary.trim()) {
                        summaryContent.textContent = result.summary;
                        summarySection.style.display = 'block';
                        resultDiv.innerHTML += 
                            '<button class="minimize-btn" onclick="minimizeSummary()">Minimize</button>';
                    }
                }
            } catch {
                document.getElementById('reportResult').innerHTML = '<div class="result error">Network error</div>';
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        function toggleSummary() {
            const summarySection = document.getElementById('summarySection');
            if (summarySection.style.display === 'none') {
                summarySection.style.display = 'block';
            } else {
                summarySection.style.display = 'none';
            }
        }
        
        function minimizeSummary() {
            document.getElementById('summarySection').style.display = 'none';
        }
        
        async function loadAllData() {
            try {
                const response = await fetch('/get_all_data');
                const result = await response.json();
                
                if (result.status === 'success' && result.data.length > 0) {
                    currentData = result.data;
                    filteredData = currentData;
                    currentDisplayedData = currentData;
                    displayData(currentData);
                    updateStats(currentData);
                    hasSearched = true;
                } else {
                    showNoDataMessage();
                    hideStats();
                }
            } catch (error) {
                console.error('Error loading data:', error);
                showNoDataMessage();
                hideStats();
            }
        }
        
        function displayData(data) {
            const tableBody = document.getElementById('tableBody');
            
            currentDisplayedData = data;
            
            if (data.length === 0) {
                showNoDataMessage();
                hideStats();
                return;
            }
            
            tableBody.innerHTML = '';
            showDataTable();
            
            data.forEach((row, displayIndex) => {
                const tr = document.createElement('tr');
                
                const dateParts = row[0].split('-');
                const displayDate = dateParts.length === 3 ? 
                    `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` : row[0];
                
                const originalIndex = currentData.findIndex(originalRow => 
                    originalRow[0] === row[0] && 
                    originalRow[1] === row[1] && 
                    originalRow[2] === row[2] && 
                    originalRow[3] === row[3]
                );
                
                tr.innerHTML = `
                    <td>${displayDate}</td>
                    <td>${row[1] || ''}</td>
                    <td>${row[2] || ''}</td>
                    <td>${row[3] || ''}</td>
                    <td style="text-align: center;">
                        <button class="action-btn edit-btn" onclick="openEditModal(${originalIndex})">Edit</button>
                        <button class="delete-btn-sm" onclick="quickDelete(${originalIndex})">Delete</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
            
            updateStats(data);
        }
        
        function updateStats(data) {
            const totalEntries = data.length;
            const totalMinutes = data.reduce((sum, row) => sum + (parseInt(row[2]) || 0), 0);
            
            const dates = data.map(row => {
                const parts = row[0].split('-');
                return parts.length === 3 ? new Date(parts[2], parts[1]-1, parts[0]) : new Date();
            }).filter(date => !isNaN(date.getTime()));
            
            let dateRangeText = 'All dates';
            if (dates.length > 0) {
                const minDate = new Date(Math.min(...dates));
                const maxDate = new Date(Math.max(...dates));
                dateRangeText = `${minDate.toLocaleDateString()} - ${maxDate.toLocaleDateString()}`;
            }
            
            document.getElementById('totalEntries').textContent = `${totalEntries} entries`;
            document.getElementById('totalMinutes').textContent = `${totalMinutes} minutes`;
            document.getElementById('dateRange').textContent = dateRangeText;
            document.getElementById('statsSummary').style.display = 'block';
        }
        
        function hideStats() {
            document.getElementById('statsSummary').style.display = 'none';
        }
        
        async function searchData() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
            
            if (currentData.length === 0) {
                await loadAllData();
            }
            
            if (!searchTerm) {
                filteredData = currentData;
                displayData(currentData);
                updateStats(currentData);
                return;
            }
            
            filteredData = currentData.filter(row => {
                const activityMatch = row[1] && row[1].toLowerCase().includes(searchTerm);
                const categoryMatch = row[3] && row[3].toLowerCase().includes(searchTerm);
                return activityMatch || categoryMatch;
            });
            
            displayData(filteredData);
        }
        
        async function filterByDateRange() {
            const fromDate = document.getElementById('filterDateFrom').value;
            const toDate = document.getElementById('filterDateTo').value;
            
            if (currentData.length === 0) {
                await loadAllData();
            }
            
            if (!fromDate && !toDate) {
                filteredData = currentData;
                displayData(currentData);
                updateStats(currentData);
                return;
            }
            
            filteredData = currentData.filter(row => {
                const dateParts = row[0].split('-');
                if (dateParts.length !== 3) return false;
                
                const rowDate = new Date(dateParts[2], dateParts[1]-1, dateParts[0]);
                
                if (fromDate && toDate) {
                    const from = new Date(fromDate);
                    const to = new Date(toDate);
                    return rowDate >= from && rowDate <= to;
                } else if (fromDate) {
                    const from = new Date(fromDate);
                    return rowDate >= from;
                } else if (toDate) {
                    const to = new Date(toDate);
                    return rowDate <= to;
                }
                return true;
            });
            
            displayData(filteredData);
        }
        
        function clearDateFilters() {
            document.getElementById('filterDateFrom').value = '';
            document.getElementById('filterDateTo').value = '';
            document.getElementById('searchInput').value = '';
            currentData = [];
            filteredData = [];
            showSearchPrompt();
        }
        
        function openEditModal(originalIndex) {
            const row = currentData[originalIndex];
            
            if (!row) {
                alert('Error: Could not find the entry to edit');
                return;
            }
            
            const dateParts = row[0].split('-');
            const inputDate = dateParts.length === 3 ? 
                `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` : row[0];
            
            document.getElementById('editIndex').value = originalIndex;
            document.getElementById('editDate').value = inputDate;
            document.getElementById('editActivity').value = row[1] || '';
            document.getElementById('editMinutes').value = row[2] || '';
            document.getElementById('editCategory').value = row[3] || '';
            document.getElementById('editModal').style.display = 'flex';
        }
        
        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }
        
        async function quickDelete(originalIndex) {
            if (confirm('Are you sure you want to delete this entry?')) {
                try {
                    const response = await fetch('/delete_entry', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ index: parseInt(originalIndex) })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        // Clear data to force refresh
                        currentData = [];
                        filteredData = [];
                        if (document.getElementById('searchInput').value || 
                            document.getElementById('filterDateFrom').value || 
                            document.getElementById('filterDateTo').value) {
                            await loadAllData();
                        } else {
                            showSearchPrompt();
                        }
                    } else {
                        alert('Error deleting entry: ' + result.message);
                    }
                } catch (error) {
                    alert('Error deleting entry: ' + error);
                }
            }
        }
        
        async function deleteEntry() {
            const originalIndex = document.getElementById('editIndex').value;
            if (confirm('Are you sure you want to delete this entry?')) {
                try {
                    const response = await fetch('/delete_entry', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ index: parseInt(originalIndex) })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        closeEditModal();
                        currentData = [];
                        filteredData = [];
                        if (document.getElementById('searchInput').value || 
                            document.getElementById('filterDateFrom').value || 
                            document.getElementById('filterDateTo').value) {
                            await loadAllData();
                        } else {
                            showSearchPrompt();
                        }
                    } else {
                        alert('Error deleting entry: ' + result.message);
                    }
                } catch (error) {
                    alert('Error deleting entry: ' + error);
                }
            }
        }
        
        document.getElementById('editForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const originalIndex = document.getElementById('editIndex').value;
            const dateInput = document.getElementById('editDate').value;
            const formattedDate = formatDateForCSV(dateInput);
            const activity = document.getElementById('editActivity').value;
            const minutes = document.getElementById('editMinutes').value;
            const category = document.getElementById('editCategory').value;
            
            try {
                const response = await fetch('/update_entry', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        index: parseInt(originalIndex),
                        date: formattedDate,
                        activity: activity,
                        minutes: minutes,
                        category: category
                    })
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    closeEditModal();
                    currentData = [];
                    filteredData = [];
                    if (document.getElementById('searchInput').value || 
                        document.getElementById('filterDateFrom').value || 
                        document.getElementById('filterDateTo').value) {
                        await loadAllData();
                    } else {
                        showSearchPrompt();
                    }
                } else {
                    alert('Error updating entry: ' + result.message);
                }
            } catch (error) {
                alert('Error updating entry: ' + error);
            }
        });
        
        // Data Management Functions
        async function createBackup() {
            try {
                const response = await fetch('/create_backup', { method: 'POST' });
                const result = await response.json();
                const resultDiv = document.getElementById('dataManagementResult');
                
                if (result.status === 'success') {
                    resultDiv.innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    resultDiv.innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('dataManagementResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
            }
        }
        
        async function validateData() {
            try {
                const response = await fetch('/validate_data', { method: 'POST' });
                const result = await response.json();
                const resultDiv = document.getElementById('dataManagementResult');
                
                if (result.status === 'success') {
                    resultDiv.innerHTML = '<div class="result success">' + result.message + '</div>';
                } else if (result.status === 'warning') {
                    let issuesHtml = '<div class="result warning">' + result.message + '</div>';
                    issuesHtml += '<div class="validation-issues">';
                    result.issues.forEach(issue => {
                        issuesHtml += '<div class="validation-issue">' + issue + '</div>';
                    });
                    issuesHtml += '</div>';
                    resultDiv.innerHTML = issuesHtml;
                } else {
                    resultDiv.innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('dataManagementResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
            }
        }
        
        function showDataIntegrityInfo() {
            const resultDiv = document.getElementById('dataManagementResult');
            resultDiv.innerHTML = `
                <div class="result info">
                    <strong>Data Integrity Features:</strong><br>
                     Automatic backups before data modifications<br>
                     Date validation (DD-MM-YYYY format)<br>
                     Activity and category length limits<br>
                     Minutes validation (1-1440)<br>
                     Data integrity checking<br>
                     Automatic cleanup of old backups (keeps last 10)
                </div>
            `;
        }
        
        // Analytics Functions
        async function loadBasicAnalytics() {
            try {
                document.getElementById('analyticsResult').innerHTML = '<div class="result info">Loading analytics...</div>';
                
                const response = await fetch('/get_analytics');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                const dashboard = document.getElementById('analyticsDashboard');
                const resultDiv = document.getElementById('analyticsResult');
                
                if (result.status === 'success') {
                    const analytics = result.analytics;
                    
                    let html = `
                        <div class="analytics-grid">
                            <div class="analytics-card">
                                <div class="analytics-label">Total Entries</div>
                                <div class="analytics-value">${analytics.total_entries}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Total Minutes</div>
                                <div class="analytics-value">${analytics.total_minutes}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Categories</div>
                                <div class="analytics-value">${analytics.total_categories}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Activities</div>
                                <div class="analytics-value">${analytics.total_activities}</div>
                            </div>
                        </div>
                    `;
                    
                    // Add top categories chart
                    if (Object.keys(analytics.top_categories).length > 0) {
                        html += `
                            <div class="chart-container">
                                <h3>Top Categories</h3>
                                <div class="chart-placeholder">
                                    ${Object.entries(analytics.top_categories).map(([category, minutes]) => 
                                        `<div><strong>${category}</strong>: ${minutes} minutes</div>`
                                    ).join('')}
                                </div>
                            </div>
                        `;
                    }
                    
                    // Add recent activity chart
                    if (Object.keys(analytics.recent_activity).length > 0) {
                        html += `
                            <div class="chart-container">
                                <h3>Recent Activity (Last 7 Days)</h3>
                                <div class="chart-placeholder">
                                    ${Object.entries(analytics.recent_activity).map(([date, minutes]) => 
                                        `<div><strong>${date}</strong>: ${minutes} minutes</div>`
                                    ).join('')}
                                </div>
                            </div>
                        `;
                    }
                    
                    dashboard.innerHTML = html;
                    resultDiv.innerHTML = '<div class="result success">Analytics loaded successfully</div>';
                    
                    // Hide other sections
                    document.getElementById('advancedAnalyticsSection').style.display = 'none';
                    document.getElementById('exportSection').style.display = 'none';
                    
                } else {
                    resultDiv.innerHTML = '<div class="result error">' + (result.message || 'Error loading analytics') + '</div>';
                }
            } catch (error) {
                console.error('Analytics error:', error);
                document.getElementById('analyticsResult').innerHTML = '<div class="result error">Failed to load analytics: ' + error.message + '</div>';
            }
        }
        
        function showAdvancedAnalytics() {
            document.getElementById('advancedAnalyticsSection').style.display = 'block';
            document.getElementById('exportSection').style.display = 'none';
            document.getElementById('analyticsDashboard').innerHTML = '';
            document.getElementById('analyticsResult').innerHTML = '<div class="result info">Configure filters and generate advanced analytics</div>';
        }
        
        function showExportSection() {
            document.getElementById('exportSection').style.display = 'block';
            document.getElementById('advancedAnalyticsSection').style.display = 'none';
            document.getElementById('analyticsDashboard').innerHTML = '';
            document.getElementById('analyticsResult').innerHTML = '<div class="result info">Choose your export format below</div>';
        }
        
        async function loadAdvancedAnalytics() {
            const startDate = document.getElementById('analyticsStartDate').value;
            const endDate = document.getElementById('analyticsEndDate').value;
            const category = document.getElementById('analyticsCategory').value;
            const activity = document.getElementById('analyticsActivity').value;
            
            try {
                document.getElementById('advancedAnalyticsResult').innerHTML = '<div class="result info">Generating advanced analytics...</div>';
                
                const response = await fetch('/get_advanced_analytics', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        start_date: startDate,
                        end_date: endDate,
                        category: category,
                        activity: activity
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                const resultDiv = document.getElementById('advancedAnalyticsResult');
                
                if (result.status === 'success') {
                    const analytics = result.analytics;
                    
                    let html = `
                        <div class="analytics-grid">
                            <div class="analytics-card">
                                <div class="analytics-label">Filtered Entries</div>
                                <div class="analytics-value">${analytics.filtered_entries}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Filtered Minutes</div>
                                <div class="analytics-value">${analytics.filtered_minutes}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Total Days</div>
                                <div class="analytics-value">${analytics.productivity_metrics.total_days}</div>
                            </div>
                            <div class="analytics-card">
                                <div class="analytics-label">Avg Daily Minutes</div>
                                <div class="analytics-value">${analytics.productivity_metrics.avg_daily_minutes}</div>
                            </div>
                        </div>
                    `;
                    
                    // Add category distribution
                    if (Object.keys(analytics.category_distribution).length > 0) {
                        html += `
                            <div class="chart-container">
                                <h3>Category Distribution</h3>
                                <div class="chart-placeholder">
                                    ${Object.entries(analytics.category_distribution).map(([category, minutes]) => 
                                        `<div><strong>${category}</strong>: ${minutes} minutes</div>`
                                    ).join('')}
                                </div>
                            </div>
                        `;
                    }
                    
                    // Add daily trends
                    if (Object.keys(analytics.daily_trends).length > 0) {
                        html += `
                            <div class="chart-container">
                                <h3>Daily Trends (Last 30 Days)</h3>
                                <div class="chart-placeholder">
                                    ${Object.entries(analytics.daily_trends).map(([date, minutes]) => 
                                        `<div><strong>${date}</strong>: ${minutes} minutes</div>`
                                    ).join('')}
                                </div>
                            </div>
                        `;
                    }
                    
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = '<div class="result error">' + (result.message || 'Error loading advanced analytics') + '</div>';
                }
            } catch (error) {
                console.error('Advanced analytics error:', error);
                document.getElementById('advancedAnalyticsResult').innerHTML = '<div class="result error">Failed to load advanced analytics: ' + error.message + '</div>';
            }
        }
        
        function exportData(format) {
            window.open(`/export_data?format=${format}`, '_blank');
        }
        
        // Goals Functions
        async function loadGoals() {
            try {
                const response = await fetch('/get_goals');
                const result = await response.json();
                
                if (result.status === 'success') {
                    goals = result.goals;
                    displayGoals();
                }
            } catch (error) {
                console.error('Error loading goals:', error);
            }
        }
        
        function displayGoals() {
            const dashboard = document.getElementById('goalsDashboard');
            
            if (goals.length === 0) {
                dashboard.innerHTML = `
                    <div class="result info">
                        <p>No goals set yet. Create your first goal to start tracking your progress!</p>
                    </div>
                `;
                return;
            }
            
            let html = '<div class="goals-grid">';
            
            goals.forEach(goal => {
                const progress = goal.current_progress || 0;
                const target = goal.target || 1;
                const percentage = Math.min(100, (progress / target) * 100);
                const typeLabel = goal.type === 'category' ? 'Category' : 
                                 goal.type === 'total_minutes' ? 'Total Minutes' : 'Consistency';
                
                html += `
                    <div class="goal-card">
                        <div class="goal-header">
                            <div class="goal-title">${goal.title}</div>
                            <span class="goal-type">${typeLabel}</span>
                        </div>
                        <div class="goal-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${percentage}%"></div>
                            </div>
                            <div class="progress-text">
                                <span>${progress} / ${target}</span>
                                <span>${percentage.toFixed(1)}%</span>
                            </div>
                        </div>
                        <div class="goal-actions">
                            <button class="toggle-btn" onclick="editGoal('${goal.id}')">Edit</button>
                            <button class="toggle-btn" onclick="deleteGoal('${goal.id}')" style="background: var(--danger-color);">Delete</button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            dashboard.innerHTML = html;
        }
        
        function showGoalForm() {
            document.getElementById('goalFormSection').style.display = 'block';
            document.getElementById('goalForm').reset();
            document.getElementById('goalId').value = '';
            loadGoalCategories();
        }
        
        function hideGoalForm() {
            document.getElementById('goalFormSection').style.display = 'none';
        }
        
        function loadGoalCategories() {
            const categorySelect = document.getElementById('goalCategory');
            const goalType = document.getElementById('goalType').value;
            
            if (goalType === 'category') {
                categorySelect.style.display = 'block';
                // Populate categories from main category select
                const mainSelect = document.getElementById('categorySelect');
                categorySelect.innerHTML = '<option value="">Select Category</option>';
                for (let i = 1; i < mainSelect.options.length; i++) {
                    if (mainSelect.options[i].value !== 'new') {
                        const option = new Option(mainSelect.options[i].text, mainSelect.options[i].value);
                        categorySelect.appendChild(option);
                    }
                }
            } else {
                categorySelect.style.display = 'none';
            }
        }
        
        document.getElementById('goalType').addEventListener('change', loadGoalCategories);
        
        document.getElementById('goalForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const goalData = {
                id: document.getElementById('goalId').value,
                title: document.getElementById('goalTitle').value,
                type: document.getElementById('goalType').value,
                category: document.getElementById('goalCategory').value,
                period: document.getElementById('goalPeriod').value,
                target: parseInt(document.getElementById('goalTarget').value)
            };
            
            try {
                const response = await fetch('/save_goal', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(goalData)
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    hideGoalForm();
                    loadGoals();
                    document.getElementById('goalsResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('goalsResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('goalsResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
            }
        });
        
        async function updateAllGoalProgress() {
            try {
                const response = await fetch('/update_goal_progress', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    goals = result.goals;
                    displayGoals();
                    document.getElementById('goalsResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('goalsResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('goalsResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
            }
        }
        
        function editGoal(goalId) {
            const goal = goals.find(g => g.id === goalId);
            if (goal) {
                document.getElementById('goalId').value = goal.id;
                document.getElementById('goalTitle').value = goal.title;
                document.getElementById('goalType').value = goal.type;
                document.getElementById('goalPeriod').value = goal.period;
                document.getElementById('goalTarget').value = goal.target;
                
                if (goal.type === 'category') {
                    document.getElementById('goalCategory').value = goal.category;
                }
                
                showGoalForm();
            }
        }
        
        async function deleteGoal(goalId) {
            if (confirm('Are you sure you want to delete this goal?')) {
                try {
                    const response = await fetch('/delete_goal', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: goalId })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        loadGoals();
                        document.getElementById('goalsResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                    } else {
                        document.getElementById('goalsResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                    }
                } catch (error) {
                    document.getElementById('goalsResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
                }
            }
        }
        
        // Performance Functions
        async function loadPerformanceData() {
            try {
                document.getElementById('performanceResult').innerHTML = '<div class="result info">Loading performance data...</div>';
                
                const response = await fetch('/get_performance_data');
                const result = await response.json();
                
                if (result.status === 'success') {
                    displayPerformanceCharts(result.charts);
                    document.getElementById('performanceResult').innerHTML = '<div class="result success">Performance data loaded</div>';
                } else {
                    document.getElementById('performanceResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('performanceResult').innerHTML = '<div class="result error">Failed to load performance data: ' + error.message + '</div>';
            }
        }
        
        function displayPerformanceCharts(charts) {
            const dashboard = document.getElementById('performanceDashboard');
            
            let html = `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Tracked Days</div>
                        <div class="metric-value">${charts.daily_trends.labels.length}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Categories</div>
                        <div class="metric-value">${charts.category_distribution.labels.length}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Weekly Average</div>
                        <div class="metric-value">${Math.round(charts.weekly_performance.values.reduce((a, b) => a + b, 0) / charts.weekly_performance.values.length)}</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Daily Activity Trends (Last 30 Days)</h3>
                    <div class="chart-placeholder">
                        ${charts.daily_trends.labels.map((label, i) => 
                            `<div><strong>${label}</strong>: ${charts.daily_trends.values[i]} minutes</div>`
                        ).join('')}
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Category Distribution</h3>
                    <div class="chart-placeholder">
                        ${charts.category_distribution.labels.map((label, i) => 
                            `<div><strong>${label}</strong>: ${charts.category_distribution.values[i]} minutes</div>`
                        ).join('')}
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Weekly Performance</h3>
                    <div class="chart-placeholder">
                        ${charts.weekly_performance.labels.map((label, i) => 
                            `<div><strong>${label}</strong>: ${charts.weekly_performance.values[i]} minutes</div>`
                        ).join('')}
                    </div>
                </div>
            `;
            
            dashboard.innerHTML = html;
        }
                // To-Do List Functions
        let currentTodos = [];
        let filteredTodos = [];
        
        async function loadAllTodos() {
            try {
                const response = await fetch('/get_all_todos');
                const result = await response.json();
                
                if (result.status === 'success' && result.todos.length > 0) {
                    currentTodos = result.todos;
                    filteredTodos = currentTodos;
                    displayTodos(currentTodos);
                    updateTodoStats(currentTodos);
                    showTodoTable();
                } else {
                    showNoTodosMessage();
                    hideTodoStats();
                }
            } catch (error) {
                console.error('Error loading todos:', error);
                showNoTodosMessage();
                hideTodoStats();
            }
        }
        
        function displayTodos(todos) {
            const tableBody = document.getElementById('todoTableBody');
            
            if (todos.length === 0) {
                showNoTodosMessage();
                hideTodoStats();
                return;
            }
            
            tableBody.innerHTML = '';
            showTodoTable();
            
            todos.forEach(todo => {
                const tr = document.createElement('tr');
                const statusClass = todo.status === 'completed' ? 'success' : 'warning';
                
                tr.innerHTML = `
                    <td>${todo.date_created || 'N/A'}</td>
                    <td>${todo.activity || ''}</td>
                    <td>${todo.target_date || ''}</td>
                    <td>${todo.category || ''}</td>
                    <td><span class="result ${statusClass}" style="padding: 4px 8px; font-size: 12px;">${todo.status || 'pending'}</span></td>
                    <td style="text-align: center;">
                        <button class="action-btn edit-btn" onclick="openTodoEditModal('${todo.id}')">Edit</button>
                        <button class="delete-btn-sm" onclick="quickDeleteTodo('${todo.id}')">Delete</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
            
            updateTodoStats(todos);
        }
        
        function updateTodoStats(todos) {
            const totalTodos = todos.length;
            const pendingTodos = todos.filter(todo => todo.status === 'pending').length;
            const completedTodos = todos.filter(todo => todo.status === 'completed').length;
            
            document.getElementById('totalTodos').textContent = `${totalTodos} todos`;
            document.getElementById('pendingTodos').textContent = `${pendingTodos} pending`;
            document.getElementById('completedTodos').textContent = `${completedTodos} completed`;
            document.getElementById('todoStats').style.display = 'block';
        }
        
        function hideTodoStats() {
            document.getElementById('todoStats').style.display = 'none';
        }
        
        function showTodoSearchPrompt() {
            document.getElementById('todoSearchPrompt').style.display = 'block';
            document.getElementById('noTodosMessage').style.display = 'none';
            document.getElementById('todoTable').classList.remove('table-visible');
            document.getElementById('todoTable').classList.add('table-hidden');
            document.getElementById('todoStats').style.display = 'none';
        }
        
        function showNoTodosMessage() {
            document.getElementById('todoSearchPrompt').style.display = 'none';
            document.getElementById('noTodosMessage').style.display = 'block';
            document.getElementById('todoTable').classList.remove('table-visible');
            document.getElementById('todoTable').classList.add('table-hidden');
            document.getElementById('todoStats').style.display = 'none';
        }
        
        function showTodoTable() {
            document.getElementById('todoSearchPrompt').style.display = 'none';
            document.getElementById('noTodosMessage').style.display = 'none';
            document.getElementById('todoTable').classList.remove('table-hidden');
            document.getElementById('todoTable').classList.add('table-visible');
        }
        
        async function searchTodos() {
            const activity = document.getElementById('todoSearchActivity').value;
            const category = document.getElementById('todoSearchCategory').value;
            const status = document.getElementById('todoSearchStatus').value;
            const dateFrom = document.getElementById('todoDateFrom').value;
            const dateTo = document.getElementById('todoDateTo').value;
            
            if (currentTodos.length === 0) {
                await loadAllTodos();
            }
            
            if (!activity && !category && !status && !dateFrom && !dateTo) {
                filteredTodos = currentTodos;
                displayTodos(currentTodos);
                updateTodoStats(currentTodos);
                return;
            }
            
            try {
                const response = await fetch('/search_todos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        activity: activity,
                        category: category,
                        status: status,
                        target_date_from: dateFrom,
                        target_date_to: dateTo
                    })
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    filteredTodos = result.todos;
                    displayTodos(result.todos);
                } else {
                    document.getElementById('todoResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('todoResult').innerHTML = '<div class="result error">Search error: ' + error + '</div>';
            }
        }
        
        function clearTodoFilters() {
            document.getElementById('todoSearchActivity').value = '';
            document.getElementById('todoSearchCategory').value = '';
            document.getElementById('todoSearchStatus').value = '';
            document.getElementById('todoDateFrom').value = '';
            document.getElementById('todoDateTo').value = '';
            currentTodos = [];
            filteredTodos = [];
            showTodoSearchPrompt();
        }
        
        function showTodoForm() {
            document.getElementById('todoFormSection').style.display = 'block';
            document.getElementById('todoForm').reset();
            document.getElementById('todoId').value = '';
            // Set default target date to today
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('todoTargetDate').value = today;
        }
        
        function hideTodoForm() {
            document.getElementById('todoFormSection').style.display = 'none';
        }
        
        document.getElementById('todoForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const todoData = {
                activity: document.getElementById('todoActivity').value,
                target_date: document.getElementById('todoTargetDate').value,
                category: document.getElementById('todoCategory').value,
                status: document.getElementById('todoStatus').value
            };
            
            try {
                const response = await fetch('/add_todo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(todoData)
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    hideTodoForm();
                    loadAllTodos();
                    document.getElementById('todoResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('todoResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('todoResult').innerHTML = '<div class="result error">Network error: ' + error + '</div>';
            }
        });
        
        function openTodoEditModal(todoId) {
            const todo = currentTodos.find(t => t.id === todoId);
            
            if (!todo) {
                alert('Error: Could not find the todo to edit');
                return;
            }
            
            document.getElementById('editTodoId').value = todo.id;
            document.getElementById('editTodoActivity').value = todo.activity || '';
            document.getElementById('editTodoTargetDate').value = todo.target_date || '';
            document.getElementById('editTodoCategory').value = todo.category || '';
            document.getElementById('editTodoStatus').value = todo.status || 'pending';
            document.getElementById('todoEditModal').style.display = 'flex';
        }
        
        function closeTodoEditModal() {
            document.getElementById('todoEditModal').style.display = 'none';
        }
        
        async function quickDeleteTodo(todoId) {
            if (confirm('Are you sure you want to delete this todo?')) {
                try {
                    const response = await fetch('/delete_todo', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: todoId })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        loadAllTodos();
                        document.getElementById('todoResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                    } else {
                        document.getElementById('todoResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                    }
                } catch (error) {
                    document.getElementById('todoResult').innerHTML = '<div class="result error">Error deleting todo: ' + error + '</div>';
                }
            }
        }
        
        async function deleteTodo() {
            const todoId = document.getElementById('editTodoId').value;
            if (confirm('Are you sure you want to delete this todo?')) {
                try {
                    const response = await fetch('/delete_todo', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: todoId })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        closeTodoEditModal();
                        loadAllTodos();
                        document.getElementById('todoResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                    } else {
                        document.getElementById('todoResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                    }
                } catch (error) {
                    document.getElementById('todoResult').innerHTML = '<div class="result error">Error deleting todo: ' + error + '</div>';
                }
            }
        }
        
        document.getElementById('todoEditForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const todoData = {
                id: document.getElementById('editTodoId').value,
                activity: document.getElementById('editTodoActivity').value,
                target_date: document.getElementById('editTodoTargetDate').value,
                category: document.getElementById('editTodoCategory').value,
                status: document.getElementById('editTodoStatus').value
            };
            
            try {
                const response = await fetch('/update_todo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(todoData)
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    closeTodoEditModal();
                    loadAllTodos();
                    document.getElementById('todoResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('todoResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('todoResult').innerHTML = '<div class="result error">Error updating todo: ' + error + '</div>';
            }
        });
        
        // Initialize todo section
        document.addEventListener('DOMContentLoaded', function() {
            showTodoSearchPrompt();
        });
        // Update these JavaScript functions:

        async function sendCustomNotification() {
            const title = document.getElementById('customNotificationTitle').value || 'Life Tracker';
            const message = document.getElementById('customNotificationMessage').value;
            
            if (!message.trim()) {
                alert('Please enter a notification message');
                return;
            }
            
            try {
                document.getElementById('notificationResult').innerHTML = '<div class="result info">Sending notification...</div>';
                
                const response = await fetch('/send_custom_notification', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: title,
                        message: message
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                if (result.status === 'success') {
                    document.getElementById('notificationResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                    document.getElementById('customNotificationMessage').value = '';
                } else {
                    document.getElementById('notificationResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                console.error('Custom notification error:', error);
                document.getElementById('notificationResult').innerHTML = '<div class="result error">Network error: ' + error.message + '. Check if server is running.</div>';
            }
        }

        async function testNotification() {
            try {
                document.getElementById('notificationResult').innerHTML = '<div class="result info">Testing notification...</div>';
                
                const response = await fetch('/test_notification', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'test',
                        title: 'Test Notification',
                        message: 'This is a test notification from Life Tracker'
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                if (result.status === 'success') {
                    document.getElementById('notificationResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('notificationResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                console.error('Test notification error:', error);
                document.getElementById('notificationResult').innerHTML = '<div class="result error">Network error: ' + error.message + '. Check if server is running.</div>';
            }
        }

        async function saveNotificationSettings() {
            const settings = {
                daily_report_enabled: document.getElementById('dailyReportEnabled').checked,
                daily_report_time: document.getElementById('dailyReportTime').value,
                todo_reminder_enabled: document.getElementById('todoReminderEnabled').checked,
                todo_reminder_time: document.getElementById('todoReminderTime').value,
                goal_reminder_enabled: document.getElementById('goalReminderEnabled').checked,
                goal_reminder_time: document.getElementById('goalReminderTime').value,
                specific_date_enabled: document.getElementById('specificDateEnabled').checked,
                specific_date: document.getElementById('specificDate').value,
                specific_date_time: document.getElementById('specificDateTime').value,
                specific_date_title: document.getElementById('specificDateTitle').value,
                specific_date_message: document.getElementById('specificDateMessage').value,
                consistency_reminder_enabled: document.getElementById('consistencyReminderEnabled').checked,
                consistency_reminder_time: document.getElementById('consistencyReminderTime').value
            };
            
            try {
                document.getElementById('notificationResult').innerHTML = '<div class="result info">Saving settings...</div>';
                
                const response = await fetch('/save_notification_settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(settings)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                if (result.status === 'success') {
                    document.getElementById('notificationResult').innerHTML = '<div class="result success">' + result.message + '</div>';
                } else {
                    document.getElementById('notificationResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                console.error('Save settings error:', error);
                document.getElementById('notificationResult').innerHTML = '<div class="result error">Network error: ' + error.message + '. Check if server is running.</div>';
            }
        }
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            setToday();
            setCurrentYear();
            showSearchPrompt();
            loadGoals();
            loadPerformanceData();
            
            // Load notification settings automatically when page loads
            loadNotificationSettings();
            
            // Initialize todo section
            showTodoSearchPrompt();
            
            // Collapse all sections by default
            setTimeout(() => {
                collapseAllSections();
            }, 100);
        });
        async function loadNotificationSettings() {
            try {
                document.getElementById('notificationResult').innerHTML = '<div class="result info">Loading settings...</div>';
                
                const response = await fetch('/get_notification_settings');
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                if (result.status === 'success') {
                    const settings = result.settings;
                    
                    console.log('Loaded settings:', settings); // Debug log
                    
                    // Daily Report Settings
                    document.getElementById('dailyReportEnabled').checked = settings.daily_report_enabled || false;
                    document.getElementById('dailyReportTime').value = settings.daily_report_time || '09:00';
                    
                    // Todo Reminder Settings
                    document.getElementById('todoReminderEnabled').checked = settings.todo_reminder_enabled || false;
                    document.getElementById('todoReminderTime').value = settings.todo_reminder_time || '18:00';
                    
                    // Goal Reminder Settings
                    document.getElementById('goalReminderEnabled').checked = settings.goal_reminder_enabled || false;
                    document.getElementById('goalReminderTime').value = settings.goal_reminder_time || '20:00';
                    
                    // Specific Date Settings
                    document.getElementById('specificDateEnabled').checked = settings.specific_date_enabled || false;
                    document.getElementById('specificDate').value = settings.specific_date || '';
                    document.getElementById('specificDateTime').value = settings.specific_date_time || '10:00';
                    document.getElementById('specificDateTitle').value = settings.specific_date_title || '';
                    document.getElementById('specificDateMessage').value = settings.specific_date_message || '';
                    
                    // Consistency Reminder Settings
                    document.getElementById('consistencyReminderEnabled').checked = settings.consistency_reminder_enabled || false;
                    document.getElementById('consistencyReminderTime').value = settings.consistency_reminder_time || '21:00';
                    
                    document.getElementById('notificationResult').innerHTML = '<div class="result success">Notification settings loaded successfully</div>';
                    
                    // Debug: Log what was actually set
                    console.log('Form values after loading:');
                    console.log('Daily enabled:', document.getElementById('dailyReportEnabled').checked);
                    console.log('Todo enabled:', document.getElementById('todoReminderEnabled').checked);
                } else {
                    document.getElementById('notificationResult').innerHTML = '<div class="result error">' + result.message + '</div>';
                }
            } catch (error) {
                console.error('Load settings error:', error);
                document.getElementById('notificationResult').innerHTML = '<div class="result error">Failed to load settings: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>
"""

# Create necessary directories and files
os.makedirs("reports", exist_ok=True)
os.makedirs("backups", exist_ok=True)

# Create goals file if it doesn't exist
if not os.path.exists("goals.json"):
    with open("goals.json", "w") as f:
        json.dump([], f)

# Create todo file if it doesn't exist
if not os.path.exists("todo.json"):
    with open("todo.json", "w") as f:
        json.dump([], f)

# Create notifications file if it doesn't exist
if not os.path.exists("notifications.json"):
    with open("notifications.json", "w") as f:
        json.dump({}, f)

with open("index.html", "w") as f:
    f.write(html_content)

def signal_handler(sig, frame):
    print("\nServer stopped successfully")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Starting Life Tracker Web GUI...")
print("Open your browser and go to: http://localhost:8000")
print("Press Ctrl+C to stop the server")
print("All functionality restored: Add Data, Search, Reports, Analytics")
print("Improved: Global expand/collapse controls at top, no arrow icons")

try:
    httpd = HTTPServer(('0.0.0.0', 8000), LifeTrackerHandler)
    httpd.serve_forever()
except KeyboardInterrupt:
    print("Server stopped")

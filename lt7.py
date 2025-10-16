from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
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
from typing import Dict, List, Any

class LifeTrackerHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
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
        elif self.path == '/get_notifications':
            self.get_notifications()
            return
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def get_categories(self):
        """Get all categories from the data file"""
        categories = []
        try:
            if os.path.exists("lifetracker.csv"):
                df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
                if 'category' in df.columns:
                    categories = df['category'].unique().tolist()
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
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/add_entry':
            self.add_entry(post_data)
        elif self.path == '/run_report':
            self.run_report(post_data)
        elif self.path == '/update_entry':
            self.update_entry(post_data)
        elif self.path == '/delete_entry':
            self.delete_entry(post_data)
        elif self.path == '/create_backup':
            self.create_backup()
        elif self.path == '/validate_data':
            self.validate_data()
        elif self.path == '/get_advanced_analytics':
            self.get_advanced_analytics(post_data)
        elif self.path == '/save_goal':
            self.save_goal(post_data)
        elif self.path == '/delete_goal':
            self.delete_goal(post_data)
        elif self.path == '/update_goal_progress':
            self.update_goal_progress()
        elif self.path == '/save_notification':
            self.save_notification(post_data)
        elif self.path == '/delete_notification':
            self.delete_notification(post_data)
        elif self.path == '/test_notification':
            self.test_notification()
        elif self.path == '/send_instant_notification':
            self.send_instant_notification(post_data)
        else:
            self.send_error(404, "Endpoint not found")
    
    def parse_form_data(self, post_data):
        """Parse form data from POST request"""
        try:
            data = json.loads(post_data.decode())
            return data
        except:
            # Fallback for form data
            data = {}
            parts = post_data.decode().split('&')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=')
                    data[key] = value
            return data
    
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
    
    def add_entry(self, post_data):
        """Enhanced add_entry with validation and backup"""
        try:
            data = self.parse_form_data(post_data)
            
            date = data.get('date', '')
            activity = data.get('activity', '')
            minutes = data.get('minutes', '')
            category = data.get('category', '')
            
            # Validate data before processing
            validation_errors = self.validate_entry_data(date, activity, minutes, category)
            if validation_errors:
                self.send_error_response("Validation errors: " + "; ".join(validation_errors))
                return
            
            # Create backup before making changes
            backup_result = self.create_backup_silent()
            
            # Create data file if it doesn't exist
            if not os.path.exists("lifetracker.csv"):
                with open("lifetracker.csv", "w") as f:
                    f.write("date,activity,minutes,category\n")
            
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
    
    def run_report(self, post_data):
        """Enhanced report generation with validation"""
        try:
            data = self.parse_form_data(post_data)
            
            report_type = data.get('report_type', '')
            month = data.get('month', '')
            year = data.get('year', '')
            
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
                    # Create reports directory if it doesn't exist
                    os.makedirs("reports", exist_ok=True)
                    
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
                            # Create a placeholder image if the report script didn't generate one
                            self.create_placeholder_image(image_path, report_type, month, year)
                            output = image_path
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
    
    def create_placeholder_image(self, image_path, report_type, month, year):
        """Create a placeholder image when report scripts fail"""
        try:
            # Create a simple text file as placeholder
            with open(image_path.replace('.png', '.txt'), 'w') as f:
                f.write(f"{report_type.title()} Report\n")
                f.write(f"Month: {month}, Year: {year}\n")
                f.write("Report visualization would appear here\n")
                f.write("Ensure report generation scripts are properly configured")
            print(f"Created placeholder file: {image_path.replace('.png', '.txt')}")
        except Exception as e:
            print(f"Could not create placeholder file: {e}")
    
    def update_entry(self, post_data):
        """Enhanced update_entry with validation and backup"""
        data = self.parse_form_data(post_data)
        
        try:
            index = int(data['index'])
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
    
    def delete_entry(self, post_data):
        """Enhanced delete_entry with backup"""
        data = self.parse_form_data(post_data)
        
        try:
            index = int(data['index'])
            
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
    
    def get_advanced_analytics(self, post_data):
        """Get advanced analytics with filters"""
        try:
            data = self.parse_form_data(post_data)
            
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
    
    # ============================
    # GOALS SYSTEM
    # ============================
    
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
    
    def save_goal(self, post_data):
        """Save a new goal or update existing goal"""
        try:
            data = self.parse_form_data(post_data)
            
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
    
    def delete_goal(self, post_data):
        """Delete a goal"""
        try:
            data = self.parse_form_data(post_data)
            
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
            if not os.path.exists("goals.json"):
                self.send_success_response("No goals found")
                return
            
            # Load goals
            with open("goals.json", "r") as f:
                content = f.read().strip()
                if not content:
                    self.send_success_response("No goals found")
                    return
                goals = json.loads(content)
            
            # Load tracking data
            if not os.path.exists("lifetracker.csv"):
                self.send_success_response("No tracking data found")
                return
            
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            
            # Convert minutes to numeric
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            
            # Update each goal's progress
            for goal in goals:
                goal_type = goal.get('type', '')
                target = goal.get('target', 0)
                category = goal.get('category', '')
                activity = goal.get('activity', '')
                period = goal.get('period', 'weekly')
                
                # Calculate progress based on goal type and period
                progress = 0
                
                if goal_type == 'total_minutes':
                    if period == 'weekly':
                        # Last 7 days
                        cutoff_date = datetime.now() - timedelta(days=7)
                        try:
                            df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                            recent_data = df[df['date_obj'] >= cutoff_date]
                            progress = recent_data['minutes'].sum()
                        except:
                            progress = 0
                    elif period == 'monthly':
                        # Current month
                        current_month = datetime.now().month
                        current_year = datetime.now().year
                        try:
                            df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                            month_data = df[
                                (df['date_obj'].dt.month == current_month) & 
                                (df['date_obj'].dt.year == current_year)
                            ]
                            progress = month_data['minutes'].sum()
                        except:
                            progress = 0
                    else:  # daily
                        # Today
                        today = datetime.now().strftime('%d-%m-%Y')
                        try:
                            today_data = df[df['date'] == today]
                            progress = today_data['minutes'].sum()
                        except:
                            progress = 0
                
                elif goal_type == 'category_minutes':
                    category_data = df[df['category'] == category]
                    if period == 'weekly':
                        cutoff_date = datetime.now() - timedelta(days=7)
                        try:
                            category_data['date_obj'] = pd.to_datetime(category_data['date'], format='%d-%m-%Y', errors='coerce')
                            recent_data = category_data[category_data['date_obj'] >= cutoff_date]
                            progress = recent_data['minutes'].sum()
                        except:
                            progress = 0
                    elif period == 'monthly':
                        current_month = datetime.now().month
                        current_year = datetime.now().year
                        try:
                            category_data['date_obj'] = pd.to_datetime(category_data['date'], format='%d-%m-%Y', errors='coerce')
                            month_data = category_data[
                                (category_data['date_obj'].dt.month == current_month) & 
                                (category_data['date_obj'].dt.year == current_year)
                            ]
                            progress = month_data['minutes'].sum()
                        except:
                            progress = 0
                    else:  # daily
                        today = datetime.now().strftime('%d-%m-%Y')
                        try:
                            today_data = category_data[category_data['date'] == today]
                            progress = today_data['minutes'].sum()
                        except:
                            progress = 0
                
                elif goal_type == 'activity_completion':
                    activity_data = df[df['activity'] == activity]
                    if period == 'weekly':
                        cutoff_date = datetime.now() - timedelta(days=7)
                        try:
                            activity_data['date_obj'] = pd.to_datetime(activity_data['date'], format='%d-%m-%Y', errors='coerce')
                            recent_data = activity_data[activity_data['date_obj'] >= cutoff_date]
                            progress = len(recent_data)
                        except:
                            progress = 0
                    elif period == 'monthly':
                        current_month = datetime.now().month
                        current_year = datetime.now().year
                        try:
                            activity_data['date_obj'] = pd.to_datetime(activity_data['date'], format='%d-%m-%Y', errors='coerce')
                            month_data = activity_data[
                                (activity_data['date_obj'].dt.month == current_month) & 
                                (activity_data['date_obj'].dt.year == current_year)
                            ]
                            progress = len(month_data)
                        except:
                            progress = 0
                    else:  # daily
                        today = datetime.now().strftime('%d-%m-%Y')
                        try:
                            today_data = activity_data[activity_data['date'] == today]
                            progress = len(today_data)
                        except:
                            progress = 0
                
                # Update goal progress
                goal['current_progress'] = progress
                goal['progress_percentage'] = min(round((progress / target) * 100, 2) if target > 0 else 0, 100)
            
            # Save updated goals
            with open("goals.json", "w") as f:
                json.dump(goals, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Goal progress updated successfully",
                "goals": goals
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
    
    def get_performance_data(self):
        """Get performance metrics and insights"""
        try:
            if not os.path.exists("lifetracker.csv"):
                self.send_error_response("No data file found")
                return
            
            df = pd.read_csv("lifetracker.csv", header=None, names=['date', 'activity', 'minutes', 'category'])
            df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce')
            
            # Convert dates
            try:
                df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            except:
                pass
            
            # Performance metrics
            total_days = df['date'].nunique() if 'date' in df.columns else 0
            total_activities = len(df)
            total_minutes = df['minutes'].sum()
            avg_daily_minutes = total_minutes / total_days if total_days > 0 else 0
            
            # Streaks (simplified)
            current_streak = 0
            try:
                unique_dates = sorted(df['date_obj'].dropna().unique())
                if len(unique_dates) > 0:
                    today = pd.Timestamp(datetime.now().date())
                    last_date = unique_dates[-1]
                    if (today - last_date).days <= 1:
                        current_streak = 1
                        for i in range(len(unique_dates)-2, -1, -1):
                            if (unique_dates[i+1] - unique_dates[i]).days == 1:
                                current_streak += 1
                            else:
                                break
            except:
                pass
            
            # Category insights
            category_insights = {}
            try:
                category_stats = df.groupby('category').agg({
                    'minutes': ['sum', 'mean', 'count']
                }).round(2)
                category_insights = category_stats.to_dict()
            except:
                pass
            
            performance_data = {
                "status": "success",
                "performance": {
                    "total_days": int(total_days),
                    "total_activities": int(total_activities),
                    "total_minutes": int(total_minutes),
                    "avg_daily_minutes": round(float(avg_daily_minutes), 2),
                    "current_streak": int(current_streak),
                    "category_insights": category_insights
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
    
    # ============================
    # NOTIFICATION SYSTEM
    # ============================
    
    def get_notifications(self):
        """Get all notifications"""
        try:
            notifications = []
            if os.path.exists("notifications.json"):
                with open("notifications.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        notifications = json.loads(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "notifications": notifications
            }).encode())
            
        except Exception as e:
            print(f"Error loading notifications: {e}")
            # Return empty notifications list if there's an error
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "notifications": []
            }).encode())
    
    def save_notification(self, post_data):
        """Save a new notification or update existing notification"""
        try:
            data = self.parse_form_data(post_data)
            
            notifications = []
            if os.path.exists("notifications.json"):
                try:
                    with open("notifications.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            notifications = json.loads(content)
                except json.JSONDecodeError:
                    notifications = []
            
            # Add or update notification
            notification_id = data.get('id')
            if notification_id:
                # Update existing notification
                for i, notification in enumerate(notifications):
                    if notification.get('id') == notification_id:
                        notifications[i] = data
                        break
            else:
                # Add new notification
                data['id'] = str(int(datetime.now().timestamp() * 1000))
                data['created_at'] = datetime.now().isoformat()
                data['enabled'] = data.get('enabled', True)
                notifications.append(data)
            
            # Save notifications
            with open("notifications.json", "w") as f:
                json.dump(notifications, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Notification saved successfully",
                "notification": data
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error saving notification: {str(e)}"
            }).encode())
    
    def delete_notification(self, post_data):
        """Delete a notification"""
        try:
            data = self.parse_form_data(post_data)
            
            notification_id = data.get('id')
            
            notifications = []
            if os.path.exists("notifications.json"):
                try:
                    with open("notifications.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            notifications = json.loads(content)
                except json.JSONDecodeError:
                    notifications = []
            
            # Remove notification
            notifications = [notification for notification in notifications if notification.get('id') != notification_id]
            
            # Save updated notifications
            with open("notifications.json", "w") as f:
                json.dump(notifications, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Notification deleted successfully"
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error deleting notification: {str(e)}"
            }).encode())
    
    def test_notification(self):
        """Test notification system"""
        try:
            # Create a test notification
            test_notification = {
                "id": "test_" + str(int(datetime.now().timestamp() * 1000)),
                "title": "Test Notification",
                "message": "This is a test notification to verify the system is working.",
                "type": "info",
                "timestamp": datetime.now().isoformat(),
                "enabled": True
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Test notification generated successfully",
                "notification": test_notification
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error testing notification: {str(e)}"
            }).encode())
    
    def send_instant_notification(self, post_data):
        """Send an instant notification"""
        try:
            data = self.parse_form_data(post_data)
            
            title = data.get('title', 'Instant Notification')
            message = data.get('message', '')
            notification_type = data.get('type', 'info')
            
            # Create the instant notification
            instant_notification = {
                "id": "instant_" + str(int(datetime.now().timestamp() * 1000)),
                "title": title,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
                "is_instant": True
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Instant notification sent successfully",
                "notification": instant_notification
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Error sending instant notification: {str(e)}"
            }).encode())
    
    def send_success_response(self, message):
        """Helper method to send success response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "success",
            "message": message
        }).encode())
    
    def send_error_response(self, message):
        """Helper method to send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "error",
            "message": message
        }).encode())

def signal_handler(sig, frame):
    print("\nShutting down server...")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create necessary directories
    os.makedirs("backups", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Initialize data files if they don't exist
    if not os.path.exists("lifetracker.csv"):
        with open("lifetracker.csv", "w") as f:
            f.write("date,activity,minutes,category\n")
    
    if not os.path.exists("goals.json"):
        with open("goals.json", "w") as f:
            f.write("[]")
    
    if not os.path.exists("notifications.json"):
        with open("notifications.json", "w") as f:
            f.write("[]")
    
    port = 8000
    server = HTTPServer(('localhost', port), LifeTrackerHandler)
    print(f"Server running on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

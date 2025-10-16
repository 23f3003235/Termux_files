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
        return SimpleHTTPRequestHandler.do_GET(self)
    
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
            padding: 6px 12px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
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
                    <button class="toggle-btn" onclick="event.stopPropagation(); showGoalForm()">New Goal</button>
                    <button class="toggle-btn" onclick="event.stopPropagation(); updateAllGoalProgress()">Update Progress</button>
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
                    <h2>Manage Data</h2>
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
                    • Automatic backups before data modifications<br>
                    • Date validation (DD-MM-YYYY format)<br>
                    • Activity and category length limits<br>
                    • Minutes validation (1-1440)<br>
                    • Data integrity checking<br>
                    • Automatic cleanup of old backups (keeps last 10)
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

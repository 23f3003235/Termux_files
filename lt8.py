from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import cgi
import os
import pandas as pd
from datetime import datetime
import signal
import sys
import time
import csv

class LifeTrackerHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/get_categories':
            categories = self.get_categories()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(categories).encode())
            return
        elif self.path == '/get_all_data':
            self.get_all_data()
            return
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def get_categories(self):
        categories = []
        try:
            if os.path.exists("lifetracker.csv"):
                df = pd.read_csv("lifetracker.csv", header=None)
                if len(df.columns) >= 4:
                    categories = df[3].unique().tolist()
        except:
            pass
        return categories
    
    def get_all_data(self):
        try:
            if os.path.exists("lifetracker.csv"):
                with open("lifetracker.csv", "r") as f:
                    reader = csv.reader(f)
                    data = list(reader)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "data": data
                }).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "CSV file not found"
                }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode())
    
    def do_POST(self):
        if self.path == '/add_entry':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            date = form.getvalue('date')
            activity = form.getvalue('activity')
            minutes = form.getvalue('minutes')
            category = form.getvalue('category')
            
            with open("lifetracker.csv", "a") as f:
                f.write(f"{date},{activity},{minutes},{category}\n")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            
        elif self.path == '/run_report':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            report_type = form.getvalue('report_type')
            month = form.getvalue('month')
            year = form.getvalue('year')
            
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
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": status, 
                "output": output,
                "summary": clean_summary
            }).encode())
        
        elif self.path == '/update_entry':
            self.update_entry()
        elif self.path == '/delete_entry':
            self.delete_entry()
    
    def update_entry(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        try:
            index = data['index']
            new_date = data['date']
            new_activity = data['activity']
            new_minutes = data['minutes']
            new_category = data['category']
            
            with open("lifetracker.csv", "r") as f:
                lines = f.readlines()
            
            if 0 <= index < len(lines):
                lines[index] = f"{new_date},{new_activity},{new_minutes},{new_category}\n"
                
                with open("lifetracker.csv", "w") as f:
                    f.writelines(lines)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error", 
                    "message": "Invalid index"
                }).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error", 
                "message": str(e)
            }).encode())
    
    def delete_entry(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        try:
            index = data['index']
            
            with open("lifetracker.csv", "r") as f:
                lines = f.readlines()
            
            if 0 <= index < len(lines):
                # Remove the line at the specified index
                del lines[index]
                
                with open("lifetracker.csv", "w") as f:
                    f.writelines(lines)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error", 
                    "message": "Invalid index"
                }).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error", 
                "message": str(e)
            }).encode())

# HTML UI with all features
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Life Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --primary-color: #4CAF50;
            --primary-dark: #45a049;
            --secondary-color: #2196F3;
            --danger-color: #dc3545;
            --danger-dark: #c82333;
            --warning-color: #ffc107;
            --warning-dark: #e0a800;
            --gray-color: #6c757d;
            --gray-dark: #5a6268;
            --light-bg: #f8f9fa;
            --border-color: #dee2e6;
            --shadow: 0 2px 10px rgba(0,0,0,0.1);
            --radius: 8px;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 25px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
        }
        .section { 
            margin: 25px 0; 
            padding: 20px; 
            border: 1px solid var(--border-color); 
            border-radius: var(--radius);
            background: white;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .section:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }
        input, select, button { 
            padding: 12px; 
            margin: 8px 0; 
            width: 100%; 
            border: 2px solid #e9ecef;
            border-radius: var(--radius);
            font-size: 16px;
            transition: all 0.3s ease;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--secondary-color);
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }
        button { 
            background: var(--primary-color); 
            color: white; 
            border: none; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
        }
        button:hover { 
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .result { 
            padding: 12px; 
            margin: 12px 0; 
            border-radius: var(--radius); 
            font-size: 14px;
            border-left: 4px solid transparent;
        }
        .success { 
            background: #d4edda; 
            color: #155724; 
            border-left-color: var(--primary-color);
        }
        .error { 
            background: #f8d7da; 
            color: #721c24; 
            border-left-color: var(--danger-color);
        }
        .summary { 
            background: #e8f4fd; 
            color: #0c5460; 
            border-left: 4px solid var(--secondary-color);
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            padding: 15px;
        }
        h1 { 
            color: #2c3e50; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.2em;
            font-weight: 300;
        }
        h2 { 
            color: #34495e; 
            border-bottom: 3px solid var(--primary-color); 
            padding-bottom: 8px; 
            margin-bottom: 15px;
            font-weight: 400;
        }
        .new-category { display: none; margin-top: 10px; }
        .today-btn { 
            background: var(--secondary-color); 
            padding: 10px 16px; 
            margin: 8px 0; 
            font-size: 14px; 
            width: auto; 
        }
        .today-btn:hover {
            background: #1976d2;
        }
        .preview-btn {
            background: var(--secondary-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 16px;
        }
        .summary-btn {
            background: var(--gray-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 16px;
        }
        .summary-btn:hover { background: var(--gray-dark); }
        .minimize-btn {
            background: var(--danger-color);
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 16px;
        }
        .minimize-btn:hover { background: var(--danger-dark); }
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
            justify-content: center;
        }
        .summary-section {
            margin-top: 15px;
            display: none;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .data-table th, .data-table td {
            border: 1px solid #e0e0e0;
            padding: 10px 8px;
            text-align: left;
        }
        .data-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }
        .data-table tr:nth-child(even) {
            background: #fafafa;
        }
        .data-table tr:hover {
            background: #f0f8ff;
            transform: scale(1.01);
            transition: all 0.2s ease;
        }
        .action-btn {
            padding: 6px 12px;
            margin: 0 3px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .edit-btn {
            background: var(--warning-color);
            color: #000;
        }
        .edit-btn:hover {
            background: var(--warning-dark);
            transform: translateY(-1px);
        }
        .delete-btn-sm {
            background: var(--danger-color);
            color: white;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            margin-left: 5px;
        }
        .delete-btn-sm:hover {
            background: var(--danger-dark);
            transform: translateY(-1px);
        }
        .stats-card {
            background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
            padding: 15px;
            border-radius: var(--radius);
            margin-bottom: 15px;
            border-left: 4px solid var(--secondary-color);
            font-size: 14px;
            text-align: center;
        }
        .filter-section {
            background: var(--light-bg);
            padding: 20px;
            border-radius: var(--radius);
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }
        
        /* Centered layout for ALL form elements */
        .centered-form {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            width: 100%;
        }
        
        .centered-controls {
            display: flex;
            gap: 12px;
            justify-content: center;
            align-items: end;
            flex-wrap: wrap;
            width: 100%;
            max-width: 600px;
        }
        
        .centered-controls .filter-group {
            flex: 1;
            min-width: 150px;
            max-width: 280px;
            text-align: center;
        }
        
        .centered-controls button {
            width: auto;
            min-width: 120px;
            flex-shrink: 0;
        }
        
        .filter-label {
            font-size: 13px;
            color: #666;
            margin-bottom: 6px;
            display: block;
            font-weight: 500;
        }
        
        .date-filter-buttons {
            display: flex;
            gap: 12px;
            margin-top: 15px;
            justify-content: center;
            width: 100%;
            max-width: 600px;
        }
        
        .date-filter-buttons button {
            flex: 1;
            max-width: 200px;
        }
        
        /* Centered date input in Add Entry section */
        .date-input-group {
            display: flex;
            gap: 10px;
            align-items: center;
            justify-content: center;
            width: 100%;
            max-width: 600px;
        }
        
        .date-input-group input {
            flex: 1;
            max-width: 400px;
        }
        
        /* Initial state for table */
        .table-hidden {
            display: none;
        }
        
        .table-visible {
            display: table;
        }
        
        /* No data message styling */
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
        
        /* Search prompt message */
        #searchPrompt {
            text-align: center;
            padding: 40px 20px;
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
        
        /* Mobile responsive styles */
        @media (max-width: 768px) {
            body {
                padding: 10px;
                background: #667eea;
            }
            .container {
                padding: 15px;
                margin: 10px 0;
            }
            .section {
                margin: 20px 0;
                padding: 15px;
            }
            h1 {
                font-size: 1.8em;
            }
            h2 {
                font-size: 1.3em;
            }
            .centered-controls {
                flex-direction: column;
                gap: 8px;
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
                gap: 8px;
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
                padding: 8px 6px;
            }
            input, select, button {
                padding: 14px;
                font-size: 16px;
            }
            .stats-card {
                padding: 12px;
                font-size: 13px;
            }
            #noDataMessage, #searchPrompt {
                padding: 40px 15px;
            }
            #noDataMessage div:first-child, #searchPrompt div:first-child {
                font-size: 36px;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 10px;
            }
            .section {
                padding: 12px;
            }
            h1 {
                font-size: 1.6em;
            }
            .data-table {
                font-size: 11px;
            }
            .action-btn, .delete-btn-sm {
                padding: 4px 8px;
                font-size: 10px;
                margin: 2px;
            }
            #noDataMessage, #searchPrompt {
                padding: 30px 10px;
            }
            #noDataMessage div:first-child, #searchPrompt div:first-child {
                font-size: 28px;
            }
        }
        
        /* Loading animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Life Tracker</h1>
        
        <div class="section">
            <h2>Add New Entry</h2>
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
        
        <div class="section">
            <h2>Generate Reports</h2>
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
                <button onclick="generateReport()" style="max-width: 600px;">Generate Report</button>
            </form>
            
            <div id="reportResult"></div>
            
            <!-- Summary Section -->
            <div id="summarySection" class="summary-section">
                <h3>Report Summary</h3>
                <div id="summaryContent" class="result summary"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>Manage Data</h2>
            
            <div class="filter-section">
                <!-- Search Section - Centered -->
                <div class="centered-form">
                    <div class="centered-controls">
                        <div class="filter-group">
                            <span class="filter-label">Search Activities & Categories</span>
                            <input type="text" id="searchInput" placeholder="Enter activity or category name">
                        </div>
                        <button onclick="searchData()">Search</button>
                        <button onclick="loadAllData()" style="background: var(--gray-color);">Show All</button>
                    </div>
                </div>
                
                <!-- Date Range Filter - Centered -->
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
                    
                    <!-- Date Filter Buttons - Centered -->
                    <div class="date-filter-buttons">
                        <button onclick="filterByDateRange()">Filter by Date Range</button>
                        <button onclick="clearDateFilters()" style="background: var(--danger-color);">Clear Filters</button>
                    </div>
                </div>
            </div>
            
            <!-- Stats Summary - Only shown when data is displayed -->
            <div id="statsSummary" class="stats-card" style="display: none;">
                <strong>Summary:</strong> 
                <span id="totalEntries">0 entries</span> | 
                <span id="totalMinutes">0 minutes</span> | 
                <span id="dateRange">All dates</span>
            </div>
            
            <div id="tableContainer" style="overflow-x: auto; max-height: 500px; overflow-y: auto;">
                <!-- Search Prompt (shown by default) -->
                <div id="searchPrompt">
                    <div>🔍</div>
                    <div>Search or filter to view data</div>
                    <div>Use the search box or date filters above to display entries</div>
                </div>
                
                <!-- No Data Message (shown when no results found) -->
                <div id="noDataMessage" style="display: none;">
                    <div>📭</div>
                    <div>No matching entries found</div>
                    <div>Try different search terms or date range</div>
                </div>
                
                <!-- Data Table (hidden by default) -->
                <table id="dataTable" class="data-table table-hidden">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Activity</th>
                            <th>Minutes</th>
                            <th>Category</th>
                            <th style="text-align: center; width: 120px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                    </tbody>
                </table>
            </div>
            
            <!-- Edit Modal -->
            <div id="editModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center;">
                <div style="background: white; padding: 25px; border-radius: var(--radius); width: 95%; max-width: 500px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                    <h3 style="margin-bottom: 20px; color: #2c3e50; text-align: center;">Edit Entry</h3>
                    <form id="editForm" class="centered-form">
                        <input type="hidden" id="editIndex">
                        <input type="date" id="editDate" required style="max-width: 400px;">
                        <input type="text" id="editActivity" placeholder="Activity" required style="max-width: 400px;">
                        <input type="number" id="editMinutes" placeholder="Minutes" required style="max-width: 400px;">
                        <input type="text" id="editCategory" placeholder="Category" required style="max-width: 400px;">
                        <div style="display: flex; gap: 12px; margin-top: 20px; width: 100%; max-width: 400px;">
                            <button type="submit" style="flex: 1; background: var(--primary-color); padding: 12px;">Save Changes</button>
                            <button type="button" onclick="closeEditModal()" style="flex: 1; background: var(--gray-color); padding: 12px;">Cancel</button>
                            <button type="button" onclick="deleteEntry()" style="flex: 1; background: var(--danger-color); padding: 12px;">Delete Entry</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentData = [];
        let filteredData = [];
        let currentDisplayedData = [];
        let hasSearched = false;
        
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            setToday();
            setCurrentYear();
            // Don't load data automatically - wait for user action
            showSearchPrompt();
        });
        
        function setToday() {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            document.getElementById('dateInput').value = formattedDate;
        }
        
        function setCurrentYear() {
            const currentYear = new Date().getFullYear();
            document.getElementById('year').value = currentYear;
            // Update max year to current year + 10 for future flexibility
            document.getElementById('year').max = currentYear + 10;
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
            const formattedDate = formatDateForCSV(dateInput.value);
            const formData = new FormData();
            formData.append('date', formattedDate);
            formData.append('activity', document.querySelector('input[name="activity"]').value);
            formData.append('minutes', document.querySelector('input[name="minutes"]').value);
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
                    resultDiv.innerHTML = '<div class="result success">Entry added successfully!</div>';
                    document.querySelector('input[name="activity"]').value = '';
                    document.querySelector('input[name="minutes"]').value = '';
                    document.getElementById('newCategoryDiv').style.display = 'none';
                    categorySelect.value = '';
                    loadCategories();
                    // Clear current data so next search loads fresh data
                    currentData = [];
                    filteredData = [];
                    showSearchPrompt();
                } else {
                    resultDiv.innerHTML = '<div class="result error">Error adding entry</div>';
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
            
            const formData = new FormData();
            formData.append('report_type', reportType);
            formData.append('month', month);
            formData.append('year', year);
            
            const button = document.querySelector('button[onclick="generateReport()"]');
            const originalText = button.textContent;
            button.textContent = 'Generating...';
            button.disabled = true;
            
            // Hide previous summary
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
                    
                    // Show summary button if summary exists
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
                
                // Format date from DD-MM-YYYY to YYYY-MM-DD for display
                const dateParts = row[0].split('-');
                const displayDate = dateParts.length === 3 ? 
                    `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` : row[0];
                
                // Find the original index in currentData
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
            
            // Get date range
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
            
            // Load data if not already loaded
            if (currentData.length === 0) {
                await loadAllData();
            }
            
            if (!searchTerm) {
                // If no search term, show all data
                filteredData = currentData;
                displayData(currentData);
                updateStats(currentData);
                return;
            }
            
            filteredData = currentData.filter(row => {
                // Search in activity (index 1) and category (index 3)
                const activityMatch = row[1] && row[1].toLowerCase().includes(searchTerm);
                const categoryMatch = row[3] && row[3].toLowerCase().includes(searchTerm);
                return activityMatch || categoryMatch;
            });
            
            displayData(filteredData);
        }
        
        async function filterByDateRange() {
            const fromDate = document.getElementById('filterDateFrom').value;
            const toDate = document.getElementById('filterDateTo').value;
            
            // Load data if not already loaded
            if (currentData.length === 0) {
                await loadAllData();
            }
            
            if (!fromDate && !toDate) {
                // If no date filters, show all data
                filteredData = currentData;
                displayData(currentData);
                updateStats(currentData);
                return;
            }
            
            filteredData = currentData.filter(row => {
                const dateParts = row[0].split('-');
                if (dateParts.length !== 3) return false;
                
                // Convert DD-MM-YYYY to Date object
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
            // Reset to search prompt state
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
            
            // Convert date from DD-MM-YYYY to YYYY-MM-DD for input
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
                        // Reload data to reflect deletion
                        currentData = [];
                        filteredData = [];
                        if (document.getElementById('searchInput').value || 
                            document.getElementById('filterDateFrom').value || 
                            document.getElementById('filterDateTo').value) {
                            // If there are active filters, re-apply them
                            await loadAllData();
                        } else {
                            // Otherwise show search prompt
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
                        // Reload data to reflect deletion
                        currentData = [];
                        filteredData = [];
                        if (document.getElementById('searchInput').value || 
                            document.getElementById('filterDateFrom').value || 
                            document.getElementById('filterDateTo').value) {
                            // If there are active filters, re-apply them
                            await loadAllData();
                        } else {
                            // Otherwise show search prompt
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
                    // Reload data to reflect changes
                    currentData = [];
                    filteredData = [];
                    if (document.getElementById('searchInput').value || 
                        document.getElementById('filterDateFrom').value || 
                        document.getElementById('filterDateTo').value) {
                        // If there are active filters, re-apply them
                        await loadAllData();
                    } else {
                        // Otherwise show search prompt
                        showSearchPrompt();
                    }
                } else {
                    alert('Error updating entry: ' + result.message);
                }
            } catch (error) {
                alert('Error updating entry: ' + error);
            }
        });
    </script>
</body>
</html>
"""

# Create reports folder and HTML
os.makedirs("reports", exist_ok=True)
with open("index.html", "w") as f:
    f.write(html_content)

def signal_handler(sig, frame):
    print("\nServer stopped successfully")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Starting Life Tracker Web GUI...")
print("Open your browser and go to: http://localhost:8000")
print("Press Ctrl+C to stop the server")

try:
    httpd = HTTPServer(('0.0.0.0', 8000), LifeTrackerHandler)
    httpd.serve_forever()
except KeyboardInterrupt:
    print("Server stopped")

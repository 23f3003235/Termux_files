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
            
            scripts = {
                'daily': './daily2.awk',
                'category': './category2.awk', 
                'activity': './activity2.awk'
            }
            
            image_files = {
                'daily': 'reports/daily_activity_plot.png',
                'category': 'reports/category_plot.png',
                'activity': 'reports/activity_checklist.png'
            }
            
            if report_type in scripts:
                try:
                    result = subprocess.run(
                        [scripts[report_type], month], 
                        capture_output=True, 
                        text=True,
                        timeout=30
                    )
                    
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
                except Exception as e:
                    status = "error"
                    output = str(e)
            else:
                status = "error"
                output = "Invalid report type"
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": status, "output": output}).encode())

# HTML UI
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Life Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 600px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section { 
            margin: 20px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
        }
        input, select, button { 
            padding: 10px; 
            margin: 5px 0; 
            width: 100%; 
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }
        button { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            cursor: pointer; 
            font-size: 16px;
        }
        button:hover { background: #45a049; }
        .result { 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 5px; 
            font-size: 14px;
        }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        h1 { color: #333; text-align: center; }
        h2 { color: #555; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; }
        .new-category { display: none; margin-top: 10px; }
        .today-btn { 
            background: #2196F3; 
            padding: 8px 12px; 
            margin: 5px 0; 
            font-size: 14px; 
            width: auto; 
        }
        .preview-btn {
            background: #2196F3;
            margin-top: 10px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Life Tracker</h1>
        
        <div class="section">
            <h2>Add New Entry</h2>
            <form onsubmit="addEntry(event)">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="date" id="dateInput" style="flex: 1;" required>
                    <button type="button" class="today-btn" onclick="setToday()">Today</button>
                </div>
                <input type="text" name="activity" placeholder="Activity" required>
                <input type="number" name="minutes" placeholder="Minutes" required>
                
                <select id="categorySelect" onchange="handleCategoryChange()" required>
                    <option value="">Select Category</option>
                </select>
                
                <div id="newCategoryDiv" class="new-category">
                    <input type="text" id="newCategoryInput" placeholder="Enter new category">
                </div>
                
                <button type="submit">Add Entry</button>
            </form>
            <div id="addResult"></div>
        </div>
        
        <div class="section">
            <h2>Generate Reports</h2>
            
            <select id="reportType">
                <option value="daily">Daily Time Utilization</option>
                <option value="category">Category-wise Time</option>
                <option value="activity">Activity Statistics</option>
            </select>
            <input type="number" id="month" placeholder="Month (1-12)" min="1" max="12" required>
            <button onclick="generateReport()">Generate Report</button>
            <div id="reportResult"></div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            setToday();
        });
        
        function setToday() {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            document.getElementById('dateInput').value = formattedDate;
        }
        
        function formatDateForCSV(dateString) {
            const parts = dateString.split('-');
            if (parts.length === 3) {
                return `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            return dateString;
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
            if (!month) {
                alert('Please enter a month');
                return;
            }
            const formData = new FormData();
            formData.append('report_type', reportType);
            formData.append('month', month);
            const button = document.querySelector('button[onclick="generateReport()"]');
            const originalText = button.textContent;
            button.textContent = 'Generating...';
            button.disabled = true;
            try {
                const response = await fetch('/run_report', { method: 'POST', body: formData });
                const result = await response.json();
                const resultDiv = document.getElementById('reportResult');
                if (result.status === 'success') {
                    resultDiv.innerHTML = 
                        '<div class="result success">Report generated!<br>' +
                        '<a href="' + result.output + '" target="_blank">' +
                        '<button class="preview-btn">Preview Report</button></a></div>';
                } else {
                    resultDiv.innerHTML = '<div class="result error">Error: ' + result.output + '</div>';
                }
            } catch {
                document.getElementById('reportResult').innerHTML = '<div class="result error">Network error</div>';
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
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


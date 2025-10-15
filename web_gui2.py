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
                    # Run the script and capture both output and summary
                    result = subprocess.run(
                        [scripts[report_type], month], 
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
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
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
        .summary { 
            background: #e8f4fd; 
            color: #0c5460; 
            border-left: 4px solid #17a2b8;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
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
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 15px;
        }
        .summary-btn {
            background: #6c757d;
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 15px;
        }
        .summary-btn:hover { background: #5a6268; }
        .minimize-btn {
            background: #dc3545;
            margin: 5px 5px 5px 0;
            display: inline-block;
            width: auto;
            padding: 8px 15px;
        }
        .minimize-btn:hover { background: #c82333; }
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 10px;
        }
        .summary-section {
            margin-top: 10px;
            display: none;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 14px;
        }
        .data-table th, .data-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .data-table th {
            background: #f8f9fa;
            font-weight: bold;
            position: sticky;
            top: 0;
        }
        .data-table tr:nth-child(even) {
            background: #f9f9f9;
        }
        .data-table tr:hover {
            background: #f1f1f1;
        }
        .action-btn {
            padding: 4px 8px;
            margin: 0 2px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .edit-btn {
            background: #ffc107;
            color: #000;
        }
        .edit-btn:hover {
            background: #e0a800;
        }
        .delete-btn-sm {
            background: #dc3545;
            color: white;
            padding: 4px 8px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 5px;
        }
        .delete-btn-sm:hover {
            background: #c82333;
        }
        .stats-card {
            background: #e8f4fd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            border-left: 4px solid #17a2b8;
            font-size: 14px;
        }
        .filter-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border: 1px solid #e9ecef;
        }
        .filter-row {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            align-items: end;
        }
        .filter-group {
            flex: 1;
        }
        .filter-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
            display: block;
        }
        .date-filter-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .date-filter-buttons button {
            flex: 1;
        }
        
        /* Mobile responsive styles */
        @media (max-width: 600px) {
            .filter-row {
                flex-direction: column;
            }
            .date-filter-row {
                flex-direction: column;
            }
            .date-filter-buttons {
                flex-direction: column;
            }
            .button-group {
                flex-direction: column;
            }
            .data-table {
                font-size: 12px;
            }
            .data-table th, .data-table td {
                padding: 6px 4px;
            }
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
            
            <!-- Summary Section -->
            <div id="summarySection" class="summary-section">
                <h3>Report Summary</h3>
                <div id="summaryContent" class="result summary"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>Manage Data</h2>
            
            <div class="filter-section">
                <!-- Search Section -->
                <div class="filter-row">
                    <div class="filter-group" style="flex: 2;">
                        <span class="filter-label">Search Activities & Categories</span>
                        <input type="text" id="searchInput" placeholder="Enter activity or category name">
                    </div>
                    <button onclick="searchData()" style="width: auto;">Search</button>
                    <button onclick="loadAllData()" style="background: #6c757d; width: auto;">Show All</button>
                </div>
                
                <!-- Date Range Filter -->
                <div class="date-filter-row">
                    <div class="filter-row">
                        <div class="filter-group">
                            <span class="filter-label">From Date</span>
                            <input type="date" id="filterDateFrom">
                        </div>
                        <div class="filter-group">
                            <span class="filter-label">To Date</span>
                            <input type="date" id="filterDateTo">
                        </div>
                    </div>
                    
                    <!-- Date Filter Buttons - Now below the date fields -->
                    <div class="date-filter-buttons">
                        <button onclick="filterByDateRange()">Filter by Date Range</button>
                        <button onclick="clearDateFilters()" style="background: #dc3545;">Clear Date Filters</button>
                    </div>
                </div>
            </div>
            
            <!-- Stats Summary -->
            <div id="statsSummary" class="stats-card" style="display: none;">
                <strong>Summary:</strong> 
                <span id="totalEntries">0 entries</span> | 
                <span id="totalMinutes">0 minutes</span> | 
                <span id="dateRange">All dates</span>
            </div>
            
            <div id="tableContainer" style="overflow-x: auto; max-height: 500px; overflow-y: auto;">
                <table id="dataTable" class="data-table" style="display: none;">
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
                <div id="noDataMessage" style="text-align: center; padding: 40px; color: #6c757d; display: none;">
                    <div style="font-size: 18px; margin-bottom: 10px;">📊</div>
                    <div>No data found or CSV file is empty</div>
                    <div style="font-size: 12px; margin-top: 10px;">Add some entries using the form above</div>
                </div>
            </div>
            
            <!-- Edit Modal -->
            <div id="editModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center;">
                <div style="background: white; padding: 20px; border-radius: 10px; width: 90%; max-width: 500px;">
                    <h3>Edit Entry</h3>
                    <form id="editForm">
                        <input type="hidden" id="editIndex">
                        <input type="date" id="editDate" required style="width: 100%; margin: 5px 0; padding: 8px;">
                        <input type="text" id="editActivity" placeholder="Activity" required style="width: 100%; margin: 5px 0; padding: 8px;">
                        <input type="number" id="editMinutes" placeholder="Minutes" required style="width: 100%; margin: 5px 0; padding: 8px;">
                        <input type="text" id="editCategory" placeholder="Category" required style="width: 100%; margin: 5px 0; padding: 8px;">
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <button type="submit" style="flex: 1; background: #28a745;">Save Changes</button>
                            <button type="button" onclick="closeEditModal()" style="flex: 1; background: #6c757d;">Cancel</button>
                            <button type="button" onclick="deleteEntry()" style="flex: 1; background: #dc3545;">Delete Entry</button>
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
        
        document.addEventListener('DOMContentLoaded', function() {
            loadCategories();
            setToday();
            loadAllData();
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
                    loadAllData(); // Refresh the table
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
                        '<div class="result success">Report generated successfully!</div>' +
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
            const table = document.getElementById('dataTable');
            const noDataMessage = document.getElementById('noDataMessage');
            
            currentDisplayedData = data;
            
            if (data.length === 0) {
                table.style.display = 'none';
                noDataMessage.style.display = 'block';
                hideStats();
                return;
            }
            
            tableBody.innerHTML = '';
            table.style.display = 'table';
            noDataMessage.style.display = 'none';
            
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
        
        function showNoDataMessage() {
            document.getElementById('dataTable').style.display = 'none';
            document.getElementById('noDataMessage').style.display = 'block';
        }
        
        function searchData() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
            if (!searchTerm) {
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
            updateStats(filteredData);
        }
        
        function filterByDateRange() {
            const fromDate = document.getElementById('filterDateFrom').value;
            const toDate = document.getElementById('filterDateTo').value;
            
            if (!fromDate && !toDate) {
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
            updateStats(filteredData);
        }
        
        function clearDateFilters() {
            document.getElementById('filterDateFrom').value = '';
            document.getElementById('filterDateTo').value = '';
            document.getElementById('searchInput').value = '';
            filteredData = currentData;
            loadAllData();
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
                        loadAllData(); // Reload the data
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
                        loadAllData(); // Reload the data
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
                    loadAllData(); // Reload the data
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

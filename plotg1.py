import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
import subprocess
import os

# Your data from the awk script
dates = ['01-10-2025', '02-10-2025', '03-10-2025', '04-10-2025', '05-10-2025', 
         '06-10-2025', '07-10-2025', '08-10-2025', '09-10-2025', '10-10-2025', '11-10-2025']
minutes = [45, 30, 20, 30, 120, 60, 190, 200, 265, 300, 165]
hours = [0.75, 0.50, 0.33, 0.50, 2.00, 1.00, 3.17, 3.33, 4.42, 5.00, 2.75]

# Create the plot
plt.figure(figsize=(12, 7))
plt.plot(dates, minutes, marker='o', linestyle='-', color='blue', linewidth=2, label='Minutes')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Minutes', fontsize=12)
plt.title('Daily Activity Time (Last 11 days)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# Add value labels on points
for i, (date, min_val) in enumerate(zip(dates, minutes)):
    plt.annotate(f'{min_val}m', (date, min_val), textcoords="offset points", 
                 xytext=(0,10), ha='center', fontsize=8)

plt.tight_layout()

# Save the plot
try:
    file_path = '/sdcard/daily_activity_plot.png'
    plt.savefig(file_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"Plot successfully saved as: {file_path}")
    
except Exception as e:
    print(f"Error: {e}")

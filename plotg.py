import matplotlib.pyplot as plt
import csv
import os

# Read data from plotdata.csv using built-in CSV module
dates = []
minutes = []
hours = []

try:
    with open('plotdata.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 3:  # Ensure row has at least 3 columns
                dates.append(row[0])
                minutes.append(int(row[1]))  # Convert to int
                hours.append(float(row[2]))  # Convert to float
    
    print(f"Loaded {len(dates)} records from plotdata.csv")
    
except FileNotFoundError:
    print("Error: plotdata.csv file not found!")
    exit()
except Exception as e:
    print(f"Error reading plotdata.csv: {e}")
    exit()

# Create the plot
plt.figure(figsize=(12, 7))
plt.plot(dates, minutes, marker='o', linestyle='-', color='blue', linewidth=2, label='Minutes')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Minutes', fontsize=12)
plt.title(f'Daily Activity Time (Last {len(dates)} days)', fontsize=14)
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

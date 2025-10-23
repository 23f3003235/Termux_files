import matplotlib.pyplot as plt
import csv

# Read data from plotdata.csv
categories = []
minutes = []

try:
    with open("plotdata.csv", 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 3:
                categories.append(row[1])
                minutes.append(int(row[2]))
        print(f"Loaded {len(categories)} categories from plotdata.csv")
except FileNotFoundError:
    print("Error: plotdata.csv file not found!")
    exit()
except Exception as e:
    print(f"Error reading plotdata.csv: {e}")
    exit()

# Create the category plot
plt.figure(figsize=(10, 8))
plt.bar(categories, minutes, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc'])
plt.xlabel('Categories', fontsize=12)
plt.ylabel('Minutes', fontsize=12)
plt.title('Category-wise Activity Time', fontsize=14)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# Add value labels on bars
for i, (cat, min_val) in enumerate(zip(categories, minutes)):
    plt.text(i, min_val + max(minutes)*0.01, f'{min_val}', 
             ha='center', va='bottom', fontsize=10)

plt.tight_layout()

# Save the plot
try:
    file_path = '/data/data/com.termux/files/home/termux_files/reports/category_plot.png'
    plt.savefig(file_path, dpi=100, bbox_inches='tight')
    plt.close()
    #print(f"Category plot successfully saved as: {file_path}")
except Exception as e:
    print(f"Error saving plot: {e}")

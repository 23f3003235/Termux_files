import matplotlib.pyplot as plt
import csv
import sys
import textwrap

month_name = sys.argv[1]
year_val = sys.argv[2]
plot_file = sys.argv[3]

categories = []
minutes = []

with open("category_total.csv") as f:
    reader = csv.reader(f)
    next(reader) # Skip header "Month,Year"
    next(reader) # Skip value row for month/year
    next(reader) # Skip header for category/minutes
    for row in reader:
        categories.append(row[0])
        minutes.append(int(row[1]))

# Sort data by minutes (descending) for better visualization
combined = list(zip(categories, minutes))
combined.sort(key=lambda x: x[1], reverse=True)
categories, minutes = zip(*combined)

# Create figure
plt.figure(figsize=(12, 8))

# Create bars with color gradient (darker = more minutes)
colors = plt.cm.Blues([x/max(minutes) for x in minutes])
bars = plt.bar(categories, minutes, color=colors, edgecolor='black', linewidth=0.5)

# Customize the plot
plt.xlabel("Category", fontsize=12, fontweight='bold')
plt.ylabel("Total Minutes", fontsize=12, fontweight='bold')
plt.title(f"{month_name} {year_val} - Category Minutes\nTotal: {sum(minutes)} minutes", 
          fontsize=14, fontweight='bold', pad=20)

# Wrap x-axis labels and rotate
wrapped_labels = [textwrap.fill(label, width=12) for label in categories]
plt.xticks(range(len(categories)), wrapped_labels, rotation=45, ha='right')

# Add value labels on bars
for bar, value in zip(bars, minutes):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
             f'{value}', ha='center', va='bottom', fontweight='bold', fontsize=9)

# Add percentage labels
total = sum(minutes)
for i, (bar, value) in enumerate(zip(bars, minutes)):
    percentage = (value / total) * 100
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, 
             f'{percentage:.1f}%', ha='center', va='center', 
             fontweight='bold', color='white', fontsize=8)

plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()

# Save the plot
file_path = f'/sdcard/{plot_file}'
plt.savefig(file_path, dpi=120, bbox_inches='tight', facecolor='white')
plt.close()

print(f"Plot saved as: {file_path}")

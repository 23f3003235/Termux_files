import matplotlib.pyplot as plt
import csv
import sys

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

plt.figure(figsize=(8,5))
plt.bar(categories, minutes, color="teal")
plt.xlabel("Category")
plt.ylabel("Total Minutes")
plt.title(f"{month_name} {year_val} - Category Minutes")
plt.tight_layout()
file_path = '/sdcard/plot_file'
plt.savefig(file_path, dpi=100, bbox_inches='tight')
plt.show()


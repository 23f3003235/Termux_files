import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

df = pd.read_csv("checklist.csv")

# Convert dates to datetime and sort
df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
df = df.sort_values('Date')

# Get sorted dates and activities
dates = df["Date"].dt.strftime('%d-%m-%Y').tolist()
acts = df.columns[1:]
mat = df.iloc[:,1:].fillna(0).astype(int).values

# Create figure
fig, ax = plt.subplots(figsize=(len(dates)*0.6 + 2, len(acts)*0.6 + 2))

# Create custom colormap
cmap = ListedColormap(['lightgray', 'limegreen'])

# Create heatmap
im = ax.imshow(mat.T, cmap=cmap, aspect='auto')

# Customize axes
ax.set_xticks(range(len(dates)))
ax.set_yticks(range(len(acts)))
ax.set_xticklabels(dates, rotation=45, ha='right')
ax.set_yticklabels(acts)

# Add value annotations
for i in range(len(dates)):
    for j in range(len(acts)):
        text = '✓' if mat[i][j] == 1 else '○'
        color = 'white' if mat[i][j] == 1 else 'black'
        ax.text(i, j, text, ha='center', va='center', 
               fontsize=10, fontweight='bold', color=color)

plt.xlabel("Date", fontsize=12, fontweight='bold')
plt.ylabel("Activity", fontsize=12, fontweight='bold')
plt.title("Daily Activity Checklist - " + dates[0][3:5], fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("/storage/emulated/0/activity_checklist.png", dpi=150, bbox_inches='tight')
plt.show()

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("checklist.csv")
dates = df["Date"].tolist()
acts = df.columns[1:]
mat = df.iloc[:,1:].fillna(0).astype(int).values

# Create figure with better size
fig, ax = plt.subplots(figsize=(len(dates)*0.5 + 2, len(acts)*0.6 + 2))

# Plot the activities with better styling
for i, date in enumerate(dates):
    for j, act in enumerate(acts):
        if mat[i][j]:
            ax.plot(i, j, "s", markersize=10, color="green", 
                   markeredgecolor='darkgreen', markeredgewidth=1)

# Customize axes
ax.set_xticks(range(len(dates)))
ax.set_yticks(range(len(acts)))
ax.set_xticklabels(dates, rotation=45, ha='right')
ax.set_yticklabels(acts)

# Add labels and title
plt.xlabel("Date", fontsize=12, fontweight='bold')
plt.ylabel("Activity", fontsize=12, fontweight='bold')
plt.title("Daily Activity Checklist - " + dates[0][3:5], fontsize=14, fontweight='bold')

# Add grid for better readability
ax.grid(True, alpha=0.3, linestyle='-', color='gray')

# Set better limits
ax.set_xlim(-0.5, len(dates)-0.5)
ax.set_ylim(-0.5, len(acts)-0.5)

# Invert Y-axis to have activities from top to bottom
ax.invert_yaxis()

plt.tight_layout()
plt.savefig("/storage/emulated/0/activity_checklist.png", dpi=150, bbox_inches='tight')
plt.show()

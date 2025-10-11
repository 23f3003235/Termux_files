import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

# Plot using scatter (no colormap issues)
for i in range(len(dates)):
    for j in range(len(acts)):
        if mat[i][j] == 1:
            # Green square for completed
            ax.add_patch(plt.Rectangle((i-0.4, j-0.4), 0.8, 0.8, 
                                     facecolor='limegreen', edgecolor='darkgreen'))
            ax.text(i, j, '✓', ha='center', va='center', 
                   fontsize=12, fontweight='bold', color='white')
        else:
            # Gray circle for not completed
            ax.add_patch(plt.Circle((i, j), 0.3, 
                                  facecolor='lightgray', edgecolor='gray', alpha=0.7))
            ax.text(i, j, '○', ha='center', va='center', 
                   fontsize=10, color='gray')

# Customize axes
ax.set_xticks(range(len(dates)))
ax.set_yticks(range(len(acts)))
ax.set_xticklabels(dates, rotation=45, ha='right')
ax.set_yticklabels(acts)

plt.xlabel("Date", fontsize=12, fontweight='bold')
plt.ylabel("Activity", fontsize=12, fontweight='bold')
plt.title("Daily Activity Checklist - " + dates[0][3:5], fontsize=14, fontweight='bold')

# Set limits
ax.set_xlim(-0.5, len(dates)-0.5)
ax.set_ylim(-0.5, len(acts)-0.5)

plt.tight_layout()
plt.savefig("/storage/emulated/0/activity_checklist.png", dpi=150, bbox_inches='tight')
plt.show()

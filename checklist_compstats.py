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

# Calculate completion rates
completion_rates = mat.sum(axis=0) / len(dates) * 100  # % per activity
daily_completion = mat.sum(axis=1) / len(acts) * 100   # % per day

# Create subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(len(dates)*0.5 + 2, 10), 
                               gridspec_kw={'height_ratios': [3, 1]})

# FIX: Create custom colormap and use .T (transpose) correctly
cmap = ListedColormap(['#f0f0f0', '#2ecc71'])
im = ax1.imshow(mat.T, cmap=cmap, aspect='auto')  # FIXED: mat.T not mat.I

# Add checkmarks
for i in range(len(dates)):
    for j in range(len(acts)):
        if mat[i][j] == 1:
            ax1.text(i, j, '✓', ha='center', va='center', 
                    fontsize=12, fontweight='bold', color='white')
        else:
            ax1.text(i, j, '○', ha='center', va='center', 
                    fontsize=10, color='gray', alpha=0.7)

# Customize main plot
ax1.set_xticks(range(len(dates)))
ax1.set_yticks(range(len(acts)))
ax1.set_xticklabels(dates, rotation=45, ha='right')
ax1.set_yticklabels(acts)
ax1.set_title("Daily Activity Checklist - " + dates[0][3:5], fontsize=14, fontweight='bold')

# Daily completion bar chart
bars = ax2.bar(range(len(dates)), daily_completion, color='skyblue', alpha=0.7)
ax2.set_xticks(range(len(dates)))
ax2.set_xticklabels(dates, rotation=45, ha='right')
ax2.set_ylabel('Completion %')
ax2.set_ylim(0, 100)
ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50% Target')
ax2.legend()

# Add percentage labels on bars
for bar, pct in zip(bars, daily_completion):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
             f'{pct:.0f}%', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig("/storage/emulated/0/activity_checklist.png", dpi=150, bbox_inches='tight')
plt.show()

# Print summary statistics
print(f"\n📊 Activity Completion Summary:")
for act, rate in zip(acts, completion_rates):
    print(f"  {act}: {rate:.1f}%")
print(f"\n📅 Best day: {dates[np.argmax(daily_completion)]} ({daily_completion.max():.1f}%)")
print(f"📅 Worst day: {dates[np.argmin(daily_completion)]} ({daily_completion.min():.1f}%)")

import matplotlib.pyplot as plt

dates = []
minutes = []

with open('october_data.csv', 'r') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) != 3:
            continue  # skip summary or bad lines
        date, mins, _ = parts
        dates.append(date)
        minutes.append(int(mins))

plt.figure(figsize=(10,5))
plt.plot(dates, minutes, marker='o')
plt.xticks(rotation=45)
plt.xlabel('Date')
plt.ylabel('Minutes')
plt.title('Daily Minutes - Month')
plt.tight_layout()
plt.show()


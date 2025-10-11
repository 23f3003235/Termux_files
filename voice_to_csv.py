import subprocess
import csv

csv_file = "lt.csv"
print("Speak your entry as: date,category,minutes,remarks")
result = subprocess.run(['termux-speech-to-text'], stdout=subprocess.PIPE)
voice_text = result.stdout.decode().strip()

print("Heard:", voice_text)
row = [field.strip() for field in voice_text.split(',')]

with open(csv_file, "a", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(row)


#!/data/data/com.termux/files/usr/bin/bash
CSV_FILE="lt.csv"

echo "Speak your entry as: date,category,minutes,remarks"
VOICE=$(termux-speech-to-text)
echo "Heard: $VOICE"

# Direct append to CSV, expecting comma-separated values
echo "$VOICE" >> "$CSV_FILE"


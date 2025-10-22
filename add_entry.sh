#!/data/data/com.termux/files/usr/bin/bash
ACTIVITY=$(termux-dialog text -t "Enter Activity" | jq -r '.text')
MINUTES=$(termux-dialog text -t "Enter Minutes" | jq -r '.text')
CATEGORY=$(termux-dialog text -t "Enter Category" | jq -r '.text')
DATE=$(date +"%d-%m-%Y")
echo "$DATE,$ACTIVITY,$MINUTES,$CATEGORY" >> ~/lifetracker.csv
termux-toast "✅ Entry added!"


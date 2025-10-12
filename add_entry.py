import pandas as pd
import os
from datetime import datetime

def get_user_input():
    # Read existing data to get unique categories
    try:
        df = pd.read_csv("lifetracker.csv", header=None)
        existing_categories = df[3].unique().tolist()  # 4th column (index 3)
        print("Existing categories:", existing_categories)
    except:
        existing_categories = []
        print("No existing categories found (new file)")
    
    # Input 1: Date (dd-mm-yyyy)
    while True:
        date_input = input("Enter date (dd-mm-yyyy): ").strip()
        try:
            # Validate date format
            datetime.strptime(date_input, '%d-%m-%Y')
            break
        except ValueError:
            print("Invalid date format! Please use dd-mm-yyyy")
    
    # Input 2: Activity
    activity = input("Enter activity: ").strip()
    
    # Input 3: Minutes
    while True:
        try:
            minutes = int(input("Enter minutes: ").strip())
            if minutes > 0:
                break
            else:
                print("Please enter a positive number")
        except ValueError:
            print("Please enter a valid number")
    
    # Input 4: Category
    print("\nAvailable categories:")
    for i, cat in enumerate(existing_categories, 1):
        print(f"{i}. {cat}")
    print(f"{len(existing_categories) + 1}. Enter new category")
    
    while True:
        try:
            cat_choice = input(f"Choose category (1-{len(existing_categories) + 1}): ").strip()
            choice_num = int(cat_choice)
            
            if 1 <= choice_num <= len(existing_categories):
                category = existing_categories[choice_num - 1]
                break
            elif choice_num == len(existing_categories) + 1:
                category = input("Enter new category: ").strip()
                break
            else:
                print(f"Please enter a number between 1 and {len(existing_categories) + 1}")
        except ValueError:
            print("Please enter a valid number")
    
    return date_input, activity, minutes, category

def append_to_csv(date, activity, minutes, category):
    # Create the line to append
    new_line = f"{date},{activity},{minutes},{category}\n"
    
    # Append to file
    with open("lifetracker.csv", "a") as f:
        f.write(new_line)
    
    print(f"\n✅ Successfully added to lifetracker.csv:")
    print(f"   Date: {date}")
    print(f"   Activity: {activity}")
    print(f"   Minutes: {minutes}")
    print(f"   Category: {category}")

def main():
    print("📝 Life Tracker - Add New Entry")
    print("=" * 40)
    
    # Get user input
    date, activity, minutes, category = get_user_input()
    
    # Append to CSV
    append_to_csv(date, activity, minutes, category)

if __name__ == "__main__":
    main()

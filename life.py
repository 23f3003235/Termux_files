import pandas as pd
import os
import subprocess
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

def add_entry():
    print("\n📝 ADD NEW ENTRY")
    print("=" * 40)
    
    # Get user input
    date, activity, minutes, category = get_user_input()
    
    # Append to CSV
    append_to_csv(date, activity, minutes, category)

def daily_time_utilization():
    print("\n📊 DAILY TIME UTILIZATION")
    print("=" * 40)
    
    while True:
        try:
            month = int(input("Enter month number (1-12): ").strip())
            if 1 <= month <= 12:
                break
            else:
                print("Please enter a number between 1 and 12")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"Executing daily time utilization for month {month}...")
    try:
        subprocess.run(["./daily2.awk", str(month)], check=True)
        print("✅ Daily time utilization completed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error executing daily2.awk")
    except FileNotFoundError:
        print("❌ daily2.awk file not found!")

def categorywise_time_utilization():
    print("\n📈 CATEGORY-WISE TIME UTILIZATION")
    print("=" * 40)
    
    while True:
        try:
            month = int(input("Enter month number (1-12): ").strip())
            if 1 <= month <= 12:
                break
            else:
                print("Please enter a number between 1 and 12")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"Executing category-wise time utilization for month {month}...")
    try:
        subprocess.run(["./category2.awk", str(month)], check=True)
        print("✅ Category-wise time utilization completed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error executing category2.awk")
    except FileNotFoundError:
        print("❌ category2.awk file not found!")

def activity_statistics():
    print("\n📋 ACTIVITY STATISTICS")
    print("=" * 40)
    
    while True:
        try:
            month = int(input("Enter month number (1-12): ").strip())
            if 1 <= month <= 12:
                break
            else:
                print("Please enter a number between 1 and 12")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"Executing activity statistics for month {month}...")
    try:
        subprocess.run(["./activity2.awk", str(month)], check=True)
        print("✅ Activity statistics completed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error executing activity2.awk")
    except FileNotFoundError:
        print("❌ activity2.awk file not found!")

def display_menu():
    print("\n" + "=" * 50)
    print("🎯 LIFE TRACKER - MAIN MENU")
    print("=" * 50)
    print("1. 📝 Add New Entry")
    print("2. 📊 Daily Time Utilization")
    print("3. 📈 Category-wise Time Utilization") 
    print("4. 📋 Activity Statistics")
    print("5. ❌ Exit")
    print("=" * 50)

def main():
    while True:
        display_menu()
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            add_entry()
        elif choice == '2':
            daily_time_utilization()
        elif choice == '3':
            categorywise_time_utilization()
        elif choice == '4':
            activity_statistics()
        elif choice == '5':
            print("\n👋 Thank you for using Life Tracker! Goodbye!")
            break
        else:
            print("❌ Invalid choice! Please enter 1-5")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()

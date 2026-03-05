import requests
import csv
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generate_report import generate_html
from core.activity_tracker import track_activity

# Load variables from .env
load_dotenv()

ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
SOURCE_ID = os.getenv('SOURCE_ID')
ACCOUNTS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'accounts.csv')
CSV_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'ig_growth_tracker_wide.csv')

def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_CSV):
        with open(ACCOUNTS_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                accounts.append(row['Handle'].strip())
    return accounts

def track_growth():
    if not ACCESS_TOKEN or not SOURCE_ID:
        print("Error: FB_ACCESS_TOKEN or SOURCE_ID missing in .env")
        return

    target_handles = load_accounts()
    if not target_handles:
        print(f"Error: No accounts found in {ACCOUNTS_CSV}")
        return

    # 1. Track Followers
    date = datetime.now().strftime("%Y-%m-%d")
    current_stats = {'Date': date}
    
    for handle in target_handles:
        print(f"Fetching followers for @{handle}...")
        url = f"https://graph.facebook.com/v19.0/{SOURCE_ID}"
        params = {
            'fields': f"business_discovery.username({handle}){{followers_count,username}}",
            'access_token': ACCESS_TOKEN
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'business_discovery' in data:
                followers = data['business_discovery']['followers_count']
                username = data['business_discovery']['username']
                current_stats[username] = followers
                print(f"✅ Fetched {followers} followers for @{username}")
            else:
                print(f"❌ Error fetching @{handle}: {data.get('error', {}).get('message', 'Unknown error')}")
                current_stats[handle] = 'N/A'
        except Exception as e:
            print(f"❌ Exception for @{handle}: {e}")
            current_stats[handle] = 'Error'

    # Save followers to wide format CSV
    file_exists = os.path.isfile(CSV_FILE)
    fieldnames = ['Date'] + target_handles
    existing_data = []
    
    if file_exists:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Filter out old fieldnames that are no longer in TARGET_HANDLES
            for row in reader:
                filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                existing_data.append(filtered_row)
    
    updated = False
    for row in existing_data:
        if row['Date'] == date:
            row.update(current_stats)
            updated = True
            break
    if not updated:
        existing_data.append(current_stats)

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data)
    
    print(f"✅ Follower data saved to {CSV_FILE}")

    # Create a daily backup copy
    backup_file = os.path.join(os.path.dirname(CSV_FILE), 'daily_backups', f'growth_log_{date}.csv')
    try:
        import shutil
        shutil.copy2(CSV_FILE, backup_file)
        print(f"✅ Daily backup created: {backup_file}")
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")
    
    # 2. Track Activity (Latest Post Date)
    print("\nChecking account activity...")
    track_activity()

    # 3. Generate HTML report
    print("\nGenerating HTML report...")
    generate_html()

if __name__ == "__main__":
    track_growth()
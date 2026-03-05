import requests
import csv
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
ACTIVITY_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'ig_activity_tracker.csv')
ACCOUNTS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'accounts.csv')

def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_CSV):
        with open(ACCOUNTS_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                accounts.append(row['Handle'].strip())
    return accounts

def track_activity():
    load_dotenv()
    access_token = os.getenv('FB_ACCESS_TOKEN')
    source_id = os.getenv('SOURCE_ID')
    
    if not access_token or not source_id:
        print("Error: FB_ACCESS_TOKEN or SOURCE_ID missing in .env")
        return

    target_handles = load_accounts()
    if not target_handles:
        print(f"Error: No accounts found in {ACCOUNTS_CSV}")
        return

    # Initialize data dictionary
    activity_data = {}
    
    # Load existing activity data if available
    if os.path.exists(ACTIVITY_CSV):
        with open(ACTIVITY_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                activity_data[row['Username']] = row['LastPostDate']

    for handle in target_handles:
        print(f"Checking activity for @{handle}...")
        url = f"https://graph.facebook.com/v19.0/{source_id}"
        # We fetch the media field within business_discovery to get the latest post timestamp
        params = {
            'fields': f"business_discovery.username({handle}){{media.limit(1){{timestamp}}}}",
            'access_token': access_token
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'business_discovery' in data and 'media' in data['business_discovery']:
                media_list = data['business_discovery']['media']['data']
                if media_list:
                    last_post_time = media_list[0]['timestamp']
                    # Convert ISO timestamp to YYYY-MM-DD
                    last_post_date = last_post_time.split('T')[0]
                    activity_data[handle] = last_post_date
                    print(f"✅ Last post for @{handle}: {last_post_date}")
                else:
                    activity_data[handle] = "No posts"
                    print(f"ℹ️ No posts found for @{handle}")
            else:
                print(f"❌ Error fetching activity for @{handle}: {data.get('error', {}).get('message', 'Unknown error')}")
                if handle not in activity_data:
                    activity_data[handle] = "Error/Unknown"
        except Exception as e:
            print(f"❌ Exception for @{handle}: {e}")
            if handle not in activity_data:
                activity_data[handle] = "Exception"

    # Write activity data to CSV (Current status format)
    with open(ACTIVITY_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Username', 'LastPostDate'])
        writer.writeheader()
        for username, last_date in activity_data.items():
            writer.writerow({'Username': username, 'LastPostDate': last_date})
    
    print(f"✅ Activity data saved to {ACTIVITY_CSV}")

if __name__ == "__main__":
    track_activity()

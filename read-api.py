import requests
import json
import time
import random
from datetime import datetime

# Function to get the current timestamp
def get_current_timestamp():
    return int(datetime.now().timestamp())

# Base URL for the API
base_url = "https://api.flightradar24.com/common/v1/airport.json?code=vno&plugin[]=&plugin-setting[schedule][mode]={mode}&plugin-setting[schedule][timestamp]={timestamp}&page={page}&limit=100&fleet=&token="

# Headers to simulate a Chrome browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Function to fetch data and save as JSON
def fetch_and_save(mode, page):
    timestamp = get_current_timestamp()
    url = base_url.format(mode=mode, page=page, timestamp=timestamp)
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()  # Parse JSON response

        # Save to file with UTF-8 encoding
        filename = f"airport_{mode}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # ensure_ascii=False allows special characters
        print(f"Data saved to {filename}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Infinite loop to run the script forever
while True:
    # Fetch arrivals and departures with random pause
    for mode in ["arrivals", "departures"]:
        for page in ["-1", "1"]:
            print(f"Fetching {mode}, page {page}")
            fetch_and_save(mode, page)
            
            # Add a random pause between 60 to 360 seconds
            pause_duration1 = random.randint(60, 300)
            pause_duration2 = random.randint(10, 60)
            pause_duration2 = random.randint(10, 60)
            pause_duration = pause_duration1 + pause_duration2
            print(f"Waiting for {pause_duration} seconds before the next request...")
            time.sleep(pause_duration)

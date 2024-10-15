import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sqlite3
import time

# Function to retrieve and clean HTML from a specific page
def get_clean_html(page):
    url = f"https://www.vilnius-airport.lt/en/before-the-flight/flights-information/flights-schedule?direction=arrival&destination=&date-from=2024-10-13&date-to=&page={page}"
    ua = UserAgent()
    headers = {
        'User-Agent': ua.firefox  # Random Firefox user agent
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove all <del> tags
        for del_tag in soup.find_all('del'):
            del_tag.decompose()

        # Extract the desired HTML portion
        lines = str(soup).splitlines()
        start_line = 1000 + 74
        end_line = None
        for i, line in enumerate(lines):
            if '<nav aria-label="navigation" class="text-center">' in line:
                end_line = i
                break

        cleaned_html_lines = []
        for line in lines[start_line:end_line]:
            cleaned_line = line.lstrip()
            cleaned_html_lines.append(cleaned_line)

        return '\n'.join(cleaned_html_lines)
    else:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
        return None

# Function to parse the arrivals data
def extract_arrival_data(html_snippet):
    soup = BeautifulSoup(html_snippet, 'html.parser')
    arrivals_data = []

    arrival_rows = soup.select('tbody.dumb-pager-items tr')
    for row in arrival_rows:
        time = row.select_one('td[data-label="Time"] span.light-sm').text.strip()
        estimated_time_span = row.select_one('td[data-label="Estimated time"] span.bold-lg')
        estimated_date_span = row.select_one('td[data-label="Estimated time"] span.light-sm')
        estimated_time = f"{estimated_date_span.text.strip()} {estimated_time_span.text.strip()}" if estimated_time_span and estimated_date_span else None
        arrives_from = row.select_one('td[data-label="Arrives from"] span.bold-lg').text.strip()
        arrives_from_airline = row.select_one('td[data-label="Arrives from"] span.light-sm').text.strip()
        flight_number = row.select_one('td[data-label="Flight number"] a.bold-lg').text.strip()

        modal_id = row['data-target'].replace('#', '')
        modal = soup.find('div', id=modal_id)

        if modal:
            departs_to = modal.find('span', string="Departs to:").find_next_sibling('span').text.strip() if modal.find('span', string="Departs to:") else None
            arrival_time = modal.find('span', string="Arrival Time:").find_next_sibling('span').text.strip() if modal.find('span', string="Arrival Time:") else None
            scheduled_date = f"{time} {arrival_time}" if time and arrival_time else None
            landed = modal.find('span', string="Landed:").find_next_sibling('span').text.strip() if modal.find('span', string="Landed:") else None
            status = modal.find('span', string="Status:").find_next_sibling('span').text.strip() if modal.find('span', string="Status:") else None

            if status == "On time" or not status:
                estimated_time = scheduled_date

            arrival_info = {
                "Time": time,
                "Estimated Time": estimated_time,
                "Scheduled Time": scheduled_date,
                "Arrives From": arrives_from,
                "Airline": arrives_from_airline,
                "Flight Number": flight_number,
                "Departs To": departs_to,
                "Arrival Time": arrival_time,
                "Landed": landed,
                "Status": status,
            }
            arrivals_data.append(arrival_info)
    return arrivals_data

# Function to save arrival data to the database
def save_to_database(arrivals_data, db_file_path):
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arrivals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_date TEXT,
                estimated_time TEXT,
                arrives_from TEXT,
                airline TEXT,
                flight_number TEXT,
                departs_to TEXT,
                landed TEXT,
                status TEXT
            )
        ''')

        for arrival in arrivals_data:
            cursor.execute('''
                SELECT * FROM arrivals
                WHERE scheduled_date = ? AND arrives_from = ? AND airline = ? AND flight_number = ? AND departs_to = ?
            ''', (arrival["Scheduled Time"], arrival["Arrives From"], arrival["Airline"], arrival["Flight Number"], arrival["Departs To"]))

            existing_arrival = cursor.fetchone()

            if existing_arrival:
                updates = []
                if existing_arrival[2] != arrival["Estimated Time"]:
                    updates.append(f"Estimated Time: {existing_arrival[2]} -> {arrival['Estimated Time']}")
                if existing_arrival[7] != arrival["Landed"]:
                    updates.append(f"Landed: {existing_arrival[7]} -> {arrival['Landed']}")
                if existing_arrival[8] != arrival["Status"]:
                    updates.append(f"Status: {existing_arrival[8]} -> {arrival['Status']}")

                if updates:
                    cursor.execute('''
                        UPDATE arrivals
                        SET estimated_time = ?, landed = ?, status = ?
                        WHERE id = ?
                    ''', (arrival["Estimated Time"], arrival["Landed"], arrival["Status"], existing_arrival[0]))
                    print(f"Flight {arrival['Flight Number']} (Scheduled: {arrival['Scheduled Time']}): Updated -> {', '.join(updates)}")
            else:
                cursor.execute('''
                    INSERT INTO arrivals (
                        scheduled_date, estimated_time, arrives_from, airline, flight_number, departs_to, landed, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    arrival["Scheduled Time"],
                    arrival["Estimated Time"],
                    arrival["Arrives From"],
                    arrival["Airline"],
                    arrival["Flight Number"],
                    arrival["Departs To"],
                    arrival["Landed"],
                    arrival["Status"],
                ))
                print(f"Added new flight: {arrival['Flight Number']} (Scheduled: {arrival['Scheduled Time']})")
        conn.commit()

def main():
    db_file_path = r"C:\Users\zabit\Documents\GitHub\planespotting-time-finder\second_version\arrivals.db"

    # Infinite loop to run the script indefinitely
    while True:
        # Process all pages from 1 to 10
        for page in range(1, 11):
            print(f"Processing page {page}...")
            html_snippet = get_clean_html(page)
            if html_snippet:
                arrivals_data = extract_arrival_data(html_snippet)
                save_to_database(arrivals_data, db_file_path)
            time.sleep(30)  # Delay between pages (e.g., 30 seconds)

        # Add a delay after processing all pages (e.g., 15 minutes) to avoid overwhelming the server
        print("Waiting for 15 minutes before the next run...")
        time.sleep(900)  # Wait for 15 minutes (900 seconds) before the next cycle


if __name__ == "__main__":
    main()

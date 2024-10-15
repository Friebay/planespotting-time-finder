import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sqlite3
import time

# Function to retrieve and clean HTML from a specific page (for departures)
def get_clean_html(page):
    url = f"https://www.vilnius-airport.lt/en/before-the-flight/flights-information/flights-schedule?direction=departure&destination=&date-from=2024-10-13&date-to=&page={page}"
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

# Function to parse the departures data
def extract_departure_data(html_snippet):
    soup = BeautifulSoup(html_snippet, 'html.parser')
    # print(soup)
    departures_data = []

    departure_rows = soup.select('tbody.dumb-pager-items tr')
    for row in departure_rows:
        # Extract the time and date
        # print(type(row))
        time = row.select_one('td[data-label="Time"] span.bold-lg').text.strip()
        # If time is empty, search for it inside the modal (e.g., <span> 21:40 </span>)
        if time == '':
            modal_id = row['data-target'].replace('#', '')
            modal = soup.find('div', id=modal_id)

            if modal:
                # Look for the time inside the modal under "Departure Time"
                departure_time_span = modal.find('span', string="Departure Time:")
                if departure_time_span:
                    time = departure_time_span.find_next_sibling('span').text.strip()  # Extract the time (e.g., 21:40)
        date = row.select_one('td[data-label="Time"] span.light-sm').text.strip()  # Get the date (e.g., 2024-10-14)
        
        # Format the scheduled date (combining date and time)
        scheduled_date = f"{date} {time}"  # Format as YYYY-MM-DD HH:MM

        # Extract other data
        estimated_time_span = row.select_one('td[data-label="Estimated time"] span.bold-lg')
        estimated_date_span = row.select_one('td[data-label="Estimated time"] span.light-sm')
        estimated_time = f"{estimated_date_span.text.strip()} {estimated_time_span.text.strip()}" if estimated_time_span and estimated_date_span else None
        departs_to = row.select_one('td[data-label="Departs to"] span.bold-lg').text.strip()
        departs_to_airline = row.select_one('td[data-label="Departs to"] span.light-sm').text.strip()
        flight_number = row.select_one('td[data-label="Flight number"] a.bold-lg').text.strip()

        modal_id = row['data-target'].replace('#', '')
        modal = soup.find('div', id=modal_id)

        # Extract additional information from the modal
        if modal:
            status = modal.find('span', string="Status:").find_next_sibling('span').text.strip() if modal.find('span', string="Status:") else None

            # If no estimated time, use the scheduled time
            if not estimated_time:
                estimated_time = scheduled_date

            departure_info = {
                "Time": time,
                "Estimated Time": estimated_time,
                "Scheduled Time": scheduled_date,
                "Departs To": departs_to,
                "Airline": departs_to_airline,
                "Flight Number": flight_number,
                "Status": status,
            }
            # print(departure_info)
            departures_data.append(departure_info)

    return departures_data

# Function to save departure data to the database
# Function to save departure data to the database
def save_to_database(departures_data, db_file_path):
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()

        # Create table if it doesn't exist, without the departure_time column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_date TEXT,
                estimated_time TEXT,
                departs_to TEXT,
                airline TEXT,
                flight_number TEXT,
                status TEXT
            )
        ''')

        for departure in departures_data:
            cursor.execute('''
                SELECT * FROM departures
                WHERE scheduled_date = ? AND departs_to = ? AND airline = ? AND flight_number = ?
            ''', (departure["Scheduled Time"], departure["Departs To"], departure["Airline"], departure["Flight Number"]))

            existing_departure = cursor.fetchone()

            if existing_departure:
                updates = []

                # Function to normalize strings (handles None and strips whitespace)
                def normalize_string(value):
                    return value.strip() if value else ""

                # Compare estimated time with normalization
                if normalize_string(existing_departure[2]) != normalize_string(departure["Estimated Time"]):
                    updates.append(f"Estimated Time: {existing_departure[2]} -> {departure['Estimated Time']}")

                # Compare status with normalization
                existing_status = normalize_string(existing_departure[6])
                # print(existing_status)
                new_status = normalize_string(departure["Status"])
                # print(new_status)

                if existing_status != new_status:
                    updates.append(f"Status: {existing_status} -> {new_status}")

                # Only update if there are changes
                if updates:
                    cursor.execute('''
                        UPDATE departures
                        SET estimated_time = ?, status = ?
                        WHERE id = ?
                    ''', (departure["Estimated Time"], departure["Status"], existing_departure[0]))
                    print(f"Flight {departure['Flight Number']} (Scheduled: {departure['Scheduled Time']}): Updated -> {', '.join(updates)}")
            else:
                cursor.execute('''
                    INSERT INTO departures (
                        scheduled_date, estimated_time, departs_to, airline, flight_number, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    departure["Scheduled Time"],
                    departure["Estimated Time"],
                    departure["Departs To"],
                    departure["Airline"],
                    departure["Flight Number"],
                    departure["Status"],
                ))
                print(f"Added new flight: {departure['Flight Number']} (Scheduled: {departure['Scheduled Time']})")
        conn.commit()


def main():
    db_file_path = r"C:\Users\zabit\Documents\GitHub\planespotting-time-finder\second_version\departures.db"

    # Infinite loop to run the script indefinitely
    while True:
        # Process all pages from 1 to 10
        for page in range(1, 11):
            print(f"Processing page {page}...")
            html_snippet = get_clean_html(page)
            if html_snippet:
                departures_data = extract_departure_data(html_snippet)
                save_to_database(departures_data, db_file_path)
            time.sleep(30)  # Delay between pages (e.g., 30 seconds)

        # Add a delay after processing all pages (e.g., 15 minutes) to avoid overwhelming the server
        print("Waiting for 15 minutes before the next run...")
        time.sleep(900)  # Wait for 15 minutes (900 seconds) before the next cycle


if __name__ == "__main__":
    main()

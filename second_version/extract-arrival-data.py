import sqlite3
from bs4 import BeautifulSoup

# Load the HTML content from the file
file_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/second_version/arrival_schedule_cleaned.html'

with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Initialize a list to hold arrival data
arrivals_data = []

# Find all rows in the arrivals table
arrival_rows = soup.select('tbody.dumb-pager-items tr')

for row in arrival_rows:
    # Extracting the main information from the row
    time = row.select_one('td[data-label="Time"] span.light-sm').text.strip()
    
    # Extract estimated time (including date)
    estimated_time_span = row.select_one('td[data-label="Estimated time"] span.bold-lg')
    estimated_date_span = row.select_one('td[data-label="Estimated time"] span.light-sm')
    estimated_time = f"{estimated_date_span.text.strip()} {estimated_time_span.text.strip()}" if estimated_time_span and estimated_date_span else None

    arrives_from = row.select_one('td[data-label="Arrives from"] span.bold-lg').text.strip()
    arrives_from_airline = row.select_one('td[data-label="Arrives from"] span.light-sm').text.strip()
    flight_number = row.select_one('td[data-label="Flight number"] a.bold-lg').text.strip()
    
    # Get more details from the modal
    modal_id = row['data-target'].replace('#', '')  # Get the modal id
    modal = soup.find('div', id=modal_id)
    
    if modal:
        # Extracting information directly from the modal using string
        departs_to = modal.find('span', string="Departs to:").find_next_sibling('span').text.strip() if modal.find('span', string="Departs to:") else None
        arrival_time = modal.find('span', string="Arrival Time:").find_next_sibling('span').text.strip() if modal.find('span', string="Arrival Time:") else None
        scheduled_date = f"{time} {arrival_time}" if time and arrival_time else None
        landed = modal.find('span', string="Landed:").find_next_sibling('span').text.strip() if modal.find('span', string="Landed:") else None
        status = modal.find('span', string="Status:").find_next_sibling('span').text.strip() if modal.find('span', string="Status:") else None
        
        # If the status is "On Time", set estimated_time to scheduled_date
        if status == "On time" or not status:
            estimated_time = scheduled_date
        
        # Collect the data in a dictionary
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

# Save the data into a SQLite database
db_file_path = r"C:\Users\zabit\Documents\GitHub\planespotting-time-finder\second_version\arrivals.db"

# Create a SQLite database and a table
with sqlite3.connect(db_file_path) as conn:
    cursor = conn.cursor()
    
    # Create a table for flight arrivals if it doesn't exist
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

    # Insert or update the arrival data into the database
    for arrival in arrivals_data:
        # Check if a record with the same scheduled_time, arrives_from, airline, flight_number, departs_to exists
        cursor.execute('''
            SELECT * FROM arrivals
            WHERE scheduled_date = ? AND arrives_from = ? AND airline = ? AND flight_number = ? AND departs_to = ?
        ''', (arrival["Scheduled Time"], arrival["Arrives From"], arrival["Airline"], arrival["Flight Number"], arrival["Departs To"]))
        
        existing_arrival = cursor.fetchone()
        
        if existing_arrival:
            # Compare existing data with new data and track changes
            updates = []
            if existing_arrival[2] != arrival["Estimated Time"]:
                updates.append(f"Estimated Time: {existing_arrival[2]} -> {arrival['Estimated Time']}")
            if existing_arrival[7] != arrival["Landed"]:
                updates.append(f"Landed: {existing_arrival[7]} -> {arrival['Landed']}")
            if existing_arrival[8] != arrival["Status"]:
                updates.append(f"Status: {existing_arrival[8]} -> {arrival['Status']}")

            # If there are changes, update the existing record and print the updates
            if updates:
                cursor.execute('''
                    UPDATE arrivals
                    SET estimated_time = ?, landed = ?, status = ?
                    WHERE id = ?
                ''', (arrival["Estimated Time"], arrival["Landed"], arrival["Status"], existing_arrival[0]))

                print(f"Flight {arrival['Flight Number']} (Scheduled: {arrival['Scheduled Time']}): Updated fields -> {', '.join(updates)}")
        else:
            # Insert new arrival
            cursor.execute('''
                INSERT INTO arrivals (
                    scheduled_date,
                    estimated_time,
                    arrives_from,
                    airline,
                    flight_number,
                    departs_to,
                    landed,
                    status
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

    # Commit the changes to the database
    conn.commit()

print(f"Data saved to {db_file_path}")

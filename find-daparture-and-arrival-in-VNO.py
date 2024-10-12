import json
import sqlite3
from datetime import datetime, timezone
import time

# Load the JSON files for arrivals and departures
arrivals_file_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/airport_arrivals.json'
departures_file_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/airport_departures.json'

# Connect to SQLite database and save it in the specified folder
db_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/vilnius_airport.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create a table for storing flight data if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_type TEXT,
    airline TEXT,
    aircraft_model TEXT,
    registration TEXT,
    origin_or_destination TEXT,
    scheduled_time TEXT,
    estimated_time TEXT,
    actual_time TEXT,
    status_live TEXT,
    status_text TEXT,
    status_icon TEXT,
    last_update_time TEXT,
    data_input_time TEXT
)''')

# Function to check if a flight exists and if status fields need updating
def check_and_update_flight(flight_type, flight):
    try:
        airline = flight['flight']['airline']['name']
    except:
        airline = ''
    aircraft_model = flight['flight']['aircraft']['model']['text']
    registration = flight['flight']['aircraft']['registration']
    origin_or_destination = flight['flight']['airport']['origin']['name'] if flight_type == 'arrival' else flight['flight']['airport']['destination']['name']

    # Scheduled and estimated times
    scheduled_time = datetime.fromtimestamp(
        flight['flight']['time']['scheduled']['arrival'] if flight_type == 'arrival' else flight['flight']['time']['scheduled']['departure'],
        tz=timezone.utc
    ).strftime('%Y-%m-%d %H:%M:%S')

    estimated_time = (datetime.fromtimestamp(
        flight['flight']['time']['estimated']['arrival'] if flight_type == 'arrival' else flight['flight']['time']['estimated']['departure'],
        tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') 
        if flight['flight']['time']['estimated'] and
           (flight['flight']['time']['estimated'].get('arrival') if flight_type == 'arrival' else flight['flight']['time']['estimated'].get('departure')) is not None
        else None)

    # Actual time
    real_time_key = 'arrival' if flight_type == 'arrival' else 'departure'
    actual_time = (datetime.fromtimestamp(flight['flight']['time']['real'][real_time_key], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                   if flight['flight']['time']['real'][real_time_key] else None)

    # Extract status fields
    status_live = str(flight['flight']['status']['live'])
    status_text = flight['flight']['status']['text']
    status_icon = flight['flight']['status']['icon']

    # Last update time
    last_update_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # Check if the flight exists based on airline, origin_or_destination, and scheduled_time
    cursor.execute('''SELECT actual_time, status_live, status_text, status_icon 
                      FROM flights WHERE airline=? AND origin_or_destination=? AND scheduled_time=? AND flight_type=?''',
                   (airline, origin_or_destination, scheduled_time, flight_type))
    existing_flight = cursor.fetchone()

    if existing_flight:
        # Flight exists, check if it needs to be updated
        if (existing_flight[0] != actual_time or
                existing_flight[1] != status_live or
                existing_flight[2] != status_text or
                existing_flight[3] != status_icon):
            # Update the flight
            cursor.execute('''UPDATE flights
                              SET estimated_time=?, actual_time=?, status_live=?, status_text=?, status_icon=?, last_update_time=?
                              WHERE airline=? AND origin_or_destination=? AND scheduled_time=? AND flight_type=?''',
                           (estimated_time, actual_time, status_live, status_text, status_icon, last_update_time,
                            airline, origin_or_destination, scheduled_time, flight_type))
            return 'updated', {
                'flight_type': flight_type,
                'airline': airline,
                'scheduled_time': scheduled_time,
                'actual_time': actual_time,
                'status_live': status_live,
                'status_text': status_text,
                'status_icon': status_icon
            }
        else:
            return 'unchanged', None
    else:
        # Insert new flight
        cursor.execute('''INSERT INTO flights (flight_type, airline, aircraft_model, registration, origin_or_destination, scheduled_time, estimated_time, actual_time, status_live, status_text, status_icon, last_update_time, data_input_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (flight_type, airline, aircraft_model, registration, origin_or_destination, scheduled_time, estimated_time, actual_time, status_live, status_text, status_icon,
                        last_update_time, last_update_time))
        return 'added', {
            'flight_type': flight_type,
            'airline': airline,
            'scheduled_time': scheduled_time,
            'actual_time': actual_time,
            'status_live': status_live,
            'status_text': status_text,
            'status_icon': status_icon
        }

# Function to load and process flights
def process_flights():
    # Lists to track added and updated flights
    added_flights = []
    updated_flights = []

    # Load and process arrivals data
    with open(arrivals_file_path, 'r', encoding='utf-8') as arrivals_file:
        arrivals_data = json.load(arrivals_file)
        arrivals_flights = arrivals_data['result']['response']['airport']['pluginData']['schedule']['arrivals']['data']
        for flight in arrivals_flights:
            result, flight_info = check_and_update_flight('arrival', flight)
            if result == 'added':
                added_flights.append(flight_info)
            elif result == 'updated':
                updated_flights.append(flight_info)

    # Load and process departures data
    with open(departures_file_path, 'r', encoding='utf-8') as departures_file:
        departures_data = json.load(departures_file)
        departures_flights = departures_data['result']['response']['airport']['pluginData']['schedule']['departures']['data']
        for flight in departures_flights:
            result, flight_info = check_and_update_flight('departure', flight)
            if result == 'added':
                added_flights.append(flight_info)
            elif result == 'updated':
                updated_flights.append(flight_info)

    # Commit the transaction
    conn.commit()

    # Output the results
    print(f"New flights added: {len(added_flights)}, Flights updated: {len(updated_flights)}")

    # Print added flights
    if added_flights:
        print("\nAdded Flights:")
        for flight in added_flights:
            print(f" - {flight['flight_type'].capitalize()} by {flight['airline']} at {flight['scheduled_time']} (Status: {flight['status_text']})")

    # Print updated flights
    if updated_flights:
        print("\nUpdated Flights:")
        for flight in updated_flights:
            print(f" - {flight['flight_type'].capitalize()} by {flight['airline']} at {flight['scheduled_time']} (Status: {flight['status_text']})")

# Run the process every 5 seconds
while True:
    process_flights()
    time.sleep(30)

# Close the connection to the database (this won't be reached due to the infinite loop, but is added for completeness)
conn.close()

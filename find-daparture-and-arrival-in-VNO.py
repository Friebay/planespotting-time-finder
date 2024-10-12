import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from tabulate import tabulate
import time

# File paths for JSON data
arrivals_file_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/airport_arrivals.json'
departures_file_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/airport_departures.json'

# SQLite database connection
db_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/vilnius_airport.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create flights table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_type TEXT,
        scheduled_time TEXT,
        scheduled_time_other TEXT,
        estimated_time TEXT,
        estimated_time_other TEXT,
        actual_time TEXT,
        actual_time_other TEXT,
        status_live TEXT,
        status_text TEXT,
        status_icon TEXT,
        airline TEXT,
        aircraft_model TEXT,
        registration TEXT,
        callsign TEXT,
        model_code TEXT,
        country TEXT,
        restricted TEXT,
        owner_name TEXT,
        origin_or_destination TEXT,
        last_update_time TEXT,
        data_input_time TEXT
    )
''')

# Function to extract flight data
def extract_flight_info(flight_type, flight):
    try:
        airline = flight.get('flight', {}).get('airline', {}).get('name', '')
    except:
        airline = ''
    aircraft = flight['flight']['aircraft']
    owner = flight['flight']
    
    aircraft_model = aircraft['model']['text']
    model_code = aircraft['model']['code']
    registration = aircraft['registration']
    callsign = flight['flight']['identification']['callsign']
    try:
        country = aircraft['country']['name']
    except:
        country = ''
    try:
        restricted = str(aircraft['restricted'])
    except:
        restricted = ''
    try:
        owner_name = owner['owner']['name']
    except:
        owner_name = ''
    
    if flight_type == 'arrival':
        origin_or_destination = flight['flight']['airport']['origin']['name']
        scheduled_time = flight['flight']['time']['scheduled']['arrival']
        scheduled_time_other = flight['flight']['time']['scheduled']['departure']
        estimated_time = flight['flight']['time'].get('estimated', {}).get('arrival')
        estimated_time_other = flight['flight']['time'].get('estimated', {}).get('departure')
        actual_time = flight['flight']['time']['real'].get('arrival')
        actual_time_other = flight['flight']['time']['real'].get('departure')
    else:
        origin_or_destination = flight['flight']['airport']['destination']['name']
        scheduled_time = flight['flight']['time']['scheduled']['departure']
        scheduled_time_other = flight['flight']['time']['scheduled']['arrival']
        estimated_time = flight['flight']['time'].get('estimated', {}).get('departure')
        estimated_time_other = flight['flight']['time'].get('estimated', {}).get('arrival')
        actual_time = flight['flight']['time']['real'].get('departure')
        actual_time_other = flight['flight']['time']['real'].get('arrival')

    def format_time(timestamp):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if timestamp else None

    return {
        'airline': airline,
        'aircraft_model': aircraft_model,
        'model_code': model_code,
        'registration': registration,
        'callsign': callsign,
        'country': country,
        'restricted': restricted,
        'owner_name': owner_name,
        'origin_or_destination': origin_or_destination,
        'scheduled_time': format_time(scheduled_time),
        'scheduled_time_other': format_time(scheduled_time_other),
        'estimated_time': format_time(estimated_time),
        'estimated_time_other': format_time(estimated_time_other),
        'actual_time': format_time(actual_time),
        'actual_time_other': format_time(actual_time_other),
        'status_live': str(flight['flight']['status']['live']),
        'status_text': flight['flight']['status']['text'],
        'status_icon': flight['flight']['status']['icon'],
        'last_update_time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

# Function to check and update flight in the database
def check_and_update_flight(flight_type, flight):
    flight_info = extract_flight_info(flight_type, flight)

    cursor.execute('''SELECT actual_time, status_live, status_text, status_icon 
                      FROM flights WHERE airline=? AND origin_or_destination=? AND scheduled_time=? AND flight_type=?''',
                   (flight_info['airline'], flight_info['origin_or_destination'], flight_info['scheduled_time'], flight_type))
    existing_flight = cursor.fetchone()

    if existing_flight:
        if (existing_flight[0] != flight_info['actual_time'] or 
            existing_flight[1] != flight_info['status_live'] or 
            existing_flight[2] != flight_info['status_text'] or 
            existing_flight[3] != flight_info['status_icon']):
            cursor.execute('''UPDATE flights
                              SET estimated_time=?, actual_time=?, status_live=?, status_text=?, status_icon=?, last_update_time=?,
                                  scheduled_time_other=?, estimated_time_other=?, actual_time_other=?, callsign=?, model_code=?, country=?, restricted=?, owner_name=?
                              WHERE airline=? AND origin_or_destination=? AND scheduled_time=? AND flight_type=?''',
                           (flight_info['estimated_time'], flight_info['actual_time'], flight_info['status_live'], 
                            flight_info['status_text'], flight_info['status_icon'], flight_info['last_update_time'],
                            flight_info['scheduled_time_other'], flight_info['estimated_time_other'], flight_info['actual_time_other'],
                            flight_info['callsign'], flight_info['model_code'], flight_info['country'], flight_info['restricted'], 
                            flight_info['owner_name'], flight_info['airline'], flight_info['origin_or_destination'], 
                            flight_info['scheduled_time'], flight_type))
            return 'updated', flight_info
        else:
            return 'unchanged', None
    else:
        cursor.execute('''INSERT INTO flights 
                          (flight_type, airline, aircraft_model, registration, callsign, model_code, country, restricted, owner_name,
                           origin_or_destination, scheduled_time, scheduled_time_other, estimated_time, estimated_time_other, 
                           actual_time, actual_time_other, status_live, status_text, status_icon, last_update_time, data_input_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (flight_type, flight_info['airline'], flight_info['aircraft_model'], flight_info['registration'], 
                        flight_info['callsign'], flight_info['model_code'], flight_info['country'], flight_info['restricted'], 
                        flight_info['owner_name'], flight_info['origin_or_destination'], flight_info['scheduled_time'], 
                        flight_info['scheduled_time_other'], flight_info['estimated_time'], flight_info['estimated_time_other'], 
                        flight_info['actual_time'], flight_info['actual_time_other'], flight_info['status_live'], 
                        flight_info['status_text'], flight_info['status_icon'], flight_info['last_update_time'], 
                        flight_info['last_update_time']))
        return 'added', flight_info

# Function to load and process flights from JSON files
def process_flights():
    added_flights = []
    updated_flights = []

    with open(arrivals_file_path, 'r', encoding='utf-8') as arrivals_file:
        arrivals_data = json.load(arrivals_file)['result']['response']['airport']['pluginData']['schedule']['arrivals']['data']
        for flight in arrivals_data:
            result, flight_info = check_and_update_flight('arrival', flight)
            if result == 'added':
                added_flights.append(flight_info)
            elif result == 'updated':
                updated_flights.append(flight_info)

    with open(departures_file_path, 'r', encoding='utf-8') as departures_file:
        departures_data = json.load(departures_file)['result']['response']['airport']['pluginData']['schedule']['departures']['data']
        for flight in departures_data:
            result, flight_info = check_and_update_flight('departure', flight)
            if result == 'added':
                added_flights.append(flight_info)
            elif result == 'updated':
                updated_flights.append(flight_info)

    conn.commit()

    # Print updated and added flights in a table
    if added_flights or updated_flights:
        changed_flights = pd.DataFrame(added_flights + updated_flights)

        # Put the fixed code here:
        if not changed_flights.empty:
            available_columns = changed_flights.columns
            columns_to_display = ['flight_type', 'callsign', 'origin_or_destination', 'scheduled_time', 'estimated_time']
            columns_to_display = [col for col in columns_to_display if col in available_columns]

            table = tabulate(changed_flights[columns_to_display],
                             headers='keys', tablefmt='grid', showindex=False)
            print(f"\nFlights added: {len(added_flights)}, Flights updated: {len(updated_flights)}")
            print(table)
        else:
            print("No flights were added or updated.")

# Main loop: process flights every 30 seconds
while True:
    process_flights()
    time.sleep(30)

# Close the database connection (unreachable in this infinite loop)
conn.close()

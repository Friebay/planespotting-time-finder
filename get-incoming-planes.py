import sqlite3
import pandas as pd
from datetime import datetime
from tabulate import tabulate  # Install using: pip install tabulate

# Connect to the SQLite database
db_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/vilnius_airport.db'
conn = sqlite3.connect(db_path)

# Query the database to get scheduled times for arrivals and departures, including airline and origin/destination
query = '''
SELECT flight_type, airline, origin_or_destination, scheduled_time, estimated_time, callsign
FROM flights
'''
df = pd.read_sql_query(query, conn)

# Convert scheduled_time and estimated_time columns to datetime
df['scheduled_time'] = pd.to_datetime(df['scheduled_time'])
df['estimated_time'] = pd.to_datetime(df['estimated_time'])

# Add 3 hours to each scheduled time (to account for UTC+3)
df['scheduled_time'] = df['scheduled_time'] + pd.Timedelta(hours=3)
df['estimated_time'] = df['estimated_time'] + pd.Timedelta(hours=3)

# Get the current time
current_time = datetime.now()

# Filter the data to get only upcoming flights and sort by scheduled_time
upcoming_flights = df[df['scheduled_time'] > current_time].sort_values(by='scheduled_time')

# Get the 10 most recent upcoming flights
next_flights = upcoming_flights.head(10)

# Format the data using tabulate for clean table output
table = tabulate(next_flights[['flight_type', 'callsign', 'origin_or_destination', 'scheduled_time', 'estimated_time']],
                 headers='keys', tablefmt='grid', showindex=False)

# Print the results as a table
print(table)

import os
os.system('pause')

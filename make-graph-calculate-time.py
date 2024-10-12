import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from tabulate import tabulate

# Connect to the SQLite database
db_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/vilnius_airport.db'
conn = sqlite3.connect(db_path)

# Query the database to get scheduled times for arrivals and departures, including airline and origin/destination
query = '''
SELECT flight_type, origin_or_destination, scheduled_time, estimated_time, callsign
FROM flights
'''
df = pd.read_sql_query(query, conn)

# Convert scheduled_time to datetime and adjust to UTC+3
df['scheduled_time'] = pd.to_datetime(df['scheduled_time']) + timedelta(hours=3)
df['estimated_time'] = pd.to_datetime(df['estimated_time']) + timedelta(hours=3)

# Filter for future flights only
current_time = datetime.now()  # Adjust current time to UTC+3
df = df[df['scheduled_time'] > current_time]

# Check if there are any future flights
if df.empty:
    print("No future flights available.")
else:
    # Get user input for the time window in minutes
    time_window = int(input("Enter the time window (in minutes) to check for flights: "))

    # Validate user input
    if time_window <= 0:
        raise ValueError("Time window must be a positive integer.")

    # Initialize variables to track the best time and maximum flights
    max_flights = 0
    best_time = None

    # Loop through each scheduled time to calculate the number of flights in the specified time window
    for index, row in df.iterrows():
        start_time = row['scheduled_time']
        end_time = start_time + timedelta(minutes=time_window)

        # Count the number of flights scheduled in the next time window
        flight_count = df[(df['scheduled_time'] >= start_time) & (df['scheduled_time'] < end_time)].shape[0]

        # Check if this count is the highest found so far
        if flight_count > max_flights:
            max_flights = flight_count
            best_time = start_time

    # Display the result
    if best_time:
        # Print out the times of flights in the best time window
        highlight_start = best_time
        highlight_end = best_time + timedelta(minutes=time_window)  # User-defined time window
        flights_in_window = df[(df['scheduled_time'] >= highlight_start) & (df['scheduled_time'] < highlight_end)]

        # Sort flights by scheduled_time
        flights_in_window = flights_in_window.sort_values(by='scheduled_time')

        # Print in a table format
        print("\nFlights arriving and departing during the best time window:")
        print(tabulate(flights_in_window[['flight_type', 'callsign', 'origin_or_destination', 'scheduled_time', 'estimated_time']], 
                        headers='keys', 
                        tablefmt='grid', 
                        showindex=False, 
                        numalign='center'))

        print(f"The best time to arrive at the airport is: {best_time.strftime('%Y-%m-%d %H:%M:%S')} "
              f"with approximately {max_flights} flights expected in the next {time_window} minutes.")

        # Create a new DataFrame to count flights by time intervals
        df.set_index('scheduled_time', inplace=True)
        flight_counts = df.resample('10T').size()  # Count flights every 10 minutes

        # Plot the data
        plt.figure(figsize=(14, 7))
        flight_counts.plot(kind='bar', color='skyblue', edgecolor='black')

        # Highlight the best time window
        best_window_start = best_time.floor('T')  # Round down to the nearest minute
        best_window_end = best_window_start + timedelta(minutes=time_window)

        # Convert the best_window_start and best_window_end to the appropriate indices for the bar plot
        bar_start_index = int((best_window_start - flight_counts.index[0]).total_seconds() / 600)  # 600 seconds = 10 minutes
        bar_end_index = int((best_window_end - flight_counts.index[0]).total_seconds() / 600)  # 600 seconds = 10 minutes

        plt.axvspan(bar_start_index, bar_end_index, color='orange', alpha=0.5, label='Best Time Window')

        # Formatting the plot
        plt.title('Number of Flights Over Time')
        plt.xlabel('Scheduled Time')
        plt.ylabel('Number of Flights')

        # Limit the number of x-ticks
        total_ticks = len(flight_counts)
        plt.xticks(ticks=range(0, total_ticks, max(1, total_ticks // 20)),  # Show 5% of the ticks
                   labels=flight_counts.index[::max(1, total_ticks // 20)].strftime('%Y-%m-%d %H:%M:%S'), 
                   rotation=45)

        plt.legend()
        plt.grid(axis='y')
        plt.tight_layout()

        # Show the plot
        plt.show()

    else:
        print("No flights found.")

# Close the database connection
conn.close()

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Connect to the SQLite database
db_path = 'C:/Users/zabit/Documents/GitHub/planespotting-time-finder/vilnius_airport.db'
conn = sqlite3.connect(db_path)

# Query the database to get scheduled times for arrivals and departures
query = '''
SELECT flight_type, scheduled_time 
FROM flights
'''
df = pd.read_sql_query(query, conn)

# Convert scheduled_time to datetime
df['scheduled_time'] = pd.to_datetime(df['scheduled_time'])

# Set the scheduled_time as the index
df.set_index('scheduled_time', inplace=True)

# User input for minute detail
minute_detail = int(input("Enter the minute detail for the graph (e.g., 1 for 1 minute, 5 for 5 minutes): "))

# Ensure that the input is valid
if minute_detail <= 0:
    raise ValueError("Minute detail must be a positive integer.")

# Create the frequency string for Pandas
frequency = f'{minute_detail}T'  # 'T' denotes minutes

# Count the total number of flights per specified minute detail
count_df = df.groupby(pd.Grouper(freq=frequency)).size()

# Calculate the total number of flights in a 60-minute period
rolling_counts = count_df.rolling(window='60T').sum()

# Find the time with the maximum number of flights in that 60-minute window
max_flights = rolling_counts.max()
best_time = rolling_counts.idxmax()

# Display the result
print(f"The best time to arrive at the airport is: {best_time.strftime('%Y-%m-%d %H:%M:%S')} with approximately {max_flights} flights expected in the next 60 minutes.")

# Filter for flights arriving/departing during the best time window
highlight_start = best_time
highlight_end = best_time + pd.Timedelta(hours=1)  # 60-minute period
flights_in_window = df[(df.index >= highlight_start) & (df.index < highlight_end)]

# Print out the times of flights in the best time window
if not flights_in_window.empty:
    print("\nFlights arriving and departing during the best time window:")
    for idx, row in flights_in_window.iterrows():
        print(f" - {row['flight_type'].capitalize()} at {idx.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print("\nNo flights are scheduled during this time window.")

# Calculate the number of unique flights in the best time window
expected_flights = len(flights_in_window)
print(f"\nTotal expected flights in the next 60 minutes: {expected_flights}")

# Plotting
plt.figure(figsize=(15, 8))
count_df.plot(kind='line', linestyle='-', marker='o', color='b', label='Flights per Interval')  # Use a single color for the line
plt.title(f'Total Flights (Arrivals + Departures) at Vilnius Airport - {minute_detail}-Minute Detail')
plt.xlabel('Time')
plt.ylabel('Number of Flights')
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.grid(axis='both', linestyle='--')

# Highlight the best time period
plt.axvspan(highlight_start, highlight_end, color='orange', alpha=0.3, label='Best Arrival Time Window')

plt.legend()
plt.tight_layout()
plt.show()

# Close the database connection
conn.close()

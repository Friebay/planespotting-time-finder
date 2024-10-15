import sqlite3
from datetime import datetime
from prettytable import PrettyTable

# Function to retrieve 10 upcoming arrivals and print in a table
def get_upcoming_arrivals(db_file_path):
    # Connect to the database
    with sqlite3.connect(db_file_path) as conn:
        cursor = conn.cursor()

        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Query to fetch the 10 upcoming arrivals based on the current time
        cursor.execute('''
            SELECT scheduled_date, estimated_time, arrives_from, airline, flight_number, status
            FROM arrivals
            WHERE estimated_time > ?
            ORDER BY estimated_time
            LIMIT 10
        ''', (current_time,))

        # Fetch the results
        upcoming_arrivals = cursor.fetchall()

        # Check if there are upcoming arrivals
        if upcoming_arrivals:
            # Initialize the table
            table = PrettyTable()
            table.field_names = ["#", "Flight", "From", "Airline", "Scheduled", "Estimated", "Status"]

            # Add rows to the table
            for i, arrival in enumerate(upcoming_arrivals, 1):
                scheduled_date, estimated_time, arrives_from, airline, flight_number, status = arrival
                table.add_row([i, flight_number, arrives_from, airline, scheduled_date, estimated_time, status])

            # Print the table
            print(f"\n10 Upcoming Arrivals after {current_time}:")
            print(table)
        else:
            print(f"No upcoming arrivals found after {current_time}.")

# Main function
def main():
    db_file_path = r"C:\Users\zabit\Documents\GitHub\planespotting-time-finder\second_version\arrivals.db"
    get_upcoming_arrivals(db_file_path)

if __name__ == "__main__":
    main()

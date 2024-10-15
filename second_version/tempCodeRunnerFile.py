# Function to parse the departures data
def extract_departure_data(html_snippet):
    soup = BeautifulSoup(html_snippet, 'html.parser')
    departures_data = []

    departure_rows = soup.select('tbody.dumb-pager-items tr')
    for row in departure_rows:
        # Extract the time and date
        time = row.select_one('td[data-label="Time"] span.bold-lg').text.strip()
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
            departures_data.append(departure_info)

    return departures_data
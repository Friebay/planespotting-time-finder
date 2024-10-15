import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

# URL of the page
page = 4

url = f"https://www.vilnius-airport.lt/en/before-the-flight/flights-information/flights-schedule?direction=arrival&destination=&date-from=2024-10-13&date-to=&page={page}"

print(url)

# Initialize a user agent to mimic Firefox browser
ua = UserAgent()
headers = {
    'User-Agent': ua.firefox  # Random Firefox user agent
}

# Send an HTTP GET request to fetch the page
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove all <del> tags
    for del_tag in soup.find_all('del'):
        del_tag.decompose()  # Completely removes the tag and its contents

    # Split the modified HTML content into lines
    lines = str(soup).splitlines()

    # Find start and end line numbers
    start_line = 1000+74
    end_line = None
    for i, line in enumerate(lines):
        if '<nav aria-label="navigation" class="text-center">' in line:
            end_line = i
            break

    # Extract the desired HTML portion and clean up each line
    cleaned_html_lines = []
    for line in lines[start_line:end_line]:
        cleaned_line = line.lstrip()  # Remove leading whitespaces
        cleaned_html_lines.append(cleaned_line)

    # Join the cleaned lines into the final HTML snippet
    html_snippet = '\n'.join(cleaned_html_lines)

    # Define the output file path
    output_file_path = r"C:\Users\zabit\Documents\GitHub\planespotting-time-finder\second_version\arrival_schedule_cleaned.html"

    # Save the cleaned HTML snippet to a file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(html_snippet)

    print(f"Cleaned HTML content saved to {output_file_path}")

else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

import time
import aiohttp
from bs4 import BeautifulSoup
import discord
from dotenv import dotenv_values
import asyncio
from datetime import datetime
import os
import json
import re


# Load configuration from .env file
config = dotenv_values(".env")

# URL to scrape for course information
course_schedule_url = "https://web.csulb.edu/depts/enrollment/registration/class_schedule/Spring_2024/By_Subject/"
room_bookings = []

WEEKDAY_ABBR = {
    0: "M",
    1: "Tu",
    2: "W",
    3: "Th",
    4: "F",
    5: "Sa",
    6: "Su"
}

def parse_sections_table(table):
    """
    Parses the HTML table of course sections and returns detailed information.

    Args:
        table (Tag): The BeautifulSoup object of the HTML table to be parsed.

    Returns:
        list[dict]: List of dictionaries containing section details.
    """
    sections = []
    headers = [th.text.strip() for th in table.find_all('th', scope='col')]
    
    for row in table.find_all('tr')[1:]:  # Skipping the header row
        cells = row.find_all(['th', 'td'])
        section_info = {headers[i]: cells[i].get_text(strip=True) for i in range(len(cells))}
        sections.append(section_info)

    formatted = []
    for section in sections:

        start_time, end_time = parse_times(section['TIME'])

        for day in parse_days(section['DAYS']):
            formatted_section = {
                "Location": section['LOCATION'],
                "Day": day,
                "Start": start_time,
                "End": end_time
            }

        formatted.append(formatted_section)

    return formatted

def parse_times(time_str):
    # Handle 'TBA' or 'NA' cases upfront
    if time_str == 'TBA' or time_str == 'NA':
        return (0, 0)

    # Split the time range into start and end times
    start_time_str, end_time_str = time_str.split('-')

    # Determine if AM/PM is specified for the end time and apply to start time if necessary
    if 'am' in end_time_str.lower() and 'am' not in start_time_str.lower() and 'pm' not in start_time_str.lower():
        start_time_str += 'am'
    elif 'pm' in end_time_str.lower() and 'pm' not in start_time_str.lower() and 'am' not in start_time_str.lower():
        start_time_str += 'pm'

    # Define a helper function to convert time to 24-hour format
    def time_to_24h(t_str):
        t_str = t_str.lower()
        is_pm = 'pm' in t_str
        t_str = t_str.replace('am', '').replace('pm', '')

        if ':' in t_str:
            hours, minutes = t_str.split(':')
        else:
            hours, minutes = t_str, '00'

        hours, minutes = int(hours), int(minutes)

        if is_pm and hours < 12:
            hours += 12
        elif not is_pm and hours == 12:
            hours = 0

        return (hours * 100) + minutes

    # Convert start and end times to 24-hour format
    start_time = time_to_24h(start_time_str)
    end_time = time_to_24h(end_time_str)

    return (start_time, end_time)

def parse_days(days_str):
    # split string by capital letters
    return [day for day in re.findall('[A-Z][^A-Z]*', days_str)]

async def get_page_html(url):
    """
    Asynchronously fetches course sections from a specified URL and processes the data.

    Args:
        url (str): The URL to scrape.
        course_title (str): The title of the course to look for.

    Returns:
        A list of section information if successful, an empty list otherwise.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                # Log failure
                print("Failed to retrieve the web page.")
                return []

            soup = BeautifulSoup(await response.text(), 'html.parser')
    return soup

def get_subjects(html):

    toplink_divs = html.find_all('div', class_='indexList')

    hrefs = []
    # Iterate over each 'toplink' div
    for div in toplink_divs:
        # Find all <a> tags within the div
        links = div.find_all('a')
        # Extract the href attribute from each link and add it to the list
        for link in links:
            if link.get('href') != None and link.get('href') != "#":
                hrefs.append(link.get('href'))

    return hrefs

class Room:
    def __init__(self, location, booked_times=None):
        self.location = location
        # Ensure booked_times is a list of tuples, each tuple containing (day, (start, end))
        self.booked_times = booked_times if booked_times is not None else []

    def add_booked_time(self, day, time_tuple):
        # Now each booked_time is a tuple of (day, (start, end))
        self.booked_times.append((day, time_tuple))

    def is_open(self, day, current_time):
        for booked_day, (start, end) in self.booked_times:
            if day == booked_day:
                if start <= current_time <= end:
                    return False
        return True
    
    def __str__(self):
        return self.location
    
def get_rooms(html):
    courses = html.find_all(lambda tag: tag.name == "div" and tag.get("class", []) == ["courseHeader"])
    for course_header in courses:
        if course_header:
            sections_table = course_header.find_next_sibling('table')
            if sections_table:
                sections = parse_sections_table(sections_table)
                for section in sections:
                    # check if room is already in rooms
                    for room in room_bookings:
                        if room.location == section['Location']:
                            room.add_booked_time(section['Day'], (section['Start'], section['End']))
                            break
                    else:
                        room = Room(section['Location'], [(section['Day'], (section['Start'], section['End']))])
                        room_bookings.append(room)
            
    
async def main(filter = None):
    rooms_data_file = "rooms_data.json"  # Name of the file to check/save to
    
    # Check if the rooms data file exists
    if not os.path.exists(rooms_data_file):
        print("Scraping rooms because no saved data file found...")
        subjects_page = await get_page_html(course_schedule_url)
        subjects = get_subjects(subjects_page)
        for subject in subjects:
            course_list = await get_page_html(course_schedule_url + subject)
            get_rooms(course_list)
        
        # Save rooms data to file
        with open(rooms_data_file, 'w') as file:
            # Convert the rooms list of Room objects to a list of dicts for JSON serialization
            rooms_dicts = [{'location': room.location, 'booked_times': room.booked_times} for room in room_bookings]
            json.dump(rooms_dicts, file)
    else:
        print("Loading rooms from saved data file...")
        # Load rooms data from file
        with open(rooms_data_file, 'r') as file:
            rooms_dicts = json.load(file)
            # Convert list of dicts back to list of Room objects
            room_bookings.clear()  # Ensure rooms list is empty before loading
            for room_dict in rooms_dicts:
                room = Room(room_dict['location'], room_dict['booked_times'])
                room_bookings.append(room)


    # get current time in 24 hour format
    current_time = int(time.strftime("%H%M"))
    current_day = WEEKDAY_ABBR[datetime.now().weekday()]


    print(f"Finding open rooms for {current_day} at {datetime.now().strftime('%-I:%M%p')}...")
    if filter:
        print(f"Filtering for locations containing '{filter.upper()}'...")
    open_rooms = []
    for room in room_bookings:
        if room.is_open(current_day, current_time):
            if filter:
                if filter.lower() in room.location.lower():
                    open_rooms.append(room)
            else:
                open_rooms.append(room)

    formatted_open_rooms = {}

    for room in open_rooms:
        # get the next time the room will be in use:
        last_start = 2400
        for day, (start, end) in room.booked_times:
            if start > current_time:
                if start < last_start:
                    last_start = start
        
        formatted_open_rooms[room.location] = last_start
        print(f"{room} until {datetime.strptime(str(last_start), '%H%M').strftime('%-I:%M%p').lower() if last_start != 2400 else 'the end of today'}")

    
    max_value = max(formatted_open_rooms.values())

    keys_with_max_value = [key for key, value in formatted_open_rooms.items() if value == max_value]

    print(f"Best rooms (until {datetime.strptime(str(max_value), '%H%M').strftime('%-I:%M%p').lower() if max_value != 2400 else 'the end of today'}): ", keys_with_max_value)
    

# Start the monitoring loop
asyncio.run(main('hc'))
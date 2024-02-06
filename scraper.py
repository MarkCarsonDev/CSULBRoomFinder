import time
import aiohttp
from bs4 import BeautifulSoup
import discord
from dotenv import dotenv_values
import asyncio

# Load configuration from .env file
config = dotenv_values(".env")

# Discord bot token and target user ID
TOKEN = config["DISCORD_TOKEN"]
TARGET_USER_ID = int(config["TARGET_USER_ID"])

# URL and course title for monitoring
url = "https://web.csulb.edu/depts/enrollment/registration/class_schedule/Spring_2024/By_Subject/CECS.html"
course_title = "COMPUTER SCI SENIOR PROJECT I"
# course_title = "INTRODUCTION TO CECS"
section_count = 0

# Initialize Discord bot with default intents
client = discord.Client(intents=discord.Intents.default())

async def send_message(user_id: int, message=None):
    """
    Sends a message to a specified user on Discord.

    Args:
        user_id (int): The Discord user ID to whom the message will be sent.
        message (str, optional): The content of the message. Defaults to a generic message.
    """
    user = await client.fetch_user(user_id)
    message = message or "This was an attempt to send an unspecified message."
    await user.send(message)

async def monitor_course_sections(url, course_title, section_count, check_interval=60):
    """
    Monitors the specified course sections at regular intervals.

    Args:
        url (str): The URL to scrape for course information.
        course_title (str): The title of the course to monitor.
        check_interval (int): Time interval in seconds between checks.
    """
    while True:
        sections = await fetch_course_sections(url, course_title)
        if section_count == 0:
            await send_message(TARGET_USER_ID, f"Monitoring {len(sections)} section(s) for {course_title}...")
        elif len(sections) > section_count:
            await send_message(TARGET_USER_ID, f"{len(sections) - section_count} new section(s) have been added for {course_title}!")

        section_count = len(sections)   
        await asyncio.sleep(check_interval)

def get_value_of_key_starting_with(dict_data, start_string):
    """
    Returns the value of the first key in the dictionary that starts with the given string.

    Args:
        dict_data (dict): The dictionary to search.
        start_string (str): The string to match the start of the key.
    
    Returns:
        The value of the matched key or None if no match is found.
    """
    for key in dict_data.keys():
        if key.startswith(start_string):
            return dict_data[key]
    return None

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
        open_seats_index = next((i for i, header in enumerate(headers) if "OPEN SEATS" in header.upper()), None)
        if open_seats_index is not None:
            open_seats_cell = cells[open_seats_index]
            dot_element = open_seats_cell.find(class_="dot")
            open_seats = 1 if dot_element else 0
        else:
            open_seats = 0  # Default value if header is not found

        formatted_section = {
            "Section": section['SEC.'],
            "Class Number": section['CLASS #'],
            "Instructor": section['INSTRUCTOR'],
            "Open Seats": open_seats,
        }

        formatted.append(formatted_section)

    return formatted

async def fetch_course_sections(url, course_title):
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

    course_header = soup.find(lambda tag: tag.name == "div" and tag.get("class", []) == ["courseHeader"] and course_title in tag.text)
    if course_header:
        sections_table = course_header.find_next_sibling('table')
        if sections_table:
            sections = parse_sections_table(sections_table)
            open_seats = 0
            for section in sections:
                open_seats += section["Open Seats"]
                if section["Open Seats"] > 0:
                    await send_message(TARGET_USER_ID, f'Open seat(s) for {course_title} -- {section["Section"]}\n> Course Number: `{section["Class Number"]}`\n> Instructor: {section["Instructor"]}\n[Schedule of Courses]({url})')
            if open_seats > 0:
                await send_message(TARGET_USER_ID, f"**------------^- __Updated {time.strftime('%H:%M:%S')} on {time.strftime('%A, %D')}__ -^------------**")
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"{open_seats} seats available for {course_title} (Updated {time.strftime('%H:%M')} on {time.strftime('%A, %D')})")
            await client.change_presence(status=discord.Status.online, activity=activity)
        else:
            # Log if no sections table found
            await send_message(TARGET_USER_ID, f"Error: No sections table found for '{course_title}'.")
    else:
        # Log if course title not found
        await send_message(TARGET_USER_ID, f"Error: Course with title '{course_title}' not found.")
    return sections

@client.event
async def on_ready():
    """
    Called when the bot is ready. Sets up the monitoring task.
    """
    print(f'{client.user} is now running')
    await send_message(TARGET_USER_ID, "Bot has been started.")
    asyncio.create_task(monitor_course_sections(url, course_title, section_count))

client.run(TOKEN)

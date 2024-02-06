# CSULB Enrollment Scraper

## Overview
CSULB Enrollment Scraper is a Python-based web scraper and Discord bot. This program automates the process of monitoring course availability at California State University, Long Beach (CSULB). When an open seat or a new section becomes available in a specified course, it notifies a user via Discord direct message and updates the bot's status through Discord's Activity API.

## Features
- **Course Section Monitoring**: Continuously monitors a specific course's sections at CSULB for open seats and new sections.
- **Discord Notifications**: Sends real-time notifications via Discord direct messages when changes in course availability are detected.
- **Activity Status Updates**: Utilizes Discord's Activity API to display the current monitoring status and updates.

## Requirements
- Python 3.8 or higher.
- Discord Bot Application Token (obtainable through the [Developer Portal](http://discord.com/developers/applications)).

## Setup and Installation
1. **Environment Setup**: Ensure Python 3.8 or higher is installed on your system.
2. **Install Required Libraries**: Run `pip install discord aiohttp bs4 python-dotenv` to install necessary dependencies.
3. **Discord Bot Token and User ID**: Create a Discord bot on the Discord Developer Portal to obtain a bot token. Identify the target user ID for notifications.
4. **Configuration File**: Create a `.env`


```DISCORD_TOKEN=<your_discord_bot_token>
TARGET_USER_ID=<target_discord_user_id>```

5. **Launch the Bot**: Run the script with Python to start the bot.

## Configuration
- **Target Course and URL**: Adjust the `url` and `course_title` in the script to target the specific CSULB course page and title.
- **Monitoring Frequency**: Set the `check_interval` (in seconds) to control how often the bot checks for updates.

## License
This project is released under the [MIT License](LICENSE), promoting open and reproducible software practices.

## How to Contribute
Contributions are highly encouraged and appreciated. To contribute:
- Fork the repository.
- Create a new branch for your features or fixes.
- Submit a pull request with a comprehensive description of changes.

For more information, refer to the [contribution guidelines](CONTRIBUTING.md).

## Acknowledgements
- The original scraper was created and designed by [uhohspaghettioo](https://github.com/uhohspaghettioo)
- Improvements and Discord bot functionality were implemented by [Mark Carson](https://github.com/MarkCarsonDev)

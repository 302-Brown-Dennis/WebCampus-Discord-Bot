from os import getenv, listdir
from dotenv import load_dotenv

import discord
from discord.ext import tasks, commands
import requests
from datetime import datetime
import pytz

from cogs.commands import Commands
import ApiUtil as au

import re

# Load environment variables
load_dotenv()
CANVAS_API_URL = getenv('CANVAS_API_URL')
CANVAS_API_TOKEN = getenv('CANVAS_API_TOKEN')
DISCORD_CHANNEL_ID = int(getenv("DISCORD_CHANNEL_ID", 0))
DISCORD_SERVER_ID = int(getenv("DISCORD_SERVER_ID", 0))
BOT_TOKEN = getenv('BOT_TOKEN')

# Set up the bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize sets to track seen items
seen_grades = set()
seen_messages = set()
seen_files = set()
seen_announcements = set()
bot.user_preferences = {}
# Event: When the bot joins a new server
@bot.event
async def on_guild_join(guild):
    # Find the default channel where the bot can send messages
    default_channel = next(
        (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
        None
    )
    if default_channel:
        help_message = (
            f"Hello, {guild.name}! 👋\n"
            "I'm your new bot!\n"
            "```\n"
            "Type !menu to get started!\n"
            "```\n"
        )
        await default_channel.send(help_message)

# Canvas API Helper Functions
def make_api_request(endpoint, params=None):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    response = requests.get(endpoint, headers=headers, params=params or {})
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching data from {endpoint}: {response.status_code}")
    return None

def fetch_graded_assignments(course_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/students/submissions"
    params = {"graded_since": "2023-01-01T00:00:00Z", "include[]": "submission_comments"}
    return make_api_request(endpoint, params)

def fetch_assignment_details(course_id, assignment_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}"
    return make_api_request(endpoint)

def fetch_user_details(user_id):
    endpoint = f"{CANVAS_API_URL}/users/{user_id}"
    return make_api_request(endpoint)

def fetch_inbox_messages():
    endpoint = f"{CANVAS_API_URL}/conversations"
    return make_api_request(endpoint)

def fetch_course_files(course_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/files"
    params = {"sort": "created_at", "order": "desc"}
    return make_api_request(endpoint, params)
def fetch_announcements(course_id):
    endpoint = f"{CANVAS_API_URL}/announcements"
    params = {"context_codes[]": f"course_{course_id}", "per_page": 5}
    return make_api_request(endpoint, params)
def clean_html(raw_html):
    """Remove HTML tags from a string."""
    clean_text = re.sub(r"<.*?>", "", raw_html)
    return clean_text
def format_posted_time(posted_at):
    user_timezone = pytz.timezone("US/Pacific")
    dt = datetime.strptime(posted_at, "%Y-%m-%dT%H:%M:%SZ")
    due_date_utc = pytz.utc.localize(dt)
    due_date_local = due_date_utc.astimezone(user_timezone)
    return due_date_local.strftime("%m/%d/%Y at %I:%M %p")
# Tasks for notifications
@tasks.loop(minutes=1)
async def announce_grades():

    print("Checking for new grades!")
    # Notify users based on preferences
    guild = bot.get_guild(DISCORD_SERVER_ID)
    if guild:
        for member in guild.members:
            #print(member)
            if member.bot:
                continue

            # Check user for grade notifications
            user_preferences = bot.user_preferences.get(member.id, [])
            
            for course_id in au.get_course_ids():
                submissions = fetch_graded_assignments(course_id)
                
                if not submissions:
                    continue

                for submission in submissions:
                    if submission['id'] not in seen_grades and submission.get('grade'):
                        seen_grades.add(submission['id'])
                        if "Grades" in user_preferences:
                            # Get assignment details
                            assignment_id = submission.get("assignment_id")
                            assignment_name = au.get_assignment_name(course_id, assignment_id)
                            user_id = submission.get("user_id")
                            student_name = au.get_student_name(user_id)
                            grade = submission.get('grade', "No Grade")
                            max_points = au.get_assignment_max_points(course_id, assignment_id)
                            formatted_grade = f"{grade}/{max_points}" if max_points else grade
                            comments = submission.get('submission_comments', [])

                            # Fetch comments if not included
                            if not comments:
                                comments = au.fetch_submission_comments(course_id, assignment_id, user_id)

                            # Format the comments
                            formatted_comments = "\n".join(
                                f"- {comment['author_name']} at {format_posted_time(comment['created_at'])}: {comment['comment']}"
                                for comment in comments
                            ) or "No comments"

                            link = submission.get("preview_url", "")

                            try:
                                # Send a DM to the user
                                await member.send(
                                    f"📢 **New Grade Posted!**\n"
                                    f"**Assignment:** {assignment_name}\n"
                                    f"**Student:** {student_name}\n"
                                    f"**Grade:** {formatted_grade}\n"
                                    f"**Comments:**\n{formatted_comments}\n"
                                    f"**Link:**\n{link}\n"
                                    )
                            except Exception as e:
                                print(f"Could not send DM to {member}: {e}")

@tasks.loop(minutes=1)
async def notify_inbox_messages():
    
    print("Checking for new messages!")
    # Notify users based on their preferences
    guild = bot.get_guild(DISCORD_SERVER_ID)
    if guild:
        for member in guild.members:
            if member.bot:
                continue

            # Get the users preferences
            user_preferences = bot.user_preferences.get(member.id, [])

            messages = fetch_inbox_messages()
            if not messages:
                continue

            for message in messages:
                if message['id'] not in seen_messages:
                    seen_messages.add(message['id'])
                    # Check if the user wants inbox message notifications
                    if "Messages" in user_preferences:

                        # Extract message details
                        sender_name = message.get('participants', [{}])[0].get('name', "Unknown Sender")
                        subject = message.get('subject', "No Subject")
                        body = message.get('last_message', "No Content")

                        try:
                            # Send a DM to the user
                            await member.send(
                                f"📧 **New Canvas Inbox Message!**\n"
                                f"**From:** {sender_name}\n"
                                f"**Subject:** {subject}\n"
                                f"**Message:** {body}"
                                )
                        except Exception as e:
                            print(f"Could not send DM to {member}: {e}")

@tasks.loop(minutes=1)
async def notify_new_files():

    print("Checking for new files!")
    course_ids = au.get_course_ids()
    
    for course_id in course_ids:
        # Fetch the list of file objects for the current course
        files = fetch_course_files(course_id)
        
        # Ensure non-empty list
        if not files or not isinstance(files, list):
            #print(f"No valid files found for course {course_id}. Response: {files}")
            continue

        for file in files:
            if file['id'] not in seen_files:
                seen_files.add(file['id'])

                # Extract file details
                file_name = file.get("display_name", "Unknown File")
                file_url = file.get("url", "No URL")
                upload_time = file.get("created_at", "Unknown Time")

                channel = bot.get_channel(DISCORD_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f"📂 **New File Uploaded!**\n"
                        f"**File Name:** {file_name}\n"
                        f"**Uploaded At:** {upload_time}\n"
                        f"**Download Link:** [Click here]({file_url})"
                    ) 
@tasks.loop(minutes=1)
async def check_new_announcements():

    print("Checking for new announcements!")
    # Notify users based on preferences
    guild = bot.get_guild(DISCORD_SERVER_ID)  # Replace SERVER_ID with your server's ID
    if guild:
        for member in guild.members:
            if member.bot:
                continue
                        
            # Check if the user has opted in for announcements
            user_preferences = bot.user_preferences.get(member.id, [])

            course_ids = au.get_course_ids()  # Retrieve all course IDs
            for course_id in course_ids:
                course_name = au.get_course_by_id(course_id)
                # Fetch announcements for the course
                announcements = fetch_announcements(course_id)
                if not announcements:
                    continue

                for announcement in announcements:
                    if announcement['id'] not in seen_announcements:
                        seen_announcements.add(announcement['id'])
                        if "Announcements" in user_preferences:
                            # Extract announcement details
                            title = announcement.get("title", "No Title")
                            raw_message = announcement.get("message", "No Content")
                            message = clean_html(raw_message)
                            posted_at = announcement.get("posted_at", "Unknown Time")
                            formatted_time = format_posted_time(posted_at)
                            try:
                                await member.send(
                                    f"📢 **New Announcement from {course_name}!**\n"
                                    f"**Title:** {title}\n"
                                    f"**Message:** {message}\n"
                                    f"**Posted At:** {formatted_time}"
                                    )
                            except Exception as e:
                                print(f"Could not send DM to {member}: {e}")                  

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    await bot.add_cog(Commands(bot))
    announce_grades.start()
    notify_inbox_messages.start()
    notify_new_files.start()
    check_new_announcements.start()

# Run the bot
bot.run(BOT_TOKEN)

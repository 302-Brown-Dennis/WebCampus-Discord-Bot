from os import getenv, listdir
from dotenv import load_dotenv

import discord
from discord.ext import tasks, commands
import requests

from cogs.commands import Commands

# Load environment variables
load_dotenv()
CANVAS_API_URL = getenv('CANVAS_API_URL')
CANVAS_API_TOKEN = getenv('CANVAS_API_TOKEN')
DISCORD_CHANNEL_ID = int(getenv("DISCORD_CHANNEL_ID", 0))
BOT_TOKEN = getenv('BOT_TOKEN')

# Set up the bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize sets to track seen items
seen_grades = set()
seen_messages = set()
seen_files = set()

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
            "I'm your new bot! Here are some commands to get you started:\n"
            "```\n"
            "!set_preferences <options> - Set notification preferences (grades, announcements, messages.)\n"
            "!view_preferences - View the current preferences for this channel\n"
            "!available_preferences - List the available preferences you can set for a channel\n"
            "!help - Show this help message\n"
            "```\n"
            "To get started, try `!set_preferences grades announcements`"
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

def fetch_submission_comments(course_id, assignment_id, user_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    submission = make_api_request(endpoint)
    return submission.get('submission_comments', []) if submission else []

def fetch_inbox_messages():
    endpoint = f"{CANVAS_API_URL}/conversations"
    return make_api_request(endpoint)

def fetch_course_files(course_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/files"
    params = {"sort": "created_at", "order": "desc"}
    return make_api_request(endpoint, params)

# Tasks for notifications
@tasks.loop(minutes=1)
async def announce_grades():
    course_id = 10759133
    submissions = fetch_graded_assignments(course_id)
    if not submissions:
        return

    for submission in submissions:
        if submission['id'] not in seen_grades and submission.get('grade'):
            seen_grades.add(submission['id'])

            # Get assignment details
            assignment_name = submission.get('assignment', {}).get('name', "Unknown Assignment")
            student_name = submission.get('user', {}).get('name', "Unknown Student")
            grade = submission.get('grade', "No Grade")
            comments = submission.get('submission_comments', [])

            # Fetch comments if not included
            if not comments:
                comments = fetch_submission_comments(course_id, submission['assignment_id'], submission['user_id'])

            # Format and send to Discord
            formatted_comments = "\n".join(
                f"- {comment['author_name']} ({comment['created_at']}): {comment['comment']}"
                for comment in comments
            ) or "No comments"
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📢 **New Grade Posted!**\n"
                    f"**Assignment:** {assignment_name}\n"
                    f"**Student:** {student_name}\n"
                    f"**Grade:** {grade}\n"
                    f"**Comments:**\n{formatted_comments}"
                )

@tasks.loop(minutes=1)
async def notify_inbox_messages():
    messages = fetch_inbox_messages()
    if not messages:
        return

    for message in messages:
        if message['id'] not in seen_messages:
            seen_messages.add(message['id'])

            # Extract message details
            sender_name = message.get('participants', [{}])[0].get('name', "Unknown Sender")
            subject = message.get('subject', "No Subject")
            body = message.get('last_message', "No Content")

            # Notify Discord
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📧 **New Canvas Inbox Message!**\n"
                    f"**From:** {sender_name}\n"
                    f"**Subject:** {subject}\n"
                    f"**Message:** {body}"
                )

@tasks.loop(minutes=1)
async def notify_new_files():
    course_id = 10759133
    files = fetch_course_files(course_id)
    if not files:
        return

    for file in files:
        if file['id'] not in seen_files:
            seen_files.add(file['id'])

            # Extract file details
            file_name = file.get("display_name", "Unknown File")
            file_url = file.get("url", "No URL")
            upload_time = file.get("created_at", "Unknown Time")

            # Notify Discord
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📂 **New File Uploaded!**\n"
                    f"**File Name:** {file_name}\n"
                    f"**Uploaded At:** {upload_time}\n"
                    f"**Download Link:** [Click here]({file_url})"
                )

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    await bot.add_cog(Commands(bot))
    #announce_grades.start()
    #notify_inbox_messages.start()
    #notify_new_files.start()

# Run the bot
bot.run(BOT_TOKEN)

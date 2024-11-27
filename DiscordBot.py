from os import getenv
from dotenv import load_dotenv

import discord
from discord.ext import tasks, commands
from discord.ui import View, Button, Select
import requests

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
CANVAS_API_URL = getenv('CANVAS_API_URL')
CANVAS_API_TOKEN = getenv('CANVAS_API_TOKEN')

channel_preferences = {}
seen_grades = set()
seen_messages = set()

#
# DENNIS
# NOTE:
# Code must be running BEFORE inviting the bot to a server for the below help message to display
#
@bot.event
async def on_guild_join(guild):
    # Find the "general" channel or the first available text channel
    default_channel = None
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            default_channel = channel
            break

    # Send a help message to the default channel
    if default_channel:
        help_message = (
            f"Hello, {guild.name}! 👋\n"
            "I'm your new bot! Here are some commands to get you started!:\n"
            "```\n"
            "!set_preferences <options> - Set notification preferences (grades, announcements, messages.)\n"
            "!view_preferences - View the current preferences for this channel\n"
            "!available_preferences - List the available preferences you can set for a channel\n"
            "!help - Show this help message\n"
            "```\n"
            "To get started, try `!set_preferences grades announcements`"
        )
        await default_channel.send(help_message)


# dev clear command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """
    DEV USE, deletes a specified amount of messages.
    Usage: !clear <amount> where amount is an int for number of messages to delete, side note max delete amount is 100
    """
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'Deleted {len(deleted)} messages.', delete_after=2)


# DEV gets number of message in channel
@bot.command()
async def count_messages(ctx, channel: discord.TextChannel = None):
    """
    DEV USE, counts the number of messages in a channel.
    If no channel is specified, counts messages in the current channel.
    Usage: !count_messages [#channel]
    """
    channel = channel or ctx.channel  # Use the specified channel or the current channel
    count = 0

    async for _ in channel.history(limit=None):  # Fetch all messages (limit=None)
        count += 1

    await ctx.send(f"There are {count} messages in {channel.mention}.")


# test hello command
@bot.command()
async def hello(ctx):
    """
    Prints a simple hello user message.
    Usage: !hello
    """
    await ctx.send(f"Hello, {ctx.author.name}!")


# set_preferences command
@bot.command()
async def set_preferences(ctx, *preferences):
    """
    Set the preferences for the current channel.
    Usage: !set_preferences grades announcements messages
    """
    channel_id = ctx.channel.id

    # Validate preferences
    valid_preferences = {"grades", "announcements", "messages"}
    selected_preferences = set(preferences).intersection(valid_preferences)

    if not selected_preferences:
        await ctx.send(f"Invalid preferences! Choose from: {', '.join(valid_preferences)}")
        return

    # Save preferences
    channel_preferences[channel_id] = selected_preferences
    await ctx.send(f"Preferences for this channel updated: {', '.join(selected_preferences)}")


# view_preferences command
@bot.command()
async def view_preferences(ctx):
    """
    View preferences set for this channel.
    Usage: !view_preferences
    """
    channel_id = ctx.channel.id
    preferences = channel_preferences.get(channel_id, "None set")
    await ctx.send(
        f"Current preferences for this channel: {', '.join(preferences) if preferences != 'None set' else preferences}")


# available_preferences command
@bot.command()
async def available_preferences(ctx):
    """
    View the available preferences to set.
    Usage: !available_preferences
    """
    valid_preferences = {"grades", "announcements", "messages"}
    await ctx.send(f"Available preferences to set: {', '.join(valid_preferences)}")


# get_classes command
# have to hard code this for now
@bot.command()
async def get_classes(ctx):
    """
    View your current classes.
    Usage: !get_classes
    """
    await ctx.send("Your current classes are:\n"
                   "CS 420 Human Computer Interaction\n"
                   "CS 457 Database Management Systems\n"
                   "CS 458 Introduction to Data Mining\n"
                   "CS 474 Image Processing and Interpretation\n"
                   "CPE 470 Auto Mobile Robots\n"
                   )


# hard coded command for new grade
@bot.command()
async def test_grade(ctx):
    """
    test grades.
    Usage: !test_grade
    """
    await ctx.send("Your CS 420 assignment Project Part #2: Discovery & Specification was graded!\n"
                   "You received a 93/100 (93%)!\n"
                   "Click the link below to be taken to the assignment.\n"
                   "https://webcampus.unr.edu/courses/113486/assignments/1458290/submissions/125446\n"
                   )


# hard coded command for assignment submissions
@bot.command()
async def test_submit(ctx):
    """
    test assignment submit.
    Usage: !test_submit
    """
    await ctx.send("Your assignment 'Project Part #3 Design'\n"
                   "For CS 420 Human Computer Interaction\n"
                   "Was succesfully submitted at 5:16 PM on 11/26/2024!\n"
                   "Click the link below to view the submission\n"
                   "https://webcampus.unr.edu/courses/113486/assignments/1458290/submissions/125446\n"
                   )


# hard coded command for announcments
@bot.command()
async def test_announce(ctx):
    """
    test announcments.
    Usage: !test_announce
    """
    await ctx.send("You have a new announcement from CS 420 Human Computer Interaction.\n\n"
                   "From: Sergiu Dascalu\n"
                   "Subject: CS 420/620 midterm exam tomorrow, WED November 20, from 4:00 pm\n"
                   "Hi all, this is a just reminder the midterm test will take place tomorrow, WED Nov 20 from 4:00 pm, online (via Canvas). You might start it up to 20 minutes late without losing any of the allocated time (70 min for the regular, non-DRC extended test). S. Dascalu\n\n"
                   "Click the link below to view the announcement\n"
                   "https://webcampus.unr.edu/courses/113486/discussion_topics/1135299\n"
                   )


# hard coded command that gets current gpa from classes
@bot.command()
async def test_remind(ctx):
    """
    test assignment reminder.
    Usage: !test_remind
    """
    await ctx.send("REMINDER!\n"
                   "Your assignment 'Project Part #3 Design'\n"
                   "For CS 420 Human Computer Interaction\n"
                   "Is due tomorrow 11/26/2024 at 11:59 PM!\n"
                   )


# hard coded command for getting class grade
@bot.command()
async def get_class_grade(ctx, *, class_name: str = None):
    """
    Gets your grade for a class.
    Usage: !get_class_grade <Class name> Example: !get_class_grade CPE 470 Auto Mobile Robots
    """
    if not class_name:
        await ctx.send("Please provide a class name")
        return
    if class_name.lower() == "cs 420 human computer interaction":
        await ctx.send("Your current grade for CS 420 Human Computer Interaction is: 95.64% (A)\n")
    if class_name.lower() == "cs 457 database management systems":
        await ctx.send("Your current grade for CS 457 Database Management Systems is: 91.9% (A)\n")
    if class_name.lower() == "cpe 470 auto mobile robots":
        await ctx.send("Your current grade for CPE 470 Auto Mobile Robots is: 109.32% (A)\n")


# hard coded command that gets current gpa from classes
@bot.command()
async def get_gpa(ctx):
    """
    Calcualtes your current gpa from your classes.
    Usage: !get_gpa
    """
    await ctx.send("Your current GPA is: 3.26")

# Fake Grades for each class
grades = {
    "CS 420 Human Computer Interaction": "95.64% (A)",
    "CS 457 Database Management Systems": "91.9% (A)",
    "CS 458 Introduction to Data Mining": "88.5% (B+)",
    "CPE 470 Auto Mobile Robots": "92.0% (A-)"
}

DISCORD_CHANNEL_ID = 1310883244807422024  # Replace with your channel ID
def fetch_graded_assignments(course_id):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/students/submissions"
    params = {
        "graded_since": "2023-01-01T00:00:00Z",  # Adjust as needed
        "include[]": "submission_comments"       # Ensure comments are included
    }

    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching graded assignments: {response.status_code}")
        return []
    
def fetch_assignment_details(course_id, assignment_id):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}"

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching assignment details: {response.status_code}")
        return None


def fetch_user_details(user_id):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    endpoint = f"{CANVAS_API_URL}/users/{user_id}"

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user details: {response.status_code}")
        return None

def fetch_submission_comments(course_id, assignment_id, user_id):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json().get('submission_comments', [])
    else:
        print(f"Error fetching submission comments: {response.status_code}")
        return []

@tasks.loop(minutes=1)  # Check for new grades every 5 minutes
async def announce_grades():
    course_id = 10759133  # Replace with your Canvas course ID
    submissions = fetch_graded_assignments(course_id)

    for submission in submissions:
        if submission['id'] not in seen_grades and submission.get('grade'):
            seen_grades.add(submission['id'])

            # Handle 'user' field
            student_name = "Unknown Student"
            if 'user' in submission:
                student_name = submission['user'].get('name', "Unknown Student")
            elif 'user_id' in submission:
                user_details = fetch_user_details(submission['user_id'])
                if user_details:
                    student_name = user_details.get('name', "Unknown Student")

            # Handle 'assignment' field
            assignment_name = "Unknown Assignment"
            if 'assignment' in submission:
                assignment_name = submission['assignment'].get('name', "Unknown Assignment")
            elif 'assignment_id' in submission:
                assignment_details = fetch_assignment_details(course_id, submission['assignment_id'])
                if assignment_details:
                    assignment_name = assignment_details.get('name', "Unknown Assignment")

            grade = submission.get('grade', "No Grade")

 # Fetch comments dynamically if not included
            comments = submission.get('submission_comments', [])
            if not comments and 'assignment_id' in submission and 'user_id' in submission:
                comments = fetch_submission_comments(course_id, submission['assignment_id'], submission['user_id'])

            # Format comments
            formatted_comments = "\n".join(
                f"- {comment['author_name']} ({comment['created_at']}): {comment['comment']}"
                for comment in comments
            ) or "No comments"

            # Send message to Discord
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📢 **New Grade Posted!**\n"
                    f"**Assignment:** {assignment_name}\n"
                    f"**Student:** {student_name}\n"
                    f"**Grade:** {grade}\n"
                    f"**Comments:**\n{formatted_comments}"
                )

def fetch_inbox_messages():
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    endpoint = f"{CANVAS_API_URL}/conversations"
    #params = {"filter": "unread"}  # Fetch only unread messages

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching inbox messages: {response.status_code}")
        return []
    
@tasks.loop(minutes=1)  # Check for new messages every 5 minutes
async def notify_inbox_messages():
    messages = fetch_inbox_messages()
    for message in messages:
        if message['id'] not in seen_messages:
            seen_messages.add(message['id'])  # Mark message as seen

            # Extract sender name
            sender_name = "Unknown Sender"
            participants = message.get("participants", [])
            if participants:
                sender_name = participants[0].get("name", "Unknown Sender")  # Adjust logic if needed

            # Extract message subject and body
            subject = message.get("subject", "No Subject")
            body = message.get("last_message", "No Content")

            # Send notification to Discord
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📧 **New Canvas Inbox Message!**\n"
                    f"**From:** {sender_name}\n"
                    f"**Subject:** {subject}\n"
                    f"**Message:** {body}"
                )
# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged sin as {bot.user}!")
    #announce_grades.start()
    notify_inbox_messages.start()

# View for Main Menu
class MainMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GradeButton())
        self.add_item(PreferencesButton())
        self.add_item(ClassesButton())

# Grade Button
class GradeButton(Button):
    def __init__(self):
        super().__init__(label="Grades", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        # Create an embed for grades
        embed = discord.Embed(
            title="Grade Options",
            description=(
                "Select a class below to see your grade:\n"
                "- View a specific class grade\n"
                "- Calculate GPA\n"
                "- Check recent grades\n"
            ),
            color=discord.Color.blue(),
        )

        # Create the Select menu with the list of classes
        select = ClassSelectMenu()

        # Add the Select menu to the view
        grade_view = View(timeout=None)
        grade_view.add_item(select)
        grade_view.add_item(GetGPAButton())
        grade_view.add_item(BackToMenuButton())

        await interaction.response.edit_message(embed=embed, view=grade_view)

# Select Menu for Classes
class ClassSelectMenu(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="CS 420 Human Computer Interaction"),
            discord.SelectOption(label="CS 457 Database Management Systems"),
            discord.SelectOption(label="CS 458 Introduction to Data Mining"),
            discord.SelectOption(label="CPE 470 Auto Mobile Robots")
        ]
        super().__init__(placeholder="Choose a class...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Get the selected class from the dropdown
        selected_class = self.values[0]
        grade = grades.get(selected_class, "Class not found.")

        # Send the grade for the selected class as an ephemeral (whisper) message
        await interaction.response.send_message(f"The grade for `{selected_class}` is: {grade}", ephemeral=True)

# Get GPA Button
class GetGPAButton(Button):
    def __init__(self):
        super().__init__(label="Calculate GPA", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Your current GPA is: 3.26",
            ephemeral=True,
        )

# Preferences Button
class PreferencesButton(Button):
    def __init__(self):
        super().__init__(label="Preferences", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        # Create an embed for preferences
        embed = discord.Embed(
            title="Notification Preferences",
            description=(
                "Choose your notification preferences:\n"
                "- Grades\n"
                "- Announcements\n"
                "- Messages\n"
            ),
            color=discord.Color.green(),
        )

        # Add Preferences-specific Buttons
        preferences_view = View(timeout=None)
        preferences_view.add_item(SetPreferencesButton())
        preferences_view.add_item(ViewPreferencesButton())
        preferences_view.add_item(BackToMenuButton())

        await interaction.response.edit_message(embed=embed, view=preferences_view)

# Set Preferences Button
class SetPreferencesButton(Button):
    def __init__(self):
        super().__init__(label="Set Preferences", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "To set preferences, type `!set_preferences <options>`. To see available preferences use `!available_preferences`.",
            ephemeral=True,
        )

# View Preferences Button
class ViewPreferencesButton(Button):
    def __init__(self):
        super().__init__(label="View Preferences", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Current preferences: Grades, Announcements",
            ephemeral=True,
        )

# Classes Button
class ClassesButton(Button):
    def __init__(self):
        super().__init__(label="Classes", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        # Create an embed for classes
        embed = discord.Embed(
            title="Class Options",
            description=(
                "Choose an action related to your classes:\n"
                "- View current classes\n"
                "- View assignments\n"
            ),
            color=discord.Color.purple(),
        )

        # Add Classes-specific Buttons
        class_view = View(timeout=None)
        class_view.add_item(ViewClassesButton())
        class_view.add_item(BackToMenuButton())

        await interaction.response.edit_message(embed=embed, view=class_view)

# View Classes Button
class ViewClassesButton(Button):
    def __init__(self):
        super().__init__(label="View Classes", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Your current classes are:\n"
            "- CS 420 Human Computer Interaction\n"
            "- CS 457 Database Management Systems\n"
            "- CS 458 Introduction to Data Mining\n"
            "- CPE 470 Auto Mobile Robots",
            ephemeral=True,
        )

# Back to Main Menu Button
class BackToMenuButton(Button):
    def __init__(self):
        super().__init__(label="Back to Main Menu", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Main Menu",
            description=(
                "Welcome to the bot! Use the buttons below to navigate:\n"
                "- Grades\n"
                "- Preferences\n"
                "- Classes"
            ),
            color=discord.Color.gold(),
        )
        await interaction.response.edit_message(embed=embed, view=MainMenu())

# Command: Start Menu
@bot.command()
async def menu(ctx):
    """
    Opens the main menu with buttons.
    """
    embed = discord.Embed(
        title="Main Menu",
        description=(
            "Welcome to the bot! Use the buttons below to navigate:\n"
            "- Grades\n"
            "- Preferences\n"
            "- Classes"
        ),
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed, view=MainMenu())

# Run the bot
bot.run(getenv('BOT_TOKEN'))

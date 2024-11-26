import discord
from discord.ext import commands

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
channel_preferences = {}

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

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
    deleted = await ctx.channel.purge(limit=amount+1)
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
    await ctx.send(f"Current preferences for this channel: {', '.join(preferences) if preferences != 'None set' else preferences}")

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

# Run the bot
bot.run("MTMxMDg3NDY5NjQ3NjI2MjQ0MA.GbjMHL.ZmeSN0zNEyblcl_WCX61r5Dm-F923NVtQBojIY")
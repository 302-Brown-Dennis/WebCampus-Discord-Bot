from Menu import MainMenu
import discord
from discord.ext import commands, tasks

import ApiUtil as au

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user = bot.user
        self.channel_preferences = {}

    @commands.command()
    async def test(self, ctx):
        await ctx.send("Test command works!")

    # dev clear command
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """
        DEV USE, deletes a specified amount of messages.
        Usage: !clear <amount> where amount is an int for number of messages to delete, side note max delete amount is 100
        """
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'Deleted {len(deleted)} messages.', delete_after=2)
    @commands.command()
    async def clear_dm(self, ctx, amount: int):
        """
        Clears the specified number of bot messages in the current DM channel.
        Usage: !clear_dm <amount> where amount is an int for number of messages to delete.
        """
        if isinstance(ctx.channel, discord.DMChannel):  # Check if the command is in a DM
            messages_to_delete = []
            async for message in ctx.channel.history(limit=amount + 1):
                if message.author == self.bot.user:  # Only delete bot messages
                    messages_to_delete.append(message)

            for message in messages_to_delete:
                await message.delete()

            await ctx.send(f"Cleared {len(messages_to_delete)} bot messages in this DM.", delete_after=2)
        else:
            await ctx.send("This command can only be used in DMs.")
    # DEV gets number of message in channel
    @commands.command()
    async def count_messages(self, ctx, channel: discord.TextChannel = None):
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
    @commands.command()
    async def hello(self, ctx):
        """
        Prints a simple hello user message.
        Usage: !hello
        """
        await ctx.send(f"Hello, {ctx.author.name}!")

    # set_preferences command
    @commands.command()
    async def set_preferences(self, ctx, *preferences):
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
        self.channel_preferences[channel_id] = selected_preferences
        await ctx.send(f"Preferences for this channel updated: {', '.join(selected_preferences)}")

    # view_preferences command
    @commands.command()
    async def view_preferences(self, ctx):
        """
        View preferences set for this channel.
        Usage: !view_preferences
        """
        channel_id = ctx.channel.id
        preferences = self.channel_preferences.get(channel_id, "None set")
        await ctx.send(
            f"Current preferences for this channel: {', '.join(preferences) if preferences != 'None set' else preferences}")

    # available_preferences command
    @commands.command()
    async def available_preferences(self, ctx):
        """
        View the available preferences to set.
        Usage: !available_preferences
        """
        valid_preferences = {"grades", "announcements", "messages"}
        await ctx.send(f"Available preferences to set: {', '.join(valid_preferences)}")

    # get_classes command
    # have to hard code this for now
    @commands.command()
    async def get_classes(self, ctx):
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
    @commands.command()
    async def test_grade(self, ctx):
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
    @commands.command()
    async def test_submit(self, ctx):
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
    @commands.command()
    async def test_announce(self, ctx):
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
    @commands.command()
    async def test_remind(self, ctx):
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
    @commands.command()
    async def get_class_grade(self, ctx, *, class_name: str = None):
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
    @commands.command()
    async def get_gpa(self, ctx):
        """
        Calcualtes your current gpa from your classes.
        Usage: !get_gpa
        """
        #await ctx.send("Your current GPA is: 3.26")
        gpa, average_percentage = au.calculate_gpa()
        try:
            await ctx.author.send(f"Your current GPA is: {gpa}")
            await ctx.send(f"✅ Message sent to {ctx.author.name}.")
        except discord.Forbidden:
            await ctx.send(f"❌ Could not send a DM to {ctx.author.name}. They might have DMs disabled.")
        except discord.HTTPException as e:
            # Catch any other HTTP-related exceptions (e.g., if Discord blocks DMs)
            await ctx.send(f"❌ Could not send a DM to {ctx.author.name}. Error: {str(e)}")


    # Command: Start Menu
    @commands.command(name="menu")
    async def menu(self, ctx):

        embed = discord.Embed(
            title="Main Menu",
            description=(
                "Welcome to the bot! Use the buttons below to navigate:\n"
                "- View Upcoming Assignments\n"
                "- Grades\n"
                "- Preferences\n"
                "- Classes"
            ),
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed, view=MainMenu(self.bot))


# Add the Cog to the bot
async def setup(bot):
    print("Loading Commands Cog...")
    bot.add_cog(Commands(bot))

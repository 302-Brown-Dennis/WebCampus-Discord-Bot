import discord
from discord.ui import View, Button, Select
import ApiUtil as au

# Fake Grades for each class
grades = {
    "CS 420 Human Computer Interaction": "95.64% (A)",
    "CS 457 Database Management Systems": "91.9% (A)",
    "CS 458 Introduction to Data Mining": "88.5% (B+)",
    "CPE 470 Auto Mobile Robots": "92.0% (A-)"
}

# View for Main Menu
class MainMenu(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(GradeButton(self.bot))
        self.add_item(PreferencesButton(self.bot))
        self.add_item(ClassesButton(self.bot))


# Grade Button
class GradeButton(Button):
    def __init__(self, bot):
        super().__init__(label="Grades", style=discord.ButtonStyle.primary)
        self.bot = bot

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
        select = ClassSelectMenu(self.bot)

        # Add the Select menu to the view
        grade_view = View(timeout=None)
        grade_view.add_item(select)
        grade_view.add_item(GetGPAButton(self.bot))
        grade_view.add_item(BackToMenuButton(self.bot))

        await interaction.response.edit_message(embed=embed, view=grade_view)

# Select Menu for Classes
class ClassSelectMenu(Select):
    def __init__(self, bot):
        # Dynamically populate options based on stored courses
        course_names = au.get_course_names()
        options = [discord.SelectOption(label=course) for course in course_names]

        super().__init__(
            placeholder="Choose a class...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Get the selected class from the dropdown
        selected_class = self.values[0]
        course_ids = au.get_course_ids()
        course_names = au.get_course_names()

        # Match the selected course name to its ID
        course_id = None
        for idx, name in enumerate(course_names):
            if name == selected_class:
                course_id = course_ids[idx]
                break

        if course_id:
            letter_grade, percent_grade = au.get_current_grade(course_id)
            letter_grade_message = letter_grade if letter_grade else "No letter grade data available."
            percent_grade_message = percent_grade if percent_grade else "No percent grade data available."
            await interaction.response.send_message(
                f"In your class {selected_class}, you have a {letter_grade_message}, with a grade of {percent_grade_message}%", ephemeral=True
            )
        else:
            await interaction.response.send_message("Selected class not found.", ephemeral=True)

# Get GPA Button
class GetGPAButton(Button):
    def __init__(self, bot):
        super().__init__(label="Calculate GPA", style=discord.ButtonStyle.secondary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Get the bot's context from the interaction
        ctx = await self.bot.get_context(interaction.message)
        # Manually update the ctx.author to the user who interacted with the button
        ctx.author = interaction.user

        # Trigger the get_gpa command
        await ctx.invoke(self.bot.get_command('get_gpa'))
        await interaction.response.send_message(
            "Your GPA has been requested.", ephemeral=True,
        )

# Preferences Button
class PreferencesButton(Button):
    def __init__(self, bot):
        super().__init__(label="Preferences", style=discord.ButtonStyle.primary)
        self.bot = bot

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
        preferences_view.add_item(SetPreferencesButton(self.bot))
        preferences_view.add_item(ViewPreferencesButton(self.bot))
        preferences_view.add_item(BackToMenuButton(self.bot))

        await interaction.response.edit_message(embed=embed, view=preferences_view)

# Set Preferences Button
class SetPreferencesButton(Button):
    def __init__(self, bot):
        super().__init__(label="Set Preferences", style=discord.ButtonStyle.secondary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "To set preferences, type `!set_preferences <options>`. To see available preferences use `!available_preferences`.",
            ephemeral=True,
        )

# View Preferences Button
class ViewPreferencesButton(Button):
    def __init__(self, bot):
        super().__init__(label="View Preferences", style=discord.ButtonStyle.secondary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Current preferences: Grades, Announcements",
            ephemeral=True,
        )

# Classes Button
class ClassesButton(Button):
    def __init__(self, bot):
        super().__init__(label="Classes", style=discord.ButtonStyle.primary)
        self.bot = bot

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
        class_view.add_item(ViewClassesButton(self.bot))
        class_view.add_item(BackToMenuButton(self.bot))

        await interaction.response.edit_message(embed=embed, view=class_view)

# View Classes Button
class ViewClassesButton(Button):
    def __init__(self, bot):
        super().__init__(label="View Classes", style=discord.ButtonStyle.secondary)
        self.bot = bot

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
    def __init__(self, bot):
        super().__init__(label="Back to Main Menu", style=discord.ButtonStyle.danger)
        self.bot = bot

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
        await interaction.response.edit_message(embed=embed, view=MainMenu(self.bot))
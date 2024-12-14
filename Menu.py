import json

import discord
from discord.ui import View, Button, Select
import ApiUtil as au
# View for Main Menu
class MainMenu(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(ViewUpcomingAssignmentsButton(self.bot))
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
        grade_view.add_item(GetRecentGrades(self.bot, select))
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

# Get Recent Grades Button
class GetRecentGrades(Button):
    def __init__(self, bot, select_menu):
        super().__init__(label="Get Recent Grades", style=discord.ButtonStyle.secondary)
        self.bot = bot
        self.select_menu = select_menu

    async def callback(self, interaction: discord.Interaction):
        # Fetch selected course or all courses
        selected_class = self.select_menu.values[0] if self.select_menu.values else None
        course_ids = au.get_course_ids()
        course_names = au.get_course_names()
        recent_grades = []

        if selected_class:
            # Fetch course ID for selected class
            course_id = None
            for idx, name in enumerate(course_names):
                if name == selected_class:
                    course_id = course_ids[idx]
                    break
            if course_id:
                recent_grades = au.fetch_recent_grades(course_id)
        else:
            # Fetch grades for all courses
            for course_id in course_ids:
                recent_grades.extend(au.fetch_recent_grades(course_id))

        if not recent_grades:
            await interaction.response.send_message(
                "No recent grades were found within the past 3 days.",
                ephemeral=True,
            )
            return

        # Format recent grades
        grades_list = "\n".join(
            f"**{grade['assignment_name']}**\n"
            f"Student: {grade['student_name']}\n"
            f"Grade: {grade['grade']}\n"
            f"Graded at: {grade['graded_at']}\n"
            f"[View Assignment]({grade['link']})\n"
            for grade in recent_grades
        )

        embed = discord.Embed(
            title="Recently Graded Assignments",
            description=grades_list,
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        # Create a new view for setting preferences
        set_preferences_view = PreferencesView(self.bot)

        # Embed for the Set Preferences UI
        embed = discord.Embed(
            title="Set Your Preferences",
            description="Please select your preferences using the dropdown below.",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed, view=set_preferences_view, ephemeral=True)
# Preferences View with Dropdown
class PreferencesView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        # 2 drop downs one to add , one to remove
        self.add_item(PreferencesDropdown(bot, action="add"))
        self.add_item(PreferencesDropdown(bot, action="remove"))

# Dropdown for selecting preferences
class PreferencesDropdown(Select):
    def __init__(self, bot, action="add"):
   
        self.bot = bot
        self.action = action
        options = [
            discord.SelectOption(label="Grades", description="Notifications for grades"),
            discord.SelectOption(label="Announcements", description="Notifications for announcements"),
            discord.SelectOption(label="Messages", description="Notifications for messages"),
        ]

        placeholder_text = "Select preferences to add..." if action == "add" else "Select preferences to remove..."

        super().__init__(
            placeholder=placeholder_text,
            min_values=1,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Get user ID
        user_id = interaction.user.id

        # Ensure the user has an entry in the preferences dictionary
        if user_id not in self.bot.user_preferences:
            self.bot.user_preferences[user_id] = []

        # Get the user's current preferences
        current_preferences = set(self.bot.user_preferences[user_id])

        # Add or remove preferences based on the action
        if self.action == "add":
            updated_preferences = current_preferences.union(set(self.values))
        elif self.action == "remove":
            updated_preferences = current_preferences.difference(set(self.values))
        else:
            await interaction.response.send_message(
                "Invalid action! Please try again.", ephemeral=True
            )
            return

        # Update the user's preferences
        self.bot.user_preferences[user_id] = list(updated_preferences)

        # Format the updated preferences for response
        updated_preferences_str = ", ".join(self.bot.user_preferences[user_id]) or "No preferences set."
        await interaction.response.send_message(
            f"Your preferences have been updated. Current preferences: {updated_preferences_str}",
            ephemeral=True,
        )

# View Preferences Button
class ViewPreferencesButton(Button):
    def __init__(self, bot):
        super().__init__(label="View Preferences", style=discord.ButtonStyle.secondary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        preferences = self.bot.user_preferences.get(user_id, ["No preferences set."])
        await interaction.response.send_message(
            f"Your current preferences are: {', '.join(preferences)}",
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
        # Fetch the current classes
        course_names = au.get_course_names()
        if not course_names:
            await interaction.response.send_message(
                "No classes found. Please make sure you have enrolled in courses and synced data.",
                ephemeral=True,
            )
            return

        # Format the class list
        classes_list = "\n".join(f"- {course}" for course in course_names)
        await interaction.response.send_message(
            f"Your current classes are:\n{classes_list}",
            ephemeral=True,
        )

# Button to View Upcoming Assignments
class ViewUpcomingAssignmentsButton(Button):
    def __init__(self, bot):
        super().__init__(label="View Upcoming Assignments", style=discord.ButtonStyle.primary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Fetch course IDs from locally saved courses
        # Fetch upcoming assignments within the next week
        upcoming_assignments = au.fetch_upcoming_assignments(au.get_course_ids())
        if not upcoming_assignments:
            await interaction.response.send_message(
                "No upcoming assignments due within the next week.",
                ephemeral=True,
            )
            return

        # Sort assignments by due date
        upcoming_assignments.sort(
            key=lambda x: x['due_date']
        )

        # Format the upcoming assignments for display
        assignments_list = "\n".join(
            f"- {assignment['assignment']} (Due: {assignment['due_date']}) for Class: {au.get_course_by_id(assignment['course'])}, Link: {assignment['link']}"
            for assignment in upcoming_assignments
        )

        await interaction.response.send_message(
            f"Here are your upcoming assignments due within the next week (sorted by due date):\n{assignments_list}",
            ephemeral=True,
        )

# Back to Main Menu Button
class BackToMenuButton(Button):
    def __init__(self, bot):
        super().__init__(label="Back to Main Menu", style=discord.ButtonStyle.danger)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Create a main menu embed
        embed = discord.Embed(
            title="Main Menu",
            description=(
                "Welcome to the bot! Use the buttons below to navigate:\n"
                "- View Upcoming Assignments"
                "- Grades\n"
                "- Preferences\n"
                "- Classes"
            ),
            color=discord.Color.gold(),
        )

        # Create the main menu view and add buttons
        main_menu_view = MainMenu(self.bot)

        await interaction.response.edit_message(embed=embed, view=main_menu_view)
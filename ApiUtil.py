from datetime import datetime, timedelta
import json
import pytz
from os import getenv
from dotenv import load_dotenv

import requests

load_dotenv()
CANVAS_API_URL = getenv('CANVAS_API_URL')
CANVAS_API_TOKEN = getenv('CANVAS_API_TOKEN')
DISCORD_CHANNEL_ID = int(getenv("DISCORD_CHANNEL_ID", 0))
BOT_TOKEN = getenv('BOT_TOKEN')

USER_TIMEZONE = pytz.timezone("America/Los_Angeles")
USER_TIMEZONE_PLUS = pytz.timezone("America/Denver")

# Canvas API Helper Functions
def make_api_request(endpoint, params=None):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    response = requests.get(endpoint, headers=headers, params=params or {})
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching data from {endpoint}: {response.status_code}")
    return None

def fetch_student_courses():
    endpoint = f"{CANVAS_API_URL}/courses"
    params = {"enrollment_type": "student"}  # Filter for courses where the user is enrolled as a student
    courses = make_api_request(endpoint, params)

    if not courses:
        print("No courses found or error fetching courses.")
        return

    # Extract course IDs and names
    course_data = [
        {"id": course["id"], "name": course.get("name", "Unnamed Course")}
        for course in courses
    ]

    # Store the courses locally in a JSON file
    try:
        with open("student_courses.json", "w") as file:
            json.dump(course_data, file, indent=4)
        print("Courses saved successfully to student_courses.json")
    except Exception as e:
        print(f"Error saving courses to file: {e}")

def get_course_names():
    try:
        with open("student_courses.json", "r") as file:
            courses = json.load(file)
        return [course["name"] for course in courses]
    except FileNotFoundError:
        print("No courses file found. Please fetch courses first.")
        return []
    except Exception as e:
        print(f"Error reading courses file: {e}")
        return []

def get_course_ids():
    try:
        with open("student_courses.json", "r") as file:
            courses = json.load(file)
        return [course["id"] for course in courses]
    except FileNotFoundError:
        print("No courses file found. Please fetch courses first.")
        return []
    except Exception as e:
        print(f"Error reading courses file: {e}")
        return []

def get_course_by_id(course_id):
    try:
        with open("student_courses.json", "r") as file:
            courses = json.load(file)
        for course in courses:
            if course["id"] == course_id:
                return course["name"]
        print("Course ID not found.")
        return None
    except FileNotFoundError:
        print("No courses file found. Please fetch courses first.")
        return None
    except Exception as e:
        print(f"Error reading courses file: {e}")
        return None

def get_current_grade(course_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/enrollments"
    enrollments = make_api_request(endpoint)

    if not enrollments:
        print("No enrollment data found for the course.")
        return None

    #print(f"Enrollments API response: {enrollments}")

    for enrollment in enrollments:
        # Check for the correct enrollment type and that grades exist
        if enrollment.get("type") == "StudentEnrollment" and enrollment.get("grades"):
            grades = enrollment["grades"]
            current_score = grades.get("current_score")
            if current_score is None:
                current_score = 100.0
            # Prefer current_grade if available, fallback to current_score
            return convert_score_to_grade(current_score), current_score

    print("No grade data available for the course.")
    return None

def convert_score_to_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def calculate_gpa():
    course_ids = get_course_ids()
    if not course_ids:
        print("No courses available to calculate GPA.")
        return None

    total_points = 0
    total_percent = 0
    total_courses = 0

    grade_to_points = {
        "A": 4.0,
        "B": 3.0,
        "C": 2.0,
        "D": 1.0,
        "F": 0.0
    }

    for course_id in course_ids:
        letterGrade, grade = get_current_grade(course_id)
        if letterGrade and letterGrade in grade_to_points:
            if grade:
                total_percent += grade
            total_points += grade_to_points[letterGrade]
            total_courses += 1

    if total_courses == 0:
        print("No valid grades found to calculate GPA.")
        return None

    average_percent = total_percent / total_courses
    gpa = total_points / total_courses
    return gpa, average_percent

# Canvas API Helper Functions
def make_api_request(endpoint, params=None):
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}
    response = requests.get(endpoint, headers=headers, params=params or {})
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching data from {endpoint}: {response.status_code}")
    return None


def fetch_upcoming_assignments(course_ids):
    # Define today's date and the date 7 days from now in UTC
    today = datetime.now(pytz.utc)  # Current time in UTC
    one_week_later = today + timedelta(weeks=1)

    upcoming_assignments = []

    for course_id in course_ids:
        # Fetch assignments for each course
        endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments"
        params = {"include[]": "submission"}
        assignments = make_api_request(endpoint, params)

        if assignments:
            # Filter assignments that are due within the next week
            for assignment in assignments:
                due_date_str = assignment.get("due_at")
                submission = assignment.get("submission", {})

                if submission.get("grade") is None and submission.get("submitted_at") is None and due_date_str:
                    # Parse the due date from Canvas in UTC
                    due_date_utc = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    due_date_utc = pytz.utc.localize(due_date_utc)  # Localize the UTC time

                    # Convert the due date to the user's local time zone (Pacific Time)
                    due_date_local = due_date_utc.astimezone(USER_TIMEZONE_PLUS)

                    # Only include assignments due within the next week in the local time zone
                    if today <= due_date_local <= one_week_later:
                        # Format the due date to a more readable format
                        formatted_due_date = due_date_utc.astimezone(USER_TIMEZONE_PLUS).strftime("%B %d, %Y, %I:%M %p")

                        upcoming_assignments.append({
                            "course": assignment["course_id"],
                            "assignment": assignment["name"],
                            "due_date": formatted_due_date,
                            "link": assignment.get("html_url", "")
                        })

    return upcoming_assignments

def fetch_recent_grades(course_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/students/submissions"
    submissions = make_api_request(endpoint)

    if not submissions:
        return []

    recent_grades = []
    three_days_ago = datetime.now(pytz.utc) - timedelta(days=3)

    for submission in submissions:
        graded_at_str = submission.get("graded_at")
        if graded_at_str:
            graded_at = datetime.strptime(graded_at_str, "%Y-%m-%dT%H:%M:%SZ")
            graded_at = pytz.utc.localize(graded_at)

            if graded_at >= three_days_ago:
                assignment_id = submission.get("assignment_id")
                assignment_name = get_assignment_name(course_id, assignment_id)

                user_id = submission.get("user_id")
                student_name = get_student_name(user_id)

                grade = submission.get("grade")
                score = submission.get("score", 0)

                # Fetch max points for the assignment
                max_points = get_assignment_max_points(course_id, assignment_id)
                formatted_grade = f"{score}/{max_points}" if max_points else grade

                # Fetch submission comments
                comments = submission.get('submission_comments', [])

                # Fetch comments if they are not included
                if not comments:
                    comments = fetch_submission_comments(course_id, submission['assignment_id'], submission['user_id'])

                # Format comments
                formatted_comments = "\n".join(
                    f"- {comment['author_name']} ({comment['created_at']}): {comment['comment']}"
                    for comment in comments
                ) or "No comments"

                link = submission.get("preview_url", "")

                recent_grades.append({
                    "assignment_name": assignment_name,
                    "student_name": student_name,
                    "grade": formatted_grade,
                    "comments": formatted_comments,
                    "link": link,
                    "graded_at": graded_at.astimezone(USER_TIMEZONE).strftime("%B %d, %Y, %I:%M %p")
                })

    return recent_grades

def get_assignment_name(course_id, assignment_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}"
    assignment_data = make_api_request(endpoint)
    return assignment_data.get("name", "Unnamed Assignment")

def get_student_name(user_id):
    endpoint = f"{CANVAS_API_URL}/users/{user_id}"
    user_data = make_api_request(endpoint)
    return user_data.get("name", "Unknown Student")

def get_assignment_max_points(course_id, assignment_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}"
    assignment_data = make_api_request(endpoint)
    return assignment_data.get("points_possible", 0)

def fetch_submission_comments(course_id, assignment_id, user_id):
    endpoint = f"{CANVAS_API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    submission = make_api_request(endpoint)
    return submission.get('submission_comments', []) if submission else []
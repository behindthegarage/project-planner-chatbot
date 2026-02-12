import sqlite3
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def get_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, supplies, instructions FROM activities')
    activities = cursor.fetchall()
    conn.close()
    return activities

def update_activity(id, age_group, justification, adaptations):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE activities
    SET development_age_group = ?, development_group_justification = ?, adaptations = ?
    WHERE id = ?
    ''', (age_group, justification, adaptations, id))
    conn.commit()
    conn.close()

def analyze_activity(activity):
    prompt = f"""
    You are an AI assistant specializing in early childhood education and development. Your task is to analyze child care activities and categorize them into the most appropriate developmental group. For each activity, you will be given its title, description, list of supplies, and instructions.

    Analyze each component of the activity and categorize it into one of the following groups:
    1. Toddlers (2-3 years old)
    2. Preschoolers (3-5 years old)
    3. School-age (6-13 years old)

    Consider the following factors when making your determination:
    1. Complexity of the activity
    2. Required fine and gross motor skills
    3. Cognitive demands
    4. Language and communication requirements
    5. Social interaction level
    6. Safety considerations
    7. Attention span needed
    8. Relevance to developmental milestones

    For the activity, provide:
    1. The chosen developmental group (Toddlers, Preschoolers, or School-age)
    2. A brief explanation (2-3 sentences) justifying your choice
    3. Any adaptations that could make the activity suitable for younger or older groups

    If an activity seems to span multiple age groups, choose the most appropriate primary group and explain why, noting which elements might be suitable for other age ranges.

    Activity: "{activity[1]}"
    Description: {activity[2]}
    Supplies: {activity[3]}
    Instructions: {activity[4]}

    Please provide your analysis in the following format:
    Categorization: [Age Group]
    Justification: [Your justification]
    Adaptations: [Your adaptations]
    """

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_response(response.content[0].text)

def parse_response(response):
    age_group = "Unknown"
    justification = "No justification provided"
    adaptations = "No adaptations provided"

    current_section = None
    sections = {"Categorization": "", "Justification": "", "Adaptations": ""}

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith("Categorization:"):
            current_section = "Categorization"
            sections[current_section] = line.split(":", 1)[1].strip()
        elif line.startswith("Justification:"):
            current_section = "Justification"
            sections[current_section] = line.split(":", 1)[1].strip()
        elif line.startswith("Adaptations:"):
            current_section = "Adaptations"
            sections[current_section] = line.split(":", 1)[1].strip()
        elif current_section:
            sections[current_section] += " " + line

    age_group = sections["Categorization"]
    justification = sections["Justification"]
    adaptations = sections["Adaptations"]

    return age_group, justification, adaptations

def main():
    activities = get_activities()
    total_activities = len(activities)
    for index, activity in enumerate(activities, 1):
        print(f"Analyzing activity {index}/{total_activities}: {activity[1]}")
        try:
            age_group, justification, adaptations = analyze_activity(activity)
            update_activity(activity[0], age_group, justification, adaptations)
            print(f"Updated activity: {activity[1]} - {age_group}")
            print(f"Adaptations: {adaptations}")
        except Exception as e:
            print(f"Error processing activity {activity[1]}: {str(e)}")

if __name__ == "__main__":
    main()
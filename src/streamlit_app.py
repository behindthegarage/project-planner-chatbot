import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import os
import json
from anthropic import Anthropic
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from streamlit_extras.colored_header import colored_header
from streamlit_extras.app_logo import add_logo
import random
import datetime
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile

# Load environment variables
load_dotenv()

# Initialize clients
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone_client.Index(os.getenv('PINECONE_INDEX_NAME'))

# Initialize session state for generated activities
if 'generated_activities' not in st.session_state:
    st.session_state.generated_activities = []

# Initialize session state for supplies-generated activities
if 'supplies_generated_activities' not in st.session_state:
    st.session_state.supplies_generated_activities = []

# Function to fetch activities that need to be done
def get_todo_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE to_do = 1')
    activities = cursor.fetchall()
    conn.close()
    return activities

# Function to fetch supplies for all to-do activities
def get_supplies_list():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT supplies FROM activities WHERE to_do = 1')
    supplies = cursor.fetchall()
    conn.close()
    return supplies

# Function to fetch all activities from the database
def get_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities')
    activities = cursor.fetchall()
    conn.close()
    return activities

# Function to get all available supplies from the database
def get_available_supplies():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM available_supplies ORDER BY category, item')
    supplies = cursor.fetchall()
    conn.close()
    return supplies

# Function to add a new supply to the database
def add_supply(category, item):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO available_supplies (category, item) VALUES (?, ?)', (category, item))
    conn.commit()
    conn.close()

# Function to delete a supply from the database
def delete_supply(supply_id):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM available_supplies WHERE id = ?', (supply_id,))
    conn.commit()
    conn.close()

# Function to get supplies grouped by category
def get_supplies_by_category():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, GROUP_CONCAT(item, ", ") as items FROM available_supplies GROUP BY category ORDER BY category')
    supplies_by_category = cursor.fetchall()
    conn.close()
    return supplies_by_category

# Function to add an activity to the database
def add_activity(title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO activities (title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations))
    conn.commit()
    conn.close()

# Function to update an activity in the database
def update_activity(id, title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations):
    try:
        conn = sqlite3.connect('activities.db')
        # Set the database connection to read-write mode
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE activities
        SET title = ?, type = ?, description = ?, supplies = ?, instructions = ?, source = ?, to_do = ?, development_age_group = ?, development_group_justification = ?, adaptations = ?
        WHERE id = ?
        ''', (title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations, id))
        conn.commit()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {str(e)}. Please check file permissions.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        conn.close()

# Function to delete an activity from the database and Pinecone
def delete_activity(id):
    # Delete from SQLite database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    # Delete from Pinecone
    pinecone_index.delete(ids=[str(id)])

# New functions from other files
def generate_activities(theme):
    prompt = f"""
    Given the theme "{theme}", create 2 activities for each of these types: Art, Craft, Science, Cooking, and Physical (5 activities total).
    For each activity, provide the following details in a JSON array format:
    {{
        "Activity Title": "Title of the activity",
        "Type": "Art/Craft/Science/Cooking/Physical",
        "Description": "One sentence description",
        "Supplies": ["List", "of", "supplies"],
        "Instructions": ["Step 1", "Step 2", "etc"]
    }}

    Important: Keep each activity concise and ensure the response is complete. Do not cut off mid-activity.
    Ensure the JSON is properly formatted and complete.
    """

    try:
        response = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        api_response_content = response.content[0].text
        
        # Find JSON content
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        
        if json_start == -1 or json_end == 0:
            st.error("No JSON array found in the response")
            st.code(api_response_content)  # Show the raw response for debugging
            return None
            
        json_content = api_response_content[json_start:json_end]
        
        # Check if the JSON content is complete
        if not json_content.strip().endswith("]"):
            st.error("Response appears to be truncated. Please try again.")
            st.code(json_content)  # Show the truncated content for debugging
            return None
        
        # Try to clean up common JSON issues
        json_content = json_content.replace('\n', ' ').replace('\r', ' ')
        json_content = json_content.replace('",}', '"}').replace(',]', ']')
        
        # Parse JSON
        try:
            activities = json.loads(json_content)
        except json.JSONDecodeError as json_error:
            st.error(f"JSON parsing error: {json_error}")
            st.error("Raw JSON content:")
            st.code(json_content)
            return None
        
        # Validate activities structure
        if not isinstance(activities, list):
            st.error("Response is not a list of activities")
            return None
            
        for activity in activities:
            required_fields = ["Activity Title", "Type", "Description", "Supplies", "Instructions"]
            missing_fields = [field for field in required_fields if field not in activity]
            if missing_fields:
                st.error(f"Activity missing required fields: {', '.join(missing_fields)}")
                return None
                
        return activities
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON from API response. Error: {e}")
        st.error("Raw API response:")
        st.code(api_response_content)
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

def generate_activities_from_supplies(supplies_list, theme=None):
    # Clean and simplify the supplies list to avoid overly long prompts
    supplies_clean = []
    for supply in supplies_list.split(','):
        supply_clean = supply.strip()
        # Remove detailed descriptions in parentheses to shorten the prompt
        if '(' in supply_clean:
            supply_clean = supply_clean.split('(')[0].strip()
        supplies_clean.append(supply_clean)
    
    # Limit to first 20 supplies to keep prompt manageable
    supplies_clean = supplies_clean[:20]
    supplies_text = ", ".join(supplies_clean)
    
    theme_context = f" with the theme '{theme}'" if theme else ""
    theme_instruction = f" Each activity should incorporate the theme '{theme}' while using the provided supplies." if theme else ""
    
    prompt = f"""
    Given the following list of supplies: {supplies_text}{theme_context}
    
    Create 2 activities for each of these types: Art, Craft, Science, Cooking, and Physical (5 activities total).
    Each activity must use at least some of the provided supplies, but you can suggest additional supplies if needed.{theme_instruction}
    
    For each activity, provide the following details in a JSON array format:
    {{
        "Activity Title": "Title of the activity",
        "Type": "Art/Craft/Science/Cooking/Physical",
        "Description": "One sentence description",
        "Supplies": ["List", "of", "supplies", "including", "provided", "ones"],
        "Instructions": ["Step 1", "Step 2", "etc"]
    }}

    Important: 
    - Keep each activity concise and ensure the response is complete. Do not cut off mid-activity.
    - Make sure to incorporate the provided supplies creatively into each activity.
    - If additional supplies are needed, clearly indicate which ones are from the provided list vs. additional suggestions.
    - Ensure the JSON is properly formatted and complete.
    """

    try:
        # Add retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                api_response_content = response.content[0].text
                break  # Success, exit retry loop
            except Exception as api_error:
                if attempt < max_retries - 1:
                    st.warning(f"API call attempt {attempt + 1} failed, retrying... ({str(api_error)})")
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
                else:
                    raise api_error  # Re-raise on final attempt
        
        # Find JSON content
        json_start = api_response_content.find("[")
        json_end = api_response_content.rfind("]") + 1
        
        if json_start == -1 or json_end == 0:
            st.error("No JSON array found in the response")
            st.code(api_response_content)  # Show the raw response for debugging
            return None
            
        json_content = api_response_content[json_start:json_end]
        
        # Check if the JSON content is complete
        if not json_content.strip().endswith("]"):
            st.error("Response appears to be truncated. Please try again.")
            st.code(json_content)  # Show the truncated content for debugging
            return None
        
        # Try to clean up common JSON issues
        json_content = json_content.replace('\n', ' ').replace('\r', ' ')
        json_content = json_content.replace('",}', '"}').replace(',]', ']')
        
        # Parse JSON
        try:
            activities = json.loads(json_content)
        except json.JSONDecodeError as json_error:
            st.error(f"JSON parsing error: {json_error}")
            st.error("Raw JSON content:")
            st.code(json_content)
            return None
        
        # Validate activities structure
        if not isinstance(activities, list):
            st.error("Response is not a list of activities")
            return None
            
        for activity in activities:
            required_fields = ["Activity Title", "Type", "Description", "Supplies", "Instructions"]
            missing_fields = [field for field in required_fields if field not in activity]
            if missing_fields:
                st.error(f"Activity missing required fields: {', '.join(missing_fields)}")
                return None
                
        return activities
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON from API response. Error: {e}")
        st.error("Raw API response:")
        st.code(api_response_content)
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

def get_embedding(text):
    response = openai_client.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

def add_activity_bulk(conn, cursor, index, activity):
    insert_query = """
    INSERT INTO activities (title, type, description, supplies, instructions, to_do, source, development_age_group, development_group_justification, adaptations)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        activity['Activity Title'],
        activity['Type'],
        activity['Description'],
        ', '.join(activity['Supplies']),
        '\n'.join(activity['Instructions']),
        True,
        "AI",
        activity.get('Development Age Group', 'Not specified'),
        activity.get('Development Group Justification', ''),
        activity.get('Adaptations', '')
    ))
    conn.commit()
    activity_id = cursor.lastrowid
    text = (
        f"Title: {activity['Activity Title']}\n"
        f"Description: {activity['Description']}\n"
        f"Supplies: {', '.join(activity['Supplies'])}\n"
        f"Instructions: {' '.join(activity['Instructions'])}"
    )
    embedding = get_embedding(text)
    index.upsert(vectors=[{
        "id": str(activity_id),
        "values": embedding,
        "metadata": {
            "type": activity['Type'],
            "to_do": True
        }
    }])

def parse_activities(text):
    activities = []
    current_activity = {}
    current_field = None

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if current_activity:
                activities.append(current_activity)
                current_activity = {}
            current_field = None
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.lower()
            if key in ['type', 'description', 'supplies', 'instructions']:
                current_activity[key] = value.strip()
                current_field = key
            elif 'title' not in current_activity:
                current_activity['title'] = line.strip()
        elif 'title' not in current_activity:
            current_activity['title'] = line
        elif current_field:
            current_activity[current_field] += ' ' + line

    if current_activity:
        activities.append(current_activity)

    return activities

def search_activities(keyword, top_k=4):
    embedding = get_embedding(keyword)
    activity_types = ['Art', 'Craft', 'Science', 'Cooking', 'Physical']
    results = {}
    for activity_type in activity_types:
        query_results = pinecone_index.query(vector=embedding, top_k=top_k, filter={"type": activity_type}, include_metadata=True)
        results[activity_type] = [result['id'] for result in query_results['matches']]
    return results

# Add this new function after the other database-related functions
def get_activities_by_ids(ids):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    placeholders = ', '.join('?' for _ in ids)
    query = f"SELECT * FROM activities WHERE id IN ({placeholders})"
    cursor.execute(query, ids)
    activities = cursor.fetchall()
    conn.close()
    return activities

# New function to get random activities for each type
def get_random_activities():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    activity_types = ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"]
    random_activities = {}
    for activity_type in activity_types:
        cursor.execute('SELECT * FROM activities WHERE type = ? ORDER BY RANDOM() LIMIT 2', (activity_type,))
        random_activities[activity_type] = cursor.fetchall()
    conn.close()
    return random_activities

# --- Weekly Planner Scheduling Helpers ---
def ensure_schedule_table():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER,
        scheduled_date TEXT,
        FOREIGN KEY(activity_id) REFERENCES activities(id)
    )
    ''')
    conn.commit()
    conn.close()

def ensure_weekly_meta_table():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_meta (
            week_start TEXT PRIMARY KEY,
            week_theme TEXT
        )
    ''')
    conn.commit()
    conn.close()

ensure_schedule_table()
ensure_weekly_meta_table()

def get_weekly_meta(week_start):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT week_theme FROM weekly_meta WHERE week_start = ?', (week_start,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] or ''
    return ''

def set_weekly_meta(week_start, week_theme):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO weekly_meta (week_start, week_theme)
        VALUES (?, ?)
        ON CONFLICT(week_start) DO UPDATE SET week_theme=excluded.week_theme
    ''', (week_start, week_theme))
    conn.commit()
    conn.close()

def get_scheduled_activities_for_week(start_date):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    end_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=6)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT s.id, s.scheduled_date, a.id, a.title, a.type, a.description
        FROM activity_schedule s
        JOIN activities a ON s.activity_id = a.id
        WHERE s.scheduled_date BETWEEN ? AND ?
        ORDER BY s.scheduled_date
    ''', (start_date, end_date))
    results = cursor.fetchall()
    conn.close()
    return results

def add_activity_to_schedule(activity_id, scheduled_date):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO activity_schedule (activity_id, scheduled_date) VALUES (?, ?)', (activity_id, scheduled_date))
    conn.commit()
    conn.close()

def remove_scheduled_activity(schedule_id):
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activity_schedule WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

def get_all_week_themes():
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT week_start, week_theme FROM weekly_meta ORDER BY week_start')
    rows = cursor.fetchall()
    conn.close()
    # Only include rows with a non-empty theme
    return [(row[0], row[1]) for row in rows if row[1]]

# --- Weekly Supply List Helpers ---
def get_scheduled_activities_with_supplies(start_date):
    """Get all activities scheduled for a week with their supplies."""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    end_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=6)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT a.id, a.title, a.type, a.supplies, s.scheduled_date
        FROM activity_schedule s
        JOIN activities a ON s.activity_id = a.id
        WHERE s.scheduled_date BETWEEN ? AND ?
        ORDER BY s.scheduled_date, a.type
    ''', (start_date, end_date))
    results = cursor.fetchall()
    conn.close()
    return results

def normalize_supply_name(supply):
    """Normalize a supply name for de-duplication."""
    # Convert to lowercase, strip whitespace, remove common pluralization differences
    normalized = supply.lower().strip()
    # Remove trailing 's' for basic de-duplication (paper vs papers)
    if normalized.endswith('s') and len(normalized) > 3:
        normalized = normalized[:-1]
    return normalized

def parse_supplies(supplies_text):
    """Parse supplies text into individual items."""
    if not supplies_text:
        return []
    # Split by comma, newline, or bullet points
    items = []
    for separator in [',', '\n', '•', '-', '*']:
        if separator in supplies_text:
            items = supplies_text.split(separator)
            break
    else:
        items = [supplies_text]
    
    # Clean up each item
    cleaned = []
    for item in items:
        item = item.strip()
        # Remove quantities in parentheses like "(10 sheets)" or "(1 bottle)"
        if '(' in item and ')' in item:
            item = item[:item.find('(')].strip()
        # Remove leading bullets or numbers
        item = item.lstrip('0123456789.-•* ').strip()
        if item and len(item) > 1:
            cleaned.append(item)
    return cleaned

def get_supply_category_mapping():
    """Get a mapping of supply names to their categories."""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT category, item FROM available_supplies')
    supplies = cursor.fetchall()
    conn.close()
    
    # Create mapping: normalized supply name -> category
    mapping = {}
    for category, item in supplies:
        normalized = normalize_supply_name(item)
        mapping[normalized] = category
        # Also map the original
        mapping[item.lower().strip()] = category
    return mapping

def aggregate_weekly_supplies(scheduled_activities):
    """Aggregate supplies from scheduled activities, de-duplicate and categorize."""
    supply_mapping = get_supply_category_mapping()
    
    # Track supplies: normalized_name -> {original_name, count, activities, category}
    supplies_agg = {}
    
    for activity in scheduled_activities:
        activity_id, title, act_type, supplies_text, scheduled_date = activity
        supplies_list = parse_supplies(supplies_text)
        
        for supply in supplies_list:
            normalized = normalize_supply_name(supply)
            
            if normalized not in supplies_agg:
                # Try to find category from available supplies
                category = supply_mapping.get(normalized, 'Uncategorized')
                if category == 'Uncategorized':
                    # Try fuzzy match
                    for known_supply, known_category in supply_mapping.items():
                        if normalized in known_supply or known_supply in normalized:
                            category = known_category
                            break
                
                supplies_agg[normalized] = {
                    'original': supply,
                    'count': 1,
                    'activities': [title],
                    'category': category
                }
            else:
                supplies_agg[normalized]['count'] += 1
                if title not in supplies_agg[normalized]['activities']:
                    supplies_agg[normalized]['activities'].append(title)
    
    # Group by category
    categorized = {}
    for normalized, data in supplies_agg.items():
        category = data['category']
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(data)
    
    # Sort within each category by count (descending) then alphabetically
    for category in categorized:
        categorized[category].sort(key=lambda x: (-x['count'], x['original']))
    
    # Sort categories: put Uncategorized last
    sorted_categories = sorted([c for c in categorized.keys() if c != 'Uncategorized'])
    if 'Uncategorized' in categorized:
        sorted_categories.append('Uncategorized')
    
    return {cat: categorized[cat] for cat in sorted_categories}

# Streamlit App
st.set_page_config(page_title="Activity Planner", page_icon="🎨", layout="wide")
# add_logo("./logo.png")  # Add your logo image

st.title("🎨 Activity Planner")

# Sidebar menu using streamlit-option-menu
with st.sidebar:
    st.title("Menu")
    choice = option_menu(
        menu_title=None,
        options=[
            "Home", "Theme Search", "Generate Activities (AI)", "Generate from Supplies (AI)",
            "View To Do Activities", "View Supplies List", "Manage Supplies",
            "Bulk Add Activities", "Add Activity",
            "Edit Activity", "View Activities", "Weekly Planner", "Weekly Supply List"
        ],
        icons=[
            'house', 'search', 'magic', 'box-seam',
            'list-check', 'cart', 'gear',
            'file-earmark-plus', 'plus-circle',
            'pencil', 'eye', 'calendar3', 'box'
        ],
        menu_icon="cast",
        default_index=0,
    )

# Main content area
if choice == "Home":
    colored_header(label="Featured Activities", description="Random activities for each type", color_name="blue-70")
    random_activities = get_random_activities()
    for activity_type, activities in random_activities.items():
        st.subheader(f"{activity_type}")
        for activity in activities:
            with st.expander(f"{activity[1]} (ID: {activity[0]})"):
                st.write(f"**Description:** {activity[3]}")
                st.write(f"**Supplies:** {activity[4]}")
                st.write(f"**Instructions:** {activity[5]}")
                st.write(f"**Source:** {activity[6]}")
                st.write(f"**Development Age Group:** {activity[8] if activity[8] else 'Not specified'}")
                to_do = st.checkbox("Add to To-Do List", value=activity[7], key=f"home_todo_{activity[0]}")
                if to_do != activity[7]:
                    update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do, activity[8], activity[9], activity[10])
                    st.rerun()

elif choice == "Theme Search":
    colored_header(label="Theme Search", description="Find activities based on a theme", color_name="blue-70")
    theme_description = st.text_input('Enter a theme description:')

    if 'theme_search_results' not in st.session_state:
        st.session_state.theme_search_results = {}

    if st.button('Search'):
        if theme_description:
            st.session_state.theme_search_results = search_activities(theme_description)
        else:
            st.error("Please enter a theme description to search.")

    if st.session_state.theme_search_results:
        for activity_type, ids in st.session_state.theme_search_results.items():
            if ids:
                activities = get_activities_by_ids(ids)
                if activities:
                    st.subheader(f"{activity_type} Activities:")
                    for activity in activities:
                        with st.expander(f"{activity[1]} (ID: {activity[0]})"):
                            st.write(f"**Type:** {activity[2]}")
                            st.write(f"**Description:** {activity[3]}")
                            st.write(f"**Supplies:** {activity[4]}")
                            st.write(f"**Instructions:** {activity[5]}")
                            st.write(f"**Source:** {activity[6]}")
                            st.write(f"**Development Age Group:** {activity[8] if activity[8] else 'Not specified'}")
                            to_do = st.checkbox("To Do", value=activity[7], key=f"todo_{activity[0]}")
                            if to_do != activity[7]:
                                update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do, activity[8], activity[9], activity[10])
                                st.rerun()
                else:
                    st.info(f"No matching {activity_type} activities found in the database.")
            else:
                st.info(f"No matching {activity_type} activities found in Pinecone.")

elif choice == "Generate Activities (AI)":
    colored_header(label="Generate Activities", description="Use AI to create new activities based on a theme or idea", color_name="green-70")
    theme = st.text_input("Enter a theme:")

    if st.button("Generate Activities"):
        if theme:
            activities = generate_activities(theme)
            if activities:
                st.session_state.generated_activities = activities
                st.success("Activities generated successfully!")
            else:
                st.error("No activities generated.")
        else:
            st.error("Please enter a theme.")

    if st.session_state.generated_activities:
        for i, activity in enumerate(st.session_state.generated_activities):
            st.subheader(activity["Activity Title"])
            st.write(f"**Type**: {activity['Type']}")
            st.write(f"**Description**: {activity['Description']}")
            st.write("**Supplies**:")
            st.write(", ".join(activity['Supplies']))
            st.write("**Instructions**:")
            for idx, instruction in enumerate(activity['Instructions'], 1):
                st.write(f"{idx}. {instruction}")
            st.write(f"**Development Age Group**: {activity.get('Development Age Group', 'Not specified')}")
            
            key = f"checkbox_{i}_{activity['Activity Title']}"
            activity['selected'] = st.checkbox("Select this activity", key=key, value=activity.get('selected', False))

        if st.button("Add Selected Activities"):
            selected_activities = [a for a in st.session_state.generated_activities if a.get('selected', False)]
            if selected_activities:
                conn = sqlite3.connect('activities.db')
                cursor = conn.cursor()
                
                success_count = 0
                for activity in selected_activities:
                    try:
                        add_activity_bulk(conn, cursor, pinecone_index, activity)
                        success_count += 1
                    except Exception as e:
                        st.error(f"Error adding activity '{activity['Activity Title']}': {str(e)}")
                
                conn.close()
                
                if success_count > 0:
                    st.success(f'{success_count} activities added and embedded successfully!')
                    # Clear the generated activities after successful addition
                    st.session_state.generated_activities = []
                    st.rerun()
                if success_count < len(selected_activities):
                    st.warning(f'{len(selected_activities) - success_count} activities failed to add. Please check the errors above.')
            else:
                st.warning("No activities selected. Please select at least one activity to add.")

elif choice == "Generate from Supplies (AI)":
    colored_header(label="Generate Activities from Supplies", description="Use AI to create new activities based on available supplies and theme", color_name="violet-70")
    
    # Get available supplies from database
    available_supplies = get_available_supplies()
    
    if not available_supplies:
        st.warning("No supplies in inventory. Please add supplies in the 'Manage Supplies' section first.")
        st.stop()
    
    # Group supplies by category for multi-select
    supplies_by_category = {}
    for supply in available_supplies:
        category = supply[1]
        if category not in supplies_by_category:
            supplies_by_category[category] = []
        supplies_by_category[category].append((supply[0], supply[2]))  # (id, item)
    
    st.subheader("Select Supplies from Inventory")
    
    # Create a single consolidated multi-select with category prefixes
    all_supply_options = []
    for category, supplies in supplies_by_category.items():
        for supply_id, item in supplies:
            all_supply_options.append(f"[{category}] {item}")
    
    selected_options = st.multiselect(
        "Select supplies from your inventory:",
        all_supply_options,
        help="Supplies are organized by category. You can search by typing."
    )
    
    # Extract just the item names from selected options
    selected_supplies = []
    for option in selected_options:
        # Remove the category prefix [Category] and extract just the item name
        item_name = option.split("] ", 1)[1] if "] " in option else option
        selected_supplies.append(item_name)
    
    # Custom supplies input
    st.subheader("Add Custom Supplies")
    custom_supplies_input = st.text_area(
        "Enter additional supplies (separate with commas):", 
        placeholder="e.g., paper, glue, scissors, paint, cardboard, markers"
    )
    
    # Theme input
    st.subheader("Theme (Optional)")
    theme_input = st.text_input("Enter a theme:", placeholder="e.g., space, ocean, dinosaurs, seasons")
    
    # Combine selected and custom supplies
    all_supplies = selected_supplies.copy()
    if custom_supplies_input.strip():
        custom_supplies = [supply.strip() for supply in custom_supplies_input.split(',')]
        all_supplies.extend(custom_supplies)
    
    # Display selected supplies
    if all_supplies:
        st.subheader("Selected Supplies")
        supplies_text = ", ".join(all_supplies)
        st.write(supplies_text)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Activities from Selected Supplies"):
                activities = generate_activities_from_supplies(supplies_text, theme_input.strip() if theme_input.strip() else None)
                if activities:
                    st.session_state.supplies_generated_activities = activities
                    theme_message = f" with theme '{theme_input}'" if theme_input.strip() else ""
                    st.success(f"Activities generated successfully from your supplies{theme_message}!")
                else:
                    st.error("No activities generated.")
        
        with col2:
            if st.button("Generate Activities from All Available Supplies"):
                # Get all supplies from database
                all_available_supplies = [supply[2] for supply in available_supplies]
                all_supplies_text = ", ".join(all_available_supplies)
                
                activities = generate_activities_from_supplies(all_supplies_text, theme_input.strip() if theme_input.strip() else None)
                if activities:
                    st.session_state.supplies_generated_activities = activities
                    theme_message = f" with theme '{theme_input}'" if theme_input.strip() else ""
                    st.success(f"Activities generated successfully from all available supplies{theme_message}!")
                else:
                    st.error("No activities generated.")
    else:
        st.subheader("Quick Generate")
        st.write("Generate activities using all available supplies in your inventory:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate from All Supplies"):
                # Get all supplies from database
                all_available_supplies = [supply[2] for supply in available_supplies]
                all_supplies_text = ", ".join(all_available_supplies)
                
                activities = generate_activities_from_supplies(all_supplies_text, theme_input.strip() if theme_input.strip() else None)
                if activities:
                    st.session_state.supplies_generated_activities = activities
                    theme_message = f" with theme '{theme_input}'" if theme_input.strip() else ""
                    st.success(f"Activities generated successfully from all available supplies{theme_message}!")
                else:
                    st.error("No activities generated.")
        
        with col2:
            if st.button("Generate Random Supply Activities"):
                # Select a random subset of supplies (10-15 items)
                import random
                all_available_supplies = [supply[2] for supply in available_supplies]
                num_supplies = min(random.randint(10, 15), len(all_available_supplies))
                random_supplies = random.sample(all_available_supplies, num_supplies)
                random_supplies_text = ", ".join(random_supplies)
                
                activities = generate_activities_from_supplies(random_supplies_text, theme_input.strip() if theme_input.strip() else None)
                if activities:
                    st.session_state.supplies_generated_activities = activities
                    theme_message = f" with theme '{theme_input}'" if theme_input.strip() else ""
                    st.success(f"Activities generated successfully from random supplies{theme_message}!")
                else:
                    st.error("No activities generated.")
        
        st.info("Or select specific supplies from the inventory above for more targeted generation.")

    if st.session_state.supplies_generated_activities:
        st.markdown("### Generated Activities from Your Supplies")
        for i, activity in enumerate(st.session_state.supplies_generated_activities):
            st.subheader(activity["Activity Title"])
            st.write(f"**Type**: {activity['Type']}")
            st.write(f"**Description**: {activity['Description']}")
            st.write("**Supplies**:")
            st.write(", ".join(activity['Supplies']))
            st.write("**Instructions**:")
            for idx, instruction in enumerate(activity['Instructions'], 1):
                st.write(f"{idx}. {instruction}")
            st.write(f"**Development Age Group**: {activity.get('Development Age Group', 'Not specified')}")
            
            key = f"supplies_checkbox_{i}_{activity['Activity Title']}"
            activity['selected'] = st.checkbox("Select this activity", key=key, value=activity.get('selected', False))

        if st.button("Add Selected Activities from Supplies"):
            selected_activities = [a for a in st.session_state.supplies_generated_activities if a.get('selected', False)]
            if selected_activities:
                conn = sqlite3.connect('activities.db')
                cursor = conn.cursor()
                
                success_count = 0
                for activity in selected_activities:
                    try:
                        add_activity_bulk(conn, cursor, pinecone_index, activity)
                        success_count += 1
                    except Exception as e:
                        st.error(f"Error adding activity '{activity['Activity Title']}': {str(e)}")
                
                conn.close()
                
                if success_count > 0:
                    st.success(f'{success_count} activities added and embedded successfully!')
                    # Clear the supplies-generated activities after successful addition
                    st.session_state.supplies_generated_activities = []
                    st.rerun()
                if success_count < len(selected_activities):
                    st.warning(f'{len(selected_activities) - success_count} activities failed to add. Please check the errors above.')
            else:
                st.warning("No activities selected. Please select at least one activity to add.")

elif choice == "View To Do Activities":
    colored_header(label="To Do Activities", description="View and manage activities to be done", color_name="violet-70")
    todo_activities = get_todo_activities()
    if todo_activities:
        for activity in todo_activities:
            with st.expander(f"{activity[1]} (ID: {activity[0]})"):
                st.write(f"**Type:** {activity[2]}")
                st.write(f"**Description:** {activity[3]}")
                st.write(f"**Supplies:** {activity[4]}")
                st.write(f"**Instructions:** {activity[5]}")
                st.write(f"**Source:** {activity[6]}")
                st.write(f"**Development Age Group:** {activity[8] if activity[8] else 'Not specified'}")
                to_do = st.checkbox("To Do", value=activity[7], key=f"todo_{activity[0]}")
                if to_do != activity[7]:
                    update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do, activity[8], activity[9], activity[10])
                    st.rerun()
    else:
        st.info("No activities to do!")

elif choice == "View Supplies List":
    st.subheader("Supplies List")
    st.caption("View supplies for all to-do activities")
    todo_activities = get_todo_activities()
    if todo_activities:
        for activity in todo_activities:
            st.markdown(f"**{activity[1]}**")
            supplies = [supply.strip() for supply in activity[4].split(',')]
            supplies_html = "<br>".join([f"&nbsp;&nbsp;{supply}" for supply in supplies])
            st.markdown(f'<div style="line-height: 1;">{supplies_html}</div>', unsafe_allow_html=True)
            st.write("---")
        
        if st.button("Print Supplies List"):
            printable_supplies = ''
            for activity in todo_activities:
                printable_supplies += f"<h3>{activity[1]} (ID: {activity[0]})</h3>"
                supplies = [supply.strip() for supply in activity[4].split(',')]
                printable_supplies += '<div style="line-height: 1.2;">'
                for supply in supplies:
                    printable_supplies += f"&nbsp;&nbsp;{supply}<br>"
                printable_supplies += "</div><hr>"
            
            st.markdown(f'''
                <div style="display: none;">
                    <div id="printable-supplies">
                        <h2>Supplies List for All To Do Activities</h2>
                        {printable_supplies}
                    </div>
                </div>
                <script>
                    var printContents = document.getElementById("printable-supplies").innerHTML;
                    var originalContents = document.body.innerHTML;
                    document.body.innerHTML = printContents;
                    window.print();
                    document.body.innerHTML = originalContents;
                </script>
            ''', unsafe_allow_html=True)
    else:
        st.info("No activities to do!")

elif choice == "Manage Supplies":
    colored_header(label="Manage Available Supplies", description="Add, view, and delete supplies from your inventory", color_name="blue-70")
    
    # Add new supply
    st.subheader("Add New Supply")
    supplies = get_available_supplies()
    existing_categories = sorted(list(set([s[1] for s in supplies if s[1]])))
    category_options = existing_categories + ["Other (type new category below)"] if existing_categories else ["Other (type new category below)"]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox("Category", category_options, key="supply_category_select")
        if selected_category == "Other (type new category below)":
            new_category = st.text_input("New Category", key="supply_category_new", placeholder="e.g., Art & Craft Supplies")
        else:
            new_category = selected_category
    with col2:
        new_item = st.text_input("Item", placeholder="e.g., Paint brushes")
    
    if st.button("Add Supply"):
        if new_category.strip() and new_item.strip():
            add_supply(new_category.strip(), new_item.strip())
            st.success(f"Added '{new_item}' to category '{new_category}'")
            st.rerun()
        else:
            st.error("Please enter both category and item.")
    
    # View and manage existing supplies
    st.subheader("Current Supplies")
    supplies = get_available_supplies()
    
    if supplies:
        st.write(f"**Total Supplies:** {len(supplies)} items")
        
        # Sort supplies by name first, then by category
        sorted_supplies = sorted(supplies, key=lambda x: (x[2].lower(), x[1].lower()))
        
        # Display all supplies in a simple list
        for supply in sorted_supplies:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"• {supply[2]}")
            with col2:
                st.write(f"*{supply[1]}*")  # Category in italics
            with col3:
                if st.button("Delete", key=f"delete_supply_{supply[0]}"):
                    delete_supply(supply[0])
                    st.success(f"Deleted '{supply[2]}'")
                    st.rerun()
    else:
        st.info("No supplies in inventory. Add some supplies above!")

elif choice == "Bulk Add Activities":
    colored_header(label="Bulk Add Activities", description="Add multiple activities at once", color_name="orange-70")
    
    st.markdown("""
    Enter multiple activities (separate each activity with a blank line):
    
    Example format:
    ```
    Fairy Jar Night Light
    Type: Craft
    Description: Make a magical fairy jar night light using a mason jar and fairy lights.
    Supplies:
    Mason jar, Fairy lights, Tissue paper, Glue, Scissors, Glitter
    Instructions:
    1. Cut small shapes from tissue paper.
    2. Glue the shapes to the outside of the jar.
    3. Sprinkle glitter inside the jar.
    4. Place fairy lights inside and secure the lid.
    ```
    """)
    
    activities_input = st.text_area('Enter activities here:', height=300)

    if st.button('Add Activities'):
        if activities_input:
            activities = parse_activities(activities_input)
            
            conn = sqlite3.connect('activities.db')
            cursor = conn.cursor()
            
            success_count = 0
            for activity in activities:
                try:
                    add_activity_bulk(conn, cursor, pinecone_index, activity)
                    success_count += 1
                except ValueError as e:
                    st.error(f"Error adding activity: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error adding activity: {str(e)}")
            
            conn.close()
            
            if success_count > 0:
                st.success(f'{success_count} activities added and embedded successfully!')
            if success_count < len(activities):
                st.warning(f'{len(activities) - success_count} activities failed to add. Please check the errors above.')
        else:
            st.error('Please enter at least one activity.')

elif choice == "Add Activity":
    colored_header(label="Add New Activity", description="Create a new activity", color_name="blue-70")
    title = st.text_input("Title", key="add_title")
    type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"], key="add_type")
    description = st.text_area("Description", key="add_description")
    supplies = st.text_area("Supplies", key="add_supplies")
    instructions = st.text_area("Instructions", key="add_instructions")
    
    
    development_age_group = st.selectbox("Development Age Group", 
                                         ["Toddlers (2-3 years)", "Preschoolers (3-5 years)", "School-age (6-13 years)", "Not specified"], 
                                         key="add_age_group")
    
    development_group_justification = st.text_area("Development Group Justification", key="add_justification")
    adaptations = st.text_area("Adaptations", key="add_adaptations")

    source = st.text_input("Source", key="add_source")
    to_do = st.checkbox("To Do", key="add_to_do")
    
    if st.button("Add", key="add_button"):
        add_activity(title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations)
        st.success(f"Activity '{title}' added successfully!")

elif choice == "Edit Activity":
    colored_header(label="Edit Activity", description="Modify an existing activity", color_name="orange-70")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids, key="edit_select_id")
    
    if selected_id:
        activity = [a for a in activities if a[0] == selected_id][0]
        title = st.text_input("Title", activity[1], key="edit_title")
        type = st.selectbox("Type", ["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"], index=["Art", "Cooking", "Craft", "Group Game", "Physical", "Puzzle", "Science"].index(activity[2]), key="edit_type")
        description = st.text_area("Description", activity[3], key="edit_description")
        supplies = st.text_area("Supplies", activity[4], key="edit_supplies")
        instructions = st.text_area("Instructions", activity[5], key="edit_instructions")
        source = st.text_input("Source", activity[6], key="edit_source")
        to_do = st.checkbox("To Do", activity[7], key="edit_to_do")
        
        age_group_options = ["Toddlers (2-3 years)", "Preschoolers (3-5 years)", "School-age (6-13 years)", "Not specified"]
        current_age_group = activity[8] if activity[8] else "Not specified"
        
        # Find the closest match for the current age group
        if current_age_group not in age_group_options:
            if "Toddler" in current_age_group:
                current_age_group = "Toddlers (2-3 years)"
            elif "Preschool" in current_age_group:
                current_age_group = "Preschoolers (3-5 years)"
            elif "School" in current_age_group:
                current_age_group = "School-age (6-13 years)"
            else:
                current_age_group = "Not specified"
        
        development_age_group = st.selectbox("Development Age Group", 
                                             age_group_options,
                                             index=age_group_options.index(current_age_group),
                                             key="edit_age_group")
        
        development_group_justification = st.text_area("Development Group Justification", activity[9] if activity[9] else "", key="edit_justification")
        adaptations = st.text_area("Adaptations", activity[10] if activity[10] else "", key="edit_adaptations")
        
        if st.button("Update", key="edit_button"):
            update_activity(selected_id, title, type, description, supplies, instructions, source, to_do, development_age_group, development_group_justification, adaptations)
            st.success(f"Activity '{title}' updated successfully!")

elif choice == "View Activities":
    colored_header(label="All Activities", description="View all stored activities", color_name="green-70")
    activities = get_activities()
    
    # Sort activities by type
    activities_by_type = {}
    for activity in activities:
        activity_type = activity[2]  # The type is at index 2
        if activity_type not in activities_by_type:
            activities_by_type[activity_type] = []
        activities_by_type[activity_type].append(activity)
    
    # Display activities sorted by type
    for activity_type in sorted(activities_by_type.keys()):
        st.subheader(f"{activity_type} Activities")
        for activity in activities_by_type[activity_type]:
            with st.expander(f"{activity[1]} (ID: {activity[0]})"):
                st.write(f"**Description:** {activity[3]}")
                st.write(f"**Supplies:** {activity[4]}")
                st.write(f"**Instructions:** {activity[5]}")
                st.write(f"**Development Age Group:** {activity[8] if activity[8] else 'Not specified'}")
                st.write(f"**Development Group Justification:** {activity[9] if activity[9] else 'Not provided'}")
                st.write(f"**Adaptations:** {activity[10] if activity[10] else 'Not provided'}")
                st.write(f"**Source:** {activity[6]}")
                st.write(f"**To Do:** {'Yes' if activity[7] else 'No'}")

elif choice == "Delete Activity":
    colored_header(label="Delete Activity", description="Remove an activity from the database", color_name="red-70")
    activities = get_activities()
    activity_ids = [activity[0] for activity in activities]
    selected_id = st.selectbox("Select Activity ID", activity_ids, key="delete_select_id")
    
    if selected_id and st.button("Delete", key="delete_button"):
        delete_activity(selected_id)
        st.success("Activity deleted successfully from both SQLite and Pinecone!")

elif choice == "Weekly Planner":
    colored_header(label="Weekly Planner", description="Schedule activities in a weekly calendar", color_name="blue-70")
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())

    # Dropdown for selecting week by theme
    week_theme_options = get_all_week_themes()
    theme_labels = [f"{theme} ({week_start})" for week_start, theme in week_theme_options]
    theme_to_week = {f"{theme} ({week_start})": week_start for week_start, theme in week_theme_options}
    default_week_start = start_of_week.strftime('%Y-%m-%d')

    selected_theme_label = None
    if theme_labels:
        selected_theme_label = st.selectbox('Jump to week by theme:', ["Current Week"] + theme_labels, key="theme_select")
        if selected_theme_label != "Current Week":
            selected_week_start_str = theme_to_week[selected_theme_label]
            week_start = datetime.datetime.strptime(selected_week_start_str, '%Y-%m-%d').date()
        else:
            week_start = start_of_week
    else:
        week_start = start_of_week

    start_date = st.date_input("Select week (pick any day in week)", value=week_start)
    week_start = start_date - datetime.timedelta(days=start_date.weekday())
    # Only include Monday (0), Tuesday (1), Thursday (3), Friday (4)
    week_days = [0, 1, 3, 4]
    week_dates = [(week_start + datetime.timedelta(days=i)) for i in week_days]

    week_start_str = week_start.strftime('%Y-%m-%d')
    # Load from DB
    if 'week_theme' not in st.session_state or st.session_state.get('last_week_start') != week_start_str:
        theme = get_weekly_meta(week_start_str)
        st.session_state.week_theme = theme
        st.session_state.last_week_start = week_start_str

    # UI
    week_theme = st.text_input('Week Theme', value=st.session_state.week_theme, key=f"theme_{week_start_str}")

    # Save to DB if changed
    if week_theme != st.session_state.week_theme:
        set_weekly_meta(week_start_str, week_theme)
        st.session_state.week_theme = week_theme

    st.markdown(f"**Week Theme:** {week_theme}")

    # Fetch scheduled activities for the week
    scheduled = get_scheduled_activities_for_week(week_start.strftime('%Y-%m-%d'))
    scheduled_by_date = {d.strftime('%Y-%m-%d'): [] for d in week_dates}
    for sched in scheduled:
        if sched[1] in scheduled_by_date:
            scheduled_by_date[sched[1]].append(sched)

    # Fetch only 'to do' activities for selection
    all_activities = get_todo_activities()
    activity_options = {f"{a[1]} (ID: {a[0]})": a[0] for a in all_activities}

    st.write("### Weekly Calendar")
    cols = st.columns(len(week_dates))
    for i, day in enumerate(week_dates):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A')}<br>{day.strftime('%Y-%m-%d')}**", unsafe_allow_html=True)
            # List scheduled activities
            for sched in scheduled_by_date[day.strftime('%Y-%m-%d')]:
                # Get full activity details for the expandable section
                conn = sqlite3.connect('activities.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM activities WHERE id = ?', (sched[2],))
                activity = cursor.fetchone()
                conn.close()
                
                if activity:
                    with st.expander(f"{activity[1]} ({activity[2]}) [ID: {activity[0]}]"):
                        st.write(f"**Description:** {activity[3]}")
                        st.write(f"**Supplies:** {activity[4]}")
                        st.write(f"**Instructions:** {activity[5]}")
                        st.write(f"**Source:** {activity[6]}")
                        st.write(f"**Development Age Group:** {activity[8] if activity[8] else 'Not specified'}")
                        st.write(f"**Development Group Justification:** {activity[9] if activity[9] else 'Not provided'}")
                        st.write(f"**Adaptations:** {activity[10] if activity[10] else 'Not provided'}")
                        
                        # Add to-do checkbox
                        to_do = st.checkbox("Add to To-Do List", value=activity[7], key=f"weekly_todo_{activity[0]}")
                        if to_do != activity[7]:
                            update_activity(activity[0], activity[1], activity[2], activity[3], activity[4], activity[5], activity[6], to_do, activity[8], activity[9], activity[10])
                            st.rerun()
                        
                        if st.button("Remove", key=f"remove_{sched[0]}"):
                            remove_scheduled_activity(sched[0])
                            st.rerun()
                else:
                    # Fallback if activity not found
                    st.write(f"- {sched[3]} ({sched[4]}) [ID: {sched[2]}]")
                    if st.button("Remove", key=f"remove_{sched[0]}"):
                        remove_scheduled_activity(sched[0])
                        st.rerun()
            
            # Add new activity by entering ID or selecting from dropdown
            with st.expander("Add Activity by ID or To-Do Dropdown", expanded=False):
                activity_id_input = st.text_input(f"Enter activity ID for {day.strftime('%A')}", key=f"idinput_{day}")
                todo_options = {f"{a[1]} (ID: {a[0]})": a[0] for a in all_activities}
                selected_dropdown = st.selectbox(f"Or select from To-Do List for {day.strftime('%A')}", ["-"] + list(todo_options.keys()), key=f"dropdown_{day}")
                if st.button("Schedule", key=f"schedule_{day}"):
                    chosen_id = None
                    if activity_id_input.strip():
                        if activity_id_input.strip().isdigit():
                            activity_id = int(activity_id_input.strip())
                            all_ids = [a[0] for a in get_activities()]
                            if activity_id in all_ids:
                                chosen_id = activity_id
                            else:
                                st.error(f"Activity ID {activity_id} does not exist.")
                        else:
                            st.error("Please enter a valid numeric activity ID.")
                    elif selected_dropdown != "-":
                        chosen_id = todo_options[selected_dropdown]
                    else:
                        st.error("Please enter an activity ID or select from the to-do list.")
                    if chosen_id is not None:
                        add_activity_to_schedule(chosen_id, day.strftime('%Y-%m-%d'))
                        st.success(f"Scheduled activity ID {chosen_id} for {day.strftime('%A')}")
                        st.rerun()

    # Print feature
    if st.button("Generate Printable Weekly Plan"):
        # Get full activity details for all scheduled activities
        conn = sqlite3.connect('activities.db')
        cursor = conn.cursor()
        
        # Create HTML content for printing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weekly Activity Plan</title>
            <style>
                @page {{
                    margin: 1cm;
                    @top-center {{
                        content: "Weekly Activity Plan";
                        font-size: 10pt;
                    }}
                    @bottom-center {{
                        content: counter(page);
                        font-size: 10pt;
                    }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                h1, h2, h3 {{ text-align: center; }}
                h1 {{ color: #2c3e50; font-size: 24pt; margin-bottom: 20pt; }}
                h2 {{ color: #34495e; font-size: 18pt; margin-bottom: 15pt; }}
                h3 {{ color: #2c3e50; font-size: 16pt; margin-top: 20pt; }}
                .activity {{
                    margin-left: 20px;
                    margin-bottom: 15px;
                    page-break-inside: avoid;
                }}
                .activity h4 {{ color: #34495e; font-size: 14pt; }}
                .supplies {{ margin-left: 20px; }}
                .instructions {{ margin-left: 20px; }}
                .day-section {{
                    page-break-before: always;
                }}
                .day-section:first-child {{
                    page-break-before: avoid;
                }}
            </style>
        </head>
        <body>
            <h1>Weekly Activity Plan</h1>
            <h2>Week of {week_start.strftime('%B %d, %Y')}</h2>
            <h3>Theme: {week_theme}</h3>
        """
        
        # Add activities by day
        for day in week_dates:
            day_str = day.strftime('%Y-%m-%d')
            html_content += f"""
            <div class="day-section">
                <h3>{day.strftime('%A, %B %d')}</h3>
            """
            
            for sched in scheduled_by_date[day_str]:
                # Get full activity details
                cursor.execute('SELECT * FROM activities WHERE id = ?', (sched[2],))
                activity = cursor.fetchone()
                
                if activity:
                    html_content += f"""
                    <div class="activity">
                        <h4>{activity[1]} ({activity[2]}) <span style="color: #999; font-size: 10pt;">[ID: {activity[0]}]</span></h4>
                        <p><strong>Description:</strong> {activity[3]}</p>
                        <p><strong>Supplies:</strong></p>
                        <ul class="supplies">
                    """
                    
                    # Add supplies as list items
                    for supply in activity[4].split(','):
                        html_content += f"<li>{supply.strip()}</li>"
                    
                    html_content += """
                        </ul>
                        <p><strong>Instructions:</strong></p>
                        <ol class="instructions">
                    """
                    
                    # Add instructions as numbered list
                    for instruction in activity[5].split('\n'):
                        if instruction.strip():
                            html_content += f"<li>{instruction.strip()}</li>"
                    
                    html_content += """
                        </ol>
                    </div>
                    """
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Create PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            try:
                # Create a temporary HTML file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as html_tmp:
                    html_tmp.write(html_content)
                    html_tmp.flush()
                    
                    # Generate PDF from the HTML file
                    HTML(filename=html_tmp.name).write_pdf(
                        tmp.name,
                        font_config=font_config,
                        stylesheets=[CSS(string='''
                            @page { 
                                margin: 1cm;
                                size: letter;
                            }
                            body { 
                                font-family: Arial, sans-serif;
                                margin: 0;
                                padding: 0;
                            }
                            .day-section {
                                page-break-before: always;
                                margin-top: 20px;
                            }
                            .day-section:first-child {
                                page-break-before: avoid;
                            }
                            .activity {
                                page-break-inside: avoid;
                                margin-bottom: 20px;
                            }
                        ''')]
                    )
                    
                    # Clean up the temporary HTML file
                    os.unlink(html_tmp.name)
                
                # Read the PDF file
                with open(tmp.name, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                # Clean up the temporary PDF file
                os.unlink(tmp.name)
                
                # Create a download button for the PDF file
                st.download_button(
                    label="Download Weekly Plan PDF",
                    data=pdf_bytes,
                    file_name=f"weekly_plan_{week_start.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                # Display the HTML content for debugging
                st.markdown("### Debug: HTML Content")
                st.code(html_content)
        
        # Display a preview of the HTML content
        st.markdown("### Preview of Weekly Plan")
        st.markdown(html_content, unsafe_allow_html=True)
        
        conn.close()

elif choice == "Weekly Supply List":
    colored_header(label="Weekly Supply List", description="Aggregate and print supplies for all activities in a week", color_name="green-70")
    
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())

    # Dropdown for selecting week by theme
    week_theme_options = get_all_week_themes()
    theme_labels = [f"{theme} ({week_start})" for week_start, theme in week_theme_options]
    theme_to_week = {f"{theme} ({week_start})": week_start for week_start, theme in week_theme_options}
    default_week_start = start_of_week.strftime('%Y-%m-%d')

    selected_theme_label = None
    if theme_labels:
        selected_theme_label = st.selectbox('Jump to week by theme:', ["Current Week"] + theme_labels, key="supply_theme_select")
        if selected_theme_label != "Current Week":
            selected_week_start_str = theme_to_week[selected_theme_label]
            week_start = datetime.datetime.strptime(selected_week_start_str, '%Y-%m-%d').date()
        else:
            week_start = start_of_week
    else:
        week_start = start_of_week

    start_date = st.date_input("Select week (pick any day in week)", value=week_start, key="supply_week_date")
    week_start = start_date - datetime.timedelta(days=start_date.weekday())
    week_days = [0, 1, 3, 4]  # Mon, Tue, Thu, Fri
    week_dates = [(week_start + datetime.timedelta(days=i)) for i in week_days]
    
    week_start_str = week_start.strftime('%Y-%m-%d')
    
    # Get week theme
    week_theme = get_weekly_meta(week_start_str)
    if week_theme:
        st.markdown(f"**Week Theme:** {week_theme}")
    
    st.markdown(f"**Week of:** {week_start.strftime('%B %d, %Y')} - {(week_start + datetime.timedelta(days=6)).strftime('%B %d, %Y')}")
    
    # Get scheduled activities
    scheduled_activities = get_scheduled_activities_with_supplies(week_start_str)
    
    if not scheduled_activities:
        st.info("No activities scheduled for this week. Go to Weekly Planner to add activities.")
    else:
        st.write(f"**Activities scheduled:** {len(scheduled_activities)}")
        
        # Show activities breakdown
        with st.expander("View Scheduled Activities"):
            for activity in scheduled_activities:
                activity_id, title, act_type, supplies_text, scheduled_date = activity
                day_name = datetime.datetime.strptime(scheduled_date, '%Y-%m-%d').strftime('%A')
                st.write(f"• **{title}** ({act_type}) - {day_name}")
        
        # Aggregate supplies
        categorized_supplies = aggregate_weekly_supplies(scheduled_activities)
        
        # Display aggregated supplies
        st.markdown("### Aggregated Supply List")
        
        total_items = sum(len(items) for items in categorized_supplies.values())
        st.write(f"**Total unique items:** {total_items}")
        
        # Display by category
        for category, items in categorized_supplies.items():
            with st.expander(f"📦 {category} ({len(items)} items)", expanded=True):
                for item in items:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Show checkbox for print checklist
                        st.checkbox(f"{item['original']}", key=f"supply_check_{item['original']}", value=False)
                    with col2:
                        if item['count'] > 1:
                            st.caption(f"Used in {item['count']} activities")
        
        # Print-friendly view
        st.markdown("---")
        st.markdown("### Print-Friendly Checklist")
        
        if st.button("Generate Printable Supply List"):
            # Create HTML for printing
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Weekly Supply List</title>
                <style>
                    @page {{
                        margin: 1cm;
                        @top-center {{
                            content: "Weekly Supply List";
                            font-size: 10pt;
                        }}
                        @bottom-center {{
                            content: counter(page);
                            font-size: 10pt;
                        }}
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    h1, h2 {{ text-align: center; }}
                    h1 {{ color: #2c3e50; font-size: 24pt; margin-bottom: 10pt; }}
                    h2 {{ color: #34495e; font-size: 16pt; margin-bottom: 20pt; }}
                    h3 {{ 
                        color: #2c3e50; 
                        font-size: 14pt; 
                        margin-top: 20pt;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 5pt;
                    }}
                    .supply-item {{
                        margin: 8px 0;
                        padding: 5px;
                        border-bottom: 1px dotted #ccc;
                    }}
                    .checkbox {{
                        display: inline-block;
                        width: 16px;
                        height: 16px;
                        border: 2px solid #333;
                        margin-right: 10px;
                        vertical-align: middle;
                    }}
                    .supply-name {{
                        vertical-align: middle;
                    }}
                    .multi-use {{
                        color: #e74c3c;
                        font-size: 10pt;
                        font-style: italic;
                    }}
                    .category {{
                        page-break-inside: avoid;
                    }}
                    @media print {{
                        .no-print {{ display: none; }}
                    }}
                </style>
            </head>
            <body>
                <h1>Weekly Supply List</h1>
                <h2>Week of {week_start.strftime('%B %d, %Y')}</h2>
            """
            
            if week_theme:
                html_content += f"""
                <p style="text-align: center; font-style: italic; color: #7f8c8d;">Theme: {week_theme}</p>
                """
            
            # Add activities summary
            html_content += """
                <h3>Scheduled Activities</h3>
                <ul>
            """
            for activity in scheduled_activities:
                activity_id, title, act_type, supplies_text, scheduled_date = activity
                day_name = datetime.datetime.strptime(scheduled_date, '%Y-%m-%d').strftime('%A')
                html_content += f"    <li><strong>{title}</strong> ({act_type}) - {day_name}</li>\n"
            html_content += "</ul>\n"
            
            # Add supplies by category
            html_content += f"""
                <h3>Supply Checklist ({total_items} items)</h3>
            """
            
            for category, items in categorized_supplies.items():
                html_content += f"""
                <div class="category">
                    <h3>{category} ({len(items)} items)</h3>
                """
                for item in items:
                    multi_use = f" <span class='multi-use'>(×{item['count']})</span>" if item['count'] > 1 else ""
                    html_content += f"""
                    <div class="supply-item">
                        <span class="checkbox"></span>
                        <span class="supply-name">{item['original']}{multi_use}</span>
                    </div>
                    """
                html_content += "</div>\n"
            
            html_content += """
            </body>
            </html>
            """
            
            # Configure fonts and generate PDF
            font_config = FontConfiguration()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as html_tmp:
                        html_tmp.write(html_content)
                        html_tmp.flush()
                        
                        HTML(filename=html_tmp.name).write_pdf(
                            tmp.name,
                            font_config=font_config,
                            stylesheets=[CSS(string='''
                                @page { 
                                    margin: 1cm;
                                    size: letter;
                                }
                                body { 
                                    font-family: Arial, sans-serif;
                                    margin: 0;
                                    padding: 0;
                                }
                            ''')]
                        )
                        os.unlink(html_tmp.name)
                    
                    with open(tmp.name, 'rb') as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    os.unlink(tmp.name)
                    
                    st.download_button(
                        label="📥 Download Supply List PDF",
                        data=pdf_bytes,
                        file_name=f"weekly_supplies_{week_start.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            
            # Show preview
            st.markdown("### Preview")
            st.markdown(html_content, unsafe_allow_html=True)

# Add a footer
st.markdown("---")
st.markdown("Created by Mr. Brussow")


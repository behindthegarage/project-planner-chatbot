import os
import json

def load_activities_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def browse_activities(activities):
    index = 0
    total_activities = len(activities)
    print(f"Total activities: {total_activities}")

    while True:
        print(f"Activity {index + 1}/{total_activities}")
        print(f"Title: {activities[index]['Activity Title']}")
        print(f"Type: {activities[index]['Type']}")
        print(f"Description: {activities[index]['Description']}")
        print(f"Supplies: {activities[index]['Supplies']}")
        print(f"Instructions: {activities[index]['Instructions']}\n")

        command = input("Enter 'n' for next, 'p' for previous, or 'q' to quit: ").strip().lower()
        if command == 'n':
            if index < total_activities - 1:
                index += 1
            else:
                print("This is the last activity.")
        elif command == 'p':
            if index > 0:
                index -= 1
            else:
                print("This is the first activity.")
        elif command == 'q':
            break
        else:
            print("Invalid command. Please try again.")

def main():
    file_path = os.getenv('ACTIVITIES_JSON_FILE_PATH', 'data/email_activities.json')
    activities = load_activities_from_json(file_path)
    browse_activities(activities)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quick script to import a .csv project plan into our Shortcut workspace.
"""
#!/usr/bin/env python3
import requests
import csv
import os

# =======================
# CONFIGURATION
# =======================
API_TOKEN = os.getenv("SHORTCUT_TOKEN")  # put your token in env var for safety
BASE_URL = "https://api.app.shortcut.com/api/v3"


# Path to Excel file you exported earlier
EXCEL_FILE = "/Users/brad/Desktop/AI Consulting with Darrin/Project Planning/AI_Project_Plan.csv"

# =======================
# API HELPERS
# =======================
def create_epic(name, description=""):
    url = f"{BASE_URL}/epics"
    headers = {"Shortcut-Token": API_TOKEN, "Content-Type": "application/json"}
    payload = {"name": name, "description": description}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]

def create_story(name, description, story_type, state, epic_id=None):
    url = f"{BASE_URL}/stories"
    headers = {"Shortcut-Token": API_TOKEN, "Content-Type": "application/json"}
    payload = {
        "name": name,
        "description": description,
        "story_type": story_type.lower() if story_type else "feature"
    }
    if epic_id:
        payload["epic_id"] = epic_id
    if state:
        payload["workflow_state_id"] = get_state_id(state)
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]

def get_state_id(state_name):
    # Fetch workflow states once and map them
    url = f"{BASE_URL}/workflows"
    headers = {"Shortcut-Token": API_TOKEN}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    workflows = resp.json()
    # Assuming single workflow, map names
    for workflow in workflows:
        for state in workflow["states"]:
            if state["name"].lower() == state_name.lower():
                return state["id"]
    raise ValueError(f"Workflow state '{state_name}' not found")

# =======================
# MAIN IMPORT
# =======================
def import_from_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        epic_map = {}
        for row in reader:
            name, description, epic, story_type, state = row

            # Ensure epic exists
            epic_id = None
            if epic:
                if epic not in epic_map:
                    epic_id = create_epic(epic)
                    epic_map[epic] = epic_id
                else:
                    epic_id = epic_map[epic]

            # Create story
            story_id = create_story(name, description, story_type, state, epic_id)
            print(f"Created story {story_id} under epic {epic}")

if __name__ == "__main__":
    if not API_TOKEN:
        raise RuntimeError("Set your API token as SHORTCUT_TOKEN environment variable")
    import_from_csv(EXCEL_FILE)

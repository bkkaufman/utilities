#!/usr/bin/env python3
"""
shortcut_to_notion_export.py
-----------------------------------
Exports all Shortcut stories into a Notion-ready CSV file.

Usage:
  1. Ensure your .env file contains: SHORTCUT_API_TOKEN=<your token>
  2. Run:
        python shortcut_to_notion_export.py
  3. The script outputs `shortcut_stories_notion.csv`
     ready to import into Notion as a database table.
"""

import csv
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# -------------------------
# CONFIGURATION
# -------------------------
# Load environment variables from .env file (same as your importer)
load_dotenv()
SHORTCUT_API_TOKEN = os.getenv("SHORTCUT_TOKEN")

BASE_URL = "https://api.app.shortcut.com/api/v3"
OUTPUT_FILE = "shortcut_stories_notion.csv"

# Optional: filter by project or workflow
PROJECT_ID = None  # e.g., 123
WORKFLOW_STATE = None  # e.g., "In Progress"


def fetch_all_stories():
    """Fetch all stories via workflow states."""
    headers = {"Shortcut-Token": SHORTCUT_API_TOKEN, "Content-Type": "application/json"}

    # First, get all workflows
    workflows_url = f"{BASE_URL}/workflows"
    resp = requests.get(workflows_url, headers=headers)

    print(f"Workflows status: {resp.status_code}")

    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        raise Exception(f"Failed to get workflows: {resp.status_code}")

    workflows = resp.json()
    print(f"Found {len(workflows)} workflows")

    all_stories = []

    # For each workflow, get stories in each state
    for workflow in workflows:
        print(f"Checking workflow: {workflow.get('name')}")
        for state in workflow.get('states', []):
            state_id = state.get('id')
            state_name = state.get('name')
            print(f"  Checking state: {state_name} (ID: {state_id})")

            # Try to get stories in this workflow state
            stories_url = f"{BASE_URL}/workflow-states/{state_id}/stories"
            stories_resp = requests.get(stories_url, headers=headers)

            if stories_resp.status_code == 200:
                stories = stories_resp.json()
                print(f"    Found {len(stories)} stories")
                all_stories.extend(stories)
            else:
                print(f"    Status: {stories_resp.status_code}")

    return all_stories



def test_connection():
    """Test if API connection works."""
    headers = {"Shortcut-Token": SHORTCUT_API_TOKEN}
    url = f"{BASE_URL}/members"  # Get workspace members
    resp = requests.get(url, headers=headers)
    print(f"Members endpoint status: {resp.status_code}")
    if resp.status_code == 200:
        members = resp.json()
        print(f"Found {len(members)} workspace members")
        return True
    return False

def story_to_row(story):
    """Convert Shortcut story JSON to Notion-compatible row."""
    def safe(val):
        return val if val else ""

    return {
        "Task Name": safe(story.get("name")),
        "Description": safe(story.get("description")),
        "Status": safe(story.get("workflow_state", {}).get("name")),
        "Epic": safe(story.get("epic", {}).get("name")),
        "Owner": ", ".join(story.get("owner_ids", [])) if story.get("owner_ids") else "",
        "Due Date": safe(story.get("due_date")),
        "Created Date": safe(story.get("created_at")),
        "Updated Date": safe(story.get("updated_at")),
    }


def export_to_csv(stories):
    """Write stories to CSV in Notion-friendly format."""
    fields = [
        "Task Name",
        "Description",
        "Status",
        "Epic",
        "Owner",
        "Due Date",
        "Created Date",
        "Updated Date",
    ]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for story in stories:
            writer.writerow(story_to_row(story))
    print(f"✅ Export complete: {len(stories)} stories → {OUTPUT_FILE}")


def main():
    if not SHORTCUT_API_TOKEN:
        raise SystemExit("❌ Error: SHORTCUT_API_TOKEN not found in environment or .env file.")
    print("📦 Fetching stories from Shortcut...")
    test_connection()
    stories = fetch_all_stories()
    print(f"Fetched {len(stories)} stories.")
    export_to_csv(stories)


if __name__ == "__main__":
    main()

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
KEYWORD = os.getenv('KEYWORD')
SEEK_FILE = os.getenv('SEEK')
LINKEDIN_FILE = os.getenv('LINKEDIN')

def search_seek_jobs():
    # Read the Seek JSON file
    with open(SEEK_FILE, 'r') as file:
        data = json.load(file)

    # Search for the keyword in each job's content sections
    for job in data:
        for section in job['content']['sections']:
            if KEYWORD.lower() in section.lower():
                print(f"Keyword '{KEYWORD}' found in Seek job: {job['jobLink']}")
                break  # Move to the next job after finding a match

def search_linkedin_jobs():
    # Read the LinkedIn JSON file
    with open(LINKEDIN_FILE, 'r') as file:
        jobs = json.load(file)
        # Iterate through each job in the list
        for job in jobs:
            if KEYWORD.lower() in job['description'].lower():
                print(f"Keyword '{KEYWORD}' found in LinkedIn job: {job['jobUrl']}")

def main():
    # Search both job sources
    if os.path.exists(SEEK_FILE):
        search_seek_jobs()
    if os.path.exists(LINKEDIN_FILE):
        search_linkedin_jobs()

if __name__ == "__main__":
    main()

import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize GitHub Client
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN not found in .env")

g = Github(github_token)

def fetch_pr_diff(repo_name: str, pr_number: int) -> str:
    """
    Fetches the changes (diff) for a specific PR.
    Returns a formatted string of the changed files.
    """
    try:
        # Get the repo object
        repo = g.get_repo(repo_name)
        
        # Get the specific PR object
        pr = repo.get_pull(pr_number)
        
        diff_data = ""
        
        # Loop through all files changed in this PR
        for file in pr.get_files():
            # We skip deleted files or non-text files (images/binaries)
            if file.status == "removed":
                continue
                
            # Construct a clear format for the LLM to read
            diff_data += f"--- File: {file.filename} ---\n"
            
            # If there is a patch (the actual diff), add it. 
            # If the file is huge or binary, patch might be None.
            if file.patch:
                diff_data += file.patch + "\n\n"
            else:
                diff_data += "(File content too large or binary, skipped)\n\n"
                
        return diff_data
        
    except Exception as e:
        print(f"Error fetching PR: {e}")
        return ""

# Simple test block to run this file directly
if __name__ == "__main__":
    # REPLACE THIS with the repo/pr number from your terminal log earlier!
    test_repo = "iamgautamraj/CodeGuardian" 
    test_pr_number = 1 
    
    print("Fetching diff...")
    diff = fetch_pr_diff(test_repo, test_pr_number)
    print("--- DIFF START ---")
    print(diff)
    print("--- DIFF END ---")
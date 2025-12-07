import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv

# --- IMPORTS FROM AGENT ---
from agent import run_review_agent, post_github_comment

load_dotenv()

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'), 
        msg=payload_body, 
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

@app.post("/webhook")
async def handle_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    # 1. Read and Verify
    payload_body = await request.body()
    verify_signature(payload_body, x_hub_signature_256)
    
    # 2. Parse Data
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "ping")
    
    # 3. Handle PR Events
    if event_type == "pull_request":
        action = payload.get("action")
        
        # Only run on Open or Update
        if action in ["opened", "synchronize"]:
            pr_number = payload.get("number")
            repo_name = payload["repository"]["full_name"]
            
            print(f"🚀 Starting Review for PR #{pr_number} in {repo_name}...")
            
            # --- A. TRIGGER THE AGENT ---
            review = run_review_agent(repo_name, pr_number)
            
            print(f"✅ Review Generated. Posting to GitHub...")

            # --- B. POST COMMENT ---
            post_github_comment(repo_name, pr_number, review)
            
            return {"status": "ok", "message": "Review posted successfully"}
            
    return {"status": "ok", "message": "Event ignored (not an open/sync PR)"}

@app.get("/")
def read_root():
    return {"message": "CodeGuardian is running!"}
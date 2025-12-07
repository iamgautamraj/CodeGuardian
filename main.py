import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str):
    """
    Verify that the request actually came from GitHub.
    """
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
    # 1. Read the raw body
    payload_body = await request.body()
    
    # 2. Verify security
    verify_signature(payload_body, x_hub_signature_256)
    
    # 3. Parse JSON
    payload = await request.json()
    
    # 4. Check for PR events
    event_type = request.headers.get("X-GitHub-Event", "ping")
    
    if event_type == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload["repository"]["full_name"]
        print(f"✅ Received PR Event! Action: {action}, PR #{pr_number} in {repo_name}")
        
        # TODO: Trigger LangGraph agent here later
        
    return {"status": "ok", "message": "Webhook received successfully"}

@app.get("/")
def read_root():
    return {"message": "CodeGuardian is running!"}
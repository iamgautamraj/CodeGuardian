import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
from mangum import Mangum

# --- IMPORTS FROM AGENT ---
from agent import run_review_agent, post_github_comment

load_dotenv()

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str):
    # Fail closed: without a secret we cannot verify anything.
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Server misconfigured: WEBHOOK_SECRET is not set")

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
            # The agent uses blocking network calls, so run it in a worker
            # thread instead of blocking the event loop.
            try:
                review = await run_in_threadpool(run_review_agent, repo_name, pr_number)
            except Exception as e:
                print(f"❌ Review failed: {e}")
                raise HTTPException(status_code=502, detail="Review generation failed")

            print("✅ Review Generated. Posting to GitHub...")

            # --- B. POST COMMENT ---
            posted = await run_in_threadpool(post_github_comment, repo_name, pr_number, review)
            if not posted:
                raise HTTPException(status_code=502, detail="Review generated but could not be posted to GitHub")

            return {"status": "ok", "message": "Review posted successfully"}

    return {"status": "ok", "message": "Event ignored (not an open/sync PR)"}

@app.get("/")
def read_root():
    return {"message": "CodeGuardian is running!"}

handler = Mangum(app)
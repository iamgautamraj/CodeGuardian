# CodeGuardian: AI Pull Request Reviewer Architecture

## 1. High-Level Flow

```
[GitHub PR event] -> (Webhook, JSON) -> [AWS Lambda Function URL]
    -> [FastAPI app via Mangum] -> [LangGraph workflow] -> [GitHub API: PR comment]
```

## 2. Components

### A. Trigger and ingestion (`main.py`)
* **Source:** GitHub webhook event `pull_request` with action `opened` or `synchronize`. All other events are acknowledged and ignored.
* **Entry point:** `POST /webhook` (FastAPI). `GET /` is a health check.
* **Security:** every request is verified with HMAC SHA-256 (`X-Hub-Signature-256`, constant-time comparison). Requests with a missing or wrong signature get `403`. If `WEBHOOK_SECRET` is not configured the endpoint refuses to process anything.
* **Lambda adapter:** Mangum wraps the FastAPI app so Lambda can serve it.
* **Execution:** the review runs in a worker thread so blocking network calls do not block the event loop.

### B. The review workflow (`agent.py`, LangGraph)
The workflow is a linear graph with two nodes and a shared state (`repo_name`, `pr_number`, `diff`, `review`):

1. **Fetcher node:** uses PyGithub to read the changed files of the PR and builds one diff string (removed files are skipped). Diffs longer than `MAX_DIFF_CHARS` (default 24,000) are truncated, with a marker the model can see.
2. **Analyzer node:** sends the diff to Llama 3.3 70B on Groq (`temperature=0`) with a system prompt covering bugs, security issues and style. The prompt tells the model to treat the diff as untrusted input and not to follow instructions inside it. Output is plain text; "LGTM" if nothing is found.

### C. Publishing (`agent.py`, outside the graph)
`post_github_comment` posts the review as a single general PR comment. If CodeGuardian has already commented on the PR (identified by a header marker), that comment is updated instead of adding a new one on every push. It returns success or failure, and the endpoint returns `502` if posting fails.

### D. Tech stack
* **Runtime:** Python 3.10
* **API framework:** FastAPI + Mangum
* **LLM:** Groq (`llama-3.3-70b-versatile`) via `langchain-groq`
* **Orchestration:** LangGraph / LangChain
* **GitHub access:** PyGithub
* **Deployment:** Docker image on AWS ECR, run as an AWS Lambda function with a Function URL
* **Secrets:** Lambda environment variables (`GITHUB_TOKEN`, `GROQ_API_KEY`, `WEBHOOK_SECRET`); never baked into the image

## 3. Data Flow
1. A developer opens or updates a PR.
2. GitHub sends the JSON payload to the Lambda Function URL.
3. FastAPI verifies the HMAC signature.
4. LangGraph runs the fetch -> analyze pipeline.
5. The review is posted (or updated) as a comment on the PR.

## 4. Known Limitations
* **Synchronous processing:** the review runs inside the webhook request. GitHub expects a response within about 10 seconds, so slow reviews may show as failed deliveries even though the comment is eventually posted. A proper fix is to acknowledge immediately and process through a queue (e.g. SQS) or an asynchronous Lambda invocation. Simple background tasks are not reliable on Lambda because execution can freeze after the response.
* **General comments only:** feedback is one PR comment, not line-level review comments.
* **Large PRs:** diffs over the limit are truncated, so only part of the PR is reviewed.
* **Prompt injection:** the prompt instructs the model to ignore instructions inside the diff, which reduces but does not eliminate the risk.
* **Public Function URL:** the URL has no AWS auth; protection relies on the HMAC signature.

## 5. Roadmap
* Chunking / summarising large diffs per file instead of truncating
* Filtering low-confidence or nitpicky comments before posting
* Line-specific review comments via the GitHub Review API
* Asynchronous processing (queue or async Lambda invocation)
* Custom style guides read from `CONTRIBUTING.md`
* Vector memory of earlier reviews
* Automated tests and a GitHub Actions pipeline
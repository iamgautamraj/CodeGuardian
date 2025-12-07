# CodeGuardian: AI Pull Request Reviewer Architecture

## 1. High-Level Flow
[GitHub Repo] -> (Webhook) -> [FastAPI Server] -> [LangGraph Agent] -> [GitHub API]

## 2. Component Breakdown

### A. The Trigger (Ingestion)
* **Source:** GitHub Webhook event (`pull_request` -> `opened` or `synchronize`).
* **Entry Point:** A FastAPI endpoint (`POST /webhook`).
* **Data:** Receives the PR number, repo name, and commit SHA.

### B. The Brain (LangGraph Orchestrator)
The agent workflow is a Directed Acyclic Graph (DAG) with the following nodes:
1.  **Fetcher Node:** Uses `PyGithub` to fetch the raw "Diff" (changes) from the PR.
2.  **Parser Node:** Chunks the diff. If the file is too huge (>400 lines), it summarizes; otherwise, it passes raw code.
3.  **Review Node (The LLM):**
    * *Input:* Code chunks + Style Guidelines (System Prompt).
    * *Model:* Groq (Llama 3) or Gemini Flash (High context window).
    * *Task:* Identify bugs, security risks, or style violations.
4.  **Filter Node:** Removes "nitpicky" or low-confidence comments to avoid annoying developers.
5.  **Publisher Node:** Posts the surviving comments back to the specific line numbers in the PR using GitHub API.

### C. Tech Stack (Free Tier Optimized)
* **Runtime:** Python 3.10+ (GitHub Codespaces).
* **API Framework:** FastAPI.
* **LLM Provider:** Groq (via `langchain-groq`) for speed/cost.
* **Git Interaction:** PyGithub.
* **Orchestration:** LangGraph.
* **Deployment Target:** AWS Lambda + API Gateway (Event-driven architecture).

## 3. Data Flow
1.  User opens PR.
2.  GitHub sends JSON payload to FastAPI.
3.  FastAPI validates signature (security) and passes payload to LangGraph.
4.  LangGraph executes the review pipeline.
5.  Agent posts comments on GitHub.
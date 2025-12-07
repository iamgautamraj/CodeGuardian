# 🛡️ CodeGuardian: Autonomous AI Pull Request Reviewer

CodeGuardian is an event-driven, serverless AI agent that acts as a first-pass code reviewer for your development team. It hooks directly into GitHub, analyzes Pull Requests (PRs) for bugs, security vulnerabilities, and style violations, and posts constructive feedback instantly.

## 🏗️ Architecture

The system follows a Serverless Event-Driven Architecture. It scales to zero when idle (costing $0) and scales up infinitely to handle concurrent PRs.

graph LR
    User([Developer]) -- Pushes Code --> GitHub
    GitHub -- Webhook (JSON) --> Lambda[AWS Lambda Function]
    
    subgraph "AWS Cloud (Containerized)"
        Lambda --> FastAPI[FastAPI Adapter]
        FastAPI --> Agent[LangGraph Agent]
        
        Agent -- Fetch Diff --> PyGithub[GitHub API]
        Agent -- Analyze Code --> LLM[Groq / Llama 3]
        
        LLM -- Review Feedback --> Agent
    end
    
    Agent -- Post Comment --> GitHubPR[Pull Request]


## 🚀 Key Features

⚡ Zero-Latency Triggers: Powered by GitHub Webhooks and AWS Lambda URLs.

🧠 Intelligent Analysis: Uses Llama 3 (via Groq) to understand code logic, not just syntax (AST analysis).

🔄 Stateful Orchestration: Built with LangGraph to manage the fetch-analyze-review lifecycle.

🔒 Secure: Implements HMAC SHA-256 signature verification to reject unauthorized payloads.

🐳 Containerized: Packaged with Docker for consistent runtime across Dev and Prod.

## 🛠️ Tech Stack

Core Logic: Python 3.10, LangChain, LangGraph

API Framework: FastAPI, Mangum (AWS Adapter)

Infrastructure: AWS Lambda, AWS ECR (Elastic Container Registry)

LLM Provider: Groq (Llama 3.3 Versatile)

DevOps: Docker, GitHub Actions (Future integration)

## 🔧 Setup & Installation

Prerequisites

Python 3.10+

Docker Desktop

AWS CLI (configured)

GitHub Account

### 1. Local Development

Clone the repo and install dependencies:

    git clone [https://github.com/yourusername/CodeGuardian.git](https://github.com/yourusername/CodeGuardian.git)
    cd CodeGuardian
    pip install -r requirements.txt


Create a .env file:

    GITHUB_TOKEN="your_personal_access_token"
    GROQ_API_KEY="your_groq_api_key"
    WEBHOOK_SECRET="your_random_secret_string"''


Run the local server:

    uvicorn main:app --reload


(Use ngrok or GitHub Codespaces to expose port 8000 to the internet for webhook testing)

2. Deploy to AWS (Serverless)

Build and Push the Docker Image:

### Login to AWS ECR
    aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

### Build & Push
    docker build -t code-guardian .
    docker tag code-guardian:latest [your-account-id.dkr.ecr.your-region.amazonaws.com/code-guardian:latest](https://your-account-id.dkr.ecr.your-region.amazonaws.com/code-guardian:latest)
    docker push [your-account-id.dkr.ecr.your-region.amazonaws.com/code-guardian:latest](https://your-account-id.dkr.ecr.your-region.amazonaws.com/code-guardian:latest)


## Lambda Configuration:

Create a Lambda function from the Container Image.

Set Timeout to 60s and Memory to 512MB.

Add the environment variables from your .env.

Enable Function URL (Auth: NONE) and paste it into your GitHub Webhook settings.

## 🔮 Roadmap

[ ] Line-Specific Comments: Migrate from general PR comments to reviewing specific lines of code (GitHub Review API).

[ ] Custom Style Guides: Allow users to upload a CONTRIBUTING.md that the AI reads to enforce specific team rules.

[ ] Vector Memory: Use a Vector DB to remember previous reviews and avoid repeating the same advice.

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT
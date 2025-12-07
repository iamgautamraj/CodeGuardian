import os
from typing import TypedDict, List
from dotenv import load_dotenv
from github import Github

# LangChain / LangGraph Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

# --- 1. SETUP API CLIENTS ---
# GitHub
github_token = os.getenv("GITHUB_TOKEN")
g = Github(github_token)

# LLM (Groq - Llama 3)
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile", 
    groq_api_key=groq_api_key
)

# --- 2. DEFINE STATE ---
# This dictionary carries data between nodes
class AgentState(TypedDict):
    repo_name: str
    pr_number: int
    diff: str
    review: str

# --- 3. DEFINE NODES ---

def fetch_diff_node(state: AgentState):
    """
    Node 1: Fetches the PR diff from GitHub
    """
    print(f"--- Node 1: Fetching Diff for PR #{state['pr_number']} ---")
    repo = g.get_repo(state["repo_name"])
    pr = repo.get_pull(state["pr_number"])
    
    diff_data = ""
    for file in pr.get_files():
        if file.status == "removed":
            continue
        diff_data += f"--- File: {file.filename} ---\n"
        if file.patch:
            diff_data += file.patch + "\n\n"
            
    return {"diff": diff_data}

def analyze_code_node(state: AgentState):
    """
    Node 2: Asks Llama 3 to review the code
    """
    print("--- Node 2: Analyzing Code with Llama 3 ---")
    
    # The Prompt Engineering part
    system_prompt = """You are a Senior Software Engineer doing a code review.
    Analyze the provided Git Diff.
    Focus on:
    1. Bugs or logic errors.
    2. Security vulnerabilities.
    3. Code style issues (PEP8 for Python).
    
    If the code looks good, just say "LGTM" (Looks Good To Me).
    Be concise and professional.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Here is the diff:\n\n{diff}")
    ])
    
    # Chain: Prompt -> LLM -> String Output
    chain = prompt | llm | StrOutputParser()
    
    review_result = chain.invoke({"diff": state["diff"]})
    
    return {"review": review_result}

# --- 4. BUILD THE GRAPH ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("fetcher", fetch_diff_node)
workflow.add_node("analyzer", analyze_code_node)

# Add edges (The flow logic)
workflow.set_entry_point("fetcher")      # Start here
workflow.add_edge("fetcher", "analyzer") # Go to analyzer
workflow.add_edge("analyzer", END)       # Finish

# Compile
app = workflow.compile()

def run_review_agent(repo_name: str, pr_number: int):
    """
    Wrapper function to run the graph from the API.
    Returns the review string.
    """
    input_state = {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "diff": "",
        "review": ""
    }
    result = app.invoke(input_state)
    return result["review"]

# --- 5. TEST IT LOCALLY ---
if __name__ == "__main__":
    # Use your real repo details again
    test_input = {
        "repo_name": "iamgautamraj/CodeGuardian", 
        "pr_number": 1,
        "diff": "",   # Empty initially
        "review": ""  # Empty initially
    }
    
    print("🚀 Starting Agent Workflow...")
    result = app.invoke(test_input)
    
    print("\n✅ WORKFLOW FINISHED!")
    print("================ REVIEW RESULTS ================")
    print(result["review"])
    print("================================================")
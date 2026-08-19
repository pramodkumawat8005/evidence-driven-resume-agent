from langgraph.graph import StateGraph ,START,END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Optional, Literal,Annotated
import json
from pathlib import Path
from pydantic import BaseModel,Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from jinja2 import Template
from langgraph.types import interrupt, Command
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import requests
from langchain_core.tools import BaseTool,tool
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import threading
import aiosqlite
import os
from states import MainState,RepoAnalysis,PersonalRepoData,JDData
from prompts import jd_parser,RepoAnalysis_prompt
from extract_repo_code import extract_relevant_repositories,extract_single_repo
from analyze_repo_adaptively import analyze_repo_adaptively
load_dotenv()

# ==========================================================
# Async Loop
# ==========================================================


_ASYNC_LOOP = asyncio.new_event_loop()


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(
    target=start_loop,
    args=(_ASYNC_LOOP,),
    daemon=True,
).start()


def submit_async_task(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return submit_async_task(coro).result()

# ==========================================================
# API Keys
# ==========================================================

groq_api_key = os.getenv("GROQ_API_KEY")
openrouter_api_key = os.getenv("openrouter_api_key")
github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# ==========================================================
# LLM
# ==========================================================
model = ChatOpenAI(
    model="dots-studio/dots-3-note-preview:free",
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)
model1 = ChatGroq(
      model="openai/gpt-oss-120b",
      api_key=groq_api_key,
      )

model1 = ChatGoogleGenerativeAI(
     model="gemini-2.5-flash",
     api_key=GEMINI_API_KEY,
 )
# ==========================================================
# tools
# ==========================================================
@tool
def get_all_repositories():

    """
    Fetch all repositories of the authenticated GitHub user.
    Uses the GitHub REST API /user/repos endpoint with authentication and automatically handles pagination.
    Returns a list of repository names accessible to the authenticated user.
    
    """
    url = "https://api.github.com/user/repos"

    headers = {
        "Authorization": f"Bearer {github_access_token}",
        "Accept": "application/vnd.github+json"
    }

    repositories = []
    page = 1

    while True:
        params = {
            "per_page": 100,
            "page": page,
            "affiliation": "owner,collaborator,organization_member"
        }

        response = requests.get(
            url,
            headers=headers,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            break

        repositories.extend(data)
        page += 1

    return repositories


# ==========================================================
# MCP Client
# ==========================================================

client = MultiServerMCPClient(
    {
        "github": {
            "transport": "streamable_http",
            "url": "https://api.githubcopilot.com/mcp/", 
            "headers": { 
                "Authorization": f"Bearer {github_access_token}" 
            }, 
        } 
    } 
) 
 
# ========================================================== 
# Allowed GitHub Tools 
# ========================================================== 
 
GITHUB_TOOLS = { 
    "get_me", 
    "search_repositories", 
    "get_file_contents", 
    "search_code", 
    "list_commits", 
    "get_commit", 
    "search_commits", 
    "list_branches", 
    "list_pull_requests", 
    "pull_request_read", 
    "list_issues", 
    "issue_read", 
    "list_tags", 
    "list_releases", 
    "get_latest_release", 
} 
 
 
# ========================================================== 
# Load MCP Tools 
# ========================================================== 
 
def load_mcp_tools() -> list[BaseTool]: 
    try: 
        all_tools = run_async(client.get_tools()) 
 
        filtered_tools = [ 
            tool 
            for tool in all_tools 
            if tool.name in GITHUB_TOOLS 
        ] 
 
        print(f"Loaded {len(filtered_tools)} GitHub tools") 
 
        return filtered_tools 
 
    except Exception as e: 
        print("Failed to load MCP tools:", e) 
        return [] 
 
 
mcp_tools = load_mcp_tools() 
tools = [get_all_repositories, *mcp_tools] 
 
llm_with_tools = ( 
    model.bind_tools(tools) 
    if tools 
    else model 
) 

# ========================================================== 
# Node 
# ========================================================== 
def Jd_parser(state: MainState) -> dict:

    jd_text = state["jd_text"]

    Jd_prompt = jd_parser.format(
        jd_text=jd_text
    )
    print(f"First model call for JD parsing")
    structured_jd_model = model.with_structured_output(JDData)

    modelresponse = structured_jd_model.invoke(Jd_prompt)

    return {
        "JDData": modelresponse
    }
async def get_github_profile(state: MainState) -> dict:
    repositories = await get_all_repositories.ainvoke({})

    profile_repo_url = ""

    for repo in repositories:
        name = repo.get("name", "").lower()
        description = (repo.get("description") or "").lower()
        topics = [t.lower() for t in repo.get("topics", [])]

        profile_keywords = [
            "profile",
            "portfolio",
            "cv",
            "about-me",
            "personal",
            "portfolio-website",
        ]

        text = f"{name}"

        if any(keyword in text for keyword in profile_keywords):
            profile_repo_url = repo.get("html_url", "")
            print(f"Found profile repository: {profile_repo_url}")
            break
    
    return {
        "profile_reponame": profile_repo_url
    }

async def get_user_info(state: MainState) -> dict:

    profile_repo_url = state["profile_reponame"]

    
    # MCP tools
    get_file_contents_tool = next(
        t for t in mcp_tools
        if t.name == "get_file_contents"
    )

    repo_data = await extract_single_repo(
                repo_url=profile_repo_url,
                get_file_contents_tool=get_file_contents_tool
            )

    prompt = RepoAnalysis_prompt.format(
        repo_data=repo_data,
    )
    print(f"Second model call for personal repo analysis")
    structured_model = model.with_structured_output(PersonalRepoData)

    response: PersonalRepoData = await structured_model.ainvoke(prompt)
    print(response)

    return {
        "PersonalRepoData": response
    }
 

async def get_relevant_repos(state: MainState) -> dict:

    repositories = await get_all_repositories.ainvoke({})
    jd_data =state["JDData"]

    job_title = jd_data.job_title.lower()
    

    relevant_repos = []

    # Job title ke basis par keywords
    job_keywords = set(
        job_title.replace("-", " ").replace("/", " ").split()
    )

    for repo in repositories:

        name = repo.get("name", "").lower()
        description = (repo.get("description") or "").lower()
        topics = [
            topic.lower()
            for topic in repo.get("topics", [])
        ]
        language = (repo.get("language") or "").lower()

        text = f"{name} {description} {' '.join(topics)} {language}"

        # Direct job-title keyword matching
        score = sum(
            1 for keyword in job_keywords
            if keyword in text
        )

        # Technology-specific matching
        tech_keywords = {
            "python": ["python", "django", "flask", "fastapi"],
            "java": ["java", "spring", "hibernate", "jpa"],
            "developer": ["api", "backend", "web", "django", "fastapi"],
            "backend": ["api", "django", "flask", "fastapi", "backend"],
            "ai": ["ai", "llm", "langchain", "langgraph", "rag"],
            "ml": ["machine-learning", "ml", "tensorflow", "pytorch"],
            "data": ["pandas", "numpy", "data", "analytics"],
        }

        for job_keyword in job_keywords:
            for tech in tech_keywords.get(job_keyword, []):
                if tech in text:
                    score += 2

        if score > 0:
            relevant_repos.append({
                "url": repo.get("html_url", ""),
                "name": repo.get("name", ""),
                "score": score,
            })

    # Highest relevant repositories first
    relevant_repos.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    return {
        "relevant_repo_urls": [
            repo["url"]
            for repo in relevant_repos
        ]
    }

async def extract_github_repositories(
    state: MainState
) -> dict:

    repo_urls = state["relevant_repo_urls"]

    repo_code_data = await extract_relevant_repositories(
        relevant_repo_urls=repo_urls,
        mcp_tools=mcp_tools
    )
    return {
        "repo_code_data": repo_code_data
    }

async def analyze_github_repositories(
    state: MainState
) -> dict:

    repo_code_data = state["repo_code_data"]

    repo_analyses = []

    # repo_code_data is a LIST
    for repo_data in repo_code_data:

        try:

            # -----------------------------------------
            # Repository information
            # -----------------------------------------

            repo_name = repo_data["repo"]

            repo_url = repo_data.get("repo_url","")

            # -----------------------------------------
            # Extract files
            # -----------------------------------------

            files = {}

            for file_data in repo_data.get("files", []):

                file_path = file_data.get("path","")

                content = file_data.get("content","")

                if file_path:
                    files[file_path] = content

            print(f"\n{'=' * 60}")

            print(f"Analyzing repository: {repo_name}")

            print(f"Files found: {len(files)}")

            # -----------------------------------------
            # Adaptive analysis
            # Small repo  -> Direct LLM
            # Large repo  -> Map Reduce
            # -----------------------------------------

            analysis = await analyze_repo_adaptively(
                repo_name=repo_name,
                files=files
            )

            # -----------------------------------------
            # Add GitHub URL to projects if required
            # -----------------------------------------

            analysis_dict = analysis.model_dump()

            for project in analysis_dict.get("projects", []):

                if not project.get("github"):
                    project["github"] = repo_url

            repo_analyses.append(analysis_dict)

            print(f"\nAnalysis for {repo_name}:")
            print(analysis_dict)

        except Exception as e:

            print(f"\nError analyzing "
                f"{repo_data.get('repo', 'unknown repo')}: {e}"
            )

    return {
        "RepoAnalysis": repo_analyses
    }


# ========================================================== 
# Tool Node 
# ========================================================== 
 
tool_node = ToolNode( 
    tools, 
    handle_tool_errors=True, 
) if tools else None 
 
 
# ========================================================== 
# Checkpointer 
# ========================================================== 
 
async def create_checkpointer(): 
    conn = await aiosqlite.connect("chatbot.db") 
    return AsyncSqliteSaver(conn) 
 
 
checkpointer = run_async(create_checkpointer()) 
 
# ========================================================== 
# Graph 
# ========================================================== 
 
graph = StateGraph(MainState) 
 
graph.add_node("jd_analysis", Jd_parser) 
graph.add_node("get_github_profile", get_github_profile)
graph.add_node("get_user_info", get_user_info)
graph.add_node("get_relevant_repos", get_relevant_repos)
graph.add_node("extract_github_repositories", extract_github_repositories)
graph.add_node("analyze_github_repositories", analyze_github_repositories)

graph.add_edge(START, "jd_analysis")
graph.add_edge("jd_analysis", "get_github_profile")
graph.add_edge("get_github_profile", "get_user_info")
graph.add_edge("get_user_info", "get_relevant_repos")
graph.add_edge("get_relevant_repos", "extract_github_repositories")
graph.add_edge("extract_github_repositories", "analyze_github_repositories")
graph.add_edge("analyze_github_repositories", END)

workflow = graph.compile( 
    checkpointer=checkpointer, 
) 
# ========================================================== 
# Helper Functions 
# ========================================================== 
 
async def _retrieve_threads(): 
 
    thread_ids = [] 
 
    async for checkpoint in checkpointer.alist(None): 
 
        tid = checkpoint.config["configurable"]["thread_id"] 
 
        if tid not in thread_ids: 
            thread_ids.append(tid) 
 
    return thread_ids 
 
 
def retrieve_all_threads(): 
    return run_async(_retrieve_threads()) 
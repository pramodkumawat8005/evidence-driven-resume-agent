from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import requests
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_core.tools import BaseTool
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from dotenv import load_dotenv

import asyncio
import threading
import aiosqlite
import os

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

groq_api_key = os.getenv("groq_api_key")
github_access_token = os.getenv("github_access_token")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================================
# LLM
# ==========================================================

# model = ChatGroq(
#      model="llama-3.3-70b-versatile",
#      api_key=groq_api_key,
#      )

model = ChatGoogleGenerativeAI(
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
        for tool in all_tools:
          if tool.name in ["search_code", "get_file_contents"]:
            print("\n==============================")
            print("TOOL:", tool.name)
            print("DESCRIPTION:", tool.description)

            print("ARGS:")
            print(tool.args)

            print("ARGS_SCHEMA:")
            print(tool.args_schema)
        
        filtered_tools = [ 
            tool 
            for tool in all_tools 
            
            #if tool.name in GITHUB_TOOLS 
        ] 
        for tool in filtered_tools:
            print(tool.name)
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
# State 
# ========================================================== 
 
class ChatState(TypedDict): 
    messages: Annotated[list[BaseMessage], add_messages] 
 
 
# ========================================================== 
# System Prompt 
# ========================================================== 
 
SYSTEM_PROMPT = SystemMessage( 
    content=""" 
You are a helpful AI assistant. 
 
Rules: 
 
1. Answer normally whenever possible. 
 
2. Only use GitHub tools when the user explicitly asks about: 
   - repositories 
   - commits 
   - branches 
   - pull requests 
   - issues 
   - releases 
   - files 
   - their GitHub account 
 
3. Never invent tool names. 
 
4. If no tool is required, answer directly. 
 
5. If a tool fails, explain the error politely. 
""" 
) 
 
# ========================================================== 
# Chat Node 
# ========================================================== 
 
async def chat_node(state: ChatState): 
    response = await llm_with_tools.ainvoke( 
        [SYSTEM_PROMPT, *state["messages"]] 
    ) 
 
    return {"messages": [response]} 
 
 
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
 
graph = StateGraph(ChatState) 
 
graph.add_node("chat", chat_node) 
 
graph.add_edge(START, "chat") 
 
if tools: 
 
    tool_node = ToolNode( 
        tools, 
        handle_tool_errors=True, 
    ) 
 
    graph.add_node("tools", tool_node) 
 
    graph.add_conditional_edges( 
        "chat", 
        tools_condition, 
    ) 
 
    graph.add_edge( 
        "tools", 
        "chat", 
    ) 
 
else: 
 
    graph.add_edge( 
        "chat", 
        END, 
    ) 
 
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
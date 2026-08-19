# import os
# from typing import List, Dict, Any


# # ---------------------------------------------------------
# # Folders jo skills/project understanding ke liye useful nahi
# # ---------------------------------------------------------

# IGNORED_DIRS = {
#     ".git",
#     ".github",
#     ".gitignore",
#     ".idea",
#     ".vscode",

#     "__pycache__",
#     ".pytest_cache",

#     "node_modules",
#     "venv",
#     ".venv",
#     "env",

#     "dist",
#     "build",
#     ".next",

#     "coverage",

#     "vendor",
# }


# # ---------------------------------------------------------
# # Files jinka content normally useful nahi hota
# # ---------------------------------------------------------

# IGNORED_FILES = {
#     "package-lock.json",
#     "yarn.lock",
#     "pnpm-lock.yaml",
#     "poetry.lock",
# }


# # ---------------------------------------------------------
# # Important documentation/config files
# # ---------------------------------------------------------

# IMPORTANT_FILES = {
#     "README.md",
#     "README.txt",
#     "requirements.txt",
#     "pyproject.toml",
#     "setup.py",
#     "setup.cfg",

#     "Dockerfile",
#     "docker-compose.yml",
#     "docker-compose.yaml",

#     ".env.example",
#     "main.py",
#     "app.py",

#     "manage.py",
# }


# # ---------------------------------------------------------
# # Important source-code extensions
# # ---------------------------------------------------------

# IMPORTANT_EXTENSIONS = {
#     ".py",
#     ".js",
#     ".jsx",
#     ".ts",
#     ".tsx",

#     ".java",
#     ".go",
#     ".rs",

#     ".cpp",
#     ".c",

#     ".php",

#     ".sql",

#     ".html",
#     ".css",

#     ".md",

#     ".json",
#     ".yaml",
#     ".yml",
#     ".toml",
# }


# def is_ignored_path(path: str) -> bool:

#     parts = path.replace("\\", "/").split("/")

#     # ignored directories
#     for part in parts:
#         if part in IGNORED_DIRS:
#             return True

#     # ignored files
#     filename = os.path.basename(path)

#     if filename in IGNORED_FILES:
#         return True

#     return False


# def is_important_file(path: str) -> bool:

#     filename = os.path.basename(path)

#     # Explicit important files
#     if filename in IMPORTANT_FILES:
#         return True

#     # Extension based
#     _, extension = os.path.splitext(filename)

#     return extension.lower() in IMPORTANT_EXTENSIONS

# print(is_important_file("main.py"))
# print(is_important_file("README.md"))
# print(is_important_file("manage.py"))
# print(is_important_file("main.yaml"))

from dotenv import load_dotenv
import os

from groq import Groq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()
openrouter_api_key = os.getenv("openrouter_api_key")
groq_api_key = os.getenv("GROQ_API_KEY")
github_access_token = os.getenv("github_access_token")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

models = client.models.list()

for model in models.data:
    print(model.id)
# ==========================================================
# LLM
# ==========================================================

# model = ChatGroq(
#       model="llama-3.3-70b-versatile",
#       api_key=groq_api_key,
#       )


# repo_model = model.invoke("Say hello")
# print(f"Repo model response: {repo_model}")
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="openrouter/free",
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

response = model.invoke("Hello")
print(response.content)
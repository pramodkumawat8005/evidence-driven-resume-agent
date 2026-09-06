import os
from typing import List, Dict, Any


# ---------------------------------------------------------
# Folders jo skills/project understanding ke liye useful nahi
# ---------------------------------------------------------

IGNORED_DIRS = {
    ".git",
    ".github",
    ".gitignore",
    ".idea",
    ".vscode",
    "__pycache__",
    "__pycache__",
    ".pytest_cache",

    "node_modules",
    "venv",
    ".venv",
    "env",

    "dist",
    "build",
    ".next",

    "coverage",

    "vendor",
    "lib",
    "scss",
    "img",
    "images",
    "templates",
}


# ---------------------------------------------------------
# Files jinka content normally useful nahi hota
# ---------------------------------------------------------

IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "prompts.py",
    
}


# ---------------------------------------------------------
# Important documentation/config files
# ---------------------------------------------------------

IMPORTANT_FILES = {
    "README.md",
    "README.txt",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",

    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",

    ".env.example",
    "main.py",
    "app.py",
    "manage.py",
}


# ---------------------------------------------------------
# Important source-code extensions
# ---------------------------------------------------------

IMPORTANT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",

    ".java",
    ".go",
    ".rs",

    ".cpp",
    ".c",

    ".php",

    ".sql",


    ".md",

    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


def is_ignored_path(path: str) -> bool:

    parts = path.replace("\\", "/").split("/")

    # ignored directories
    for part in parts:
        if part in IGNORED_DIRS:
            return True

    # ignored files
    filename = os.path.basename(path)

    if filename in IGNORED_FILES:
        return True

    return False


def is_important_file(path: str) -> bool:

    filename = os.path.basename(path)

    # Explicit important files
    if filename in IMPORTANT_FILES:
        return True

    # Extension based
    _, extension = os.path.splitext(filename)

    return extension.lower() in IMPORTANT_EXTENSIONS



import json
import asyncio


# ... IGNORED_DIRS, IGNORED_FILES, IMPORTANT_FILES, IMPORTANT_EXTENSIONS
# ... is_ignored_path, is_important_file  (ye sab same rahenge, unchanged)

# Concurrency control — GitHub API rate limits se bachne ke liye
MAX_CONCURRENT_REQUESTS = 8
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def _call_with_semaphore(coro):
    async with _semaphore:
        return await coro


async def extract_single_repo(
    repo_url: str,
    get_file_contents_tool
) -> Dict[str, Any]:

    parts = repo_url.rstrip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]

    print("\n" + "=" * 70)
    print(f"PROCESSING REPOSITORY: {owner}/{repo}")
    print("=" * 70)

    folder_structure = []
    important_files = []
    extracted_files = []
    visited_dirs = set()

    # -----------------------------------------------------
    # Directory traversal — ab subdirectories parallel me traverse hoti hain
    # -----------------------------------------------------

    async def traverse_directory(path: str = "/"):

        normalized_path = path.rstrip("/") or "/"

        if normalized_path in visited_dirs:
            return
        visited_dirs.add(normalized_path)

        try:
            response = await _call_with_semaphore(
                get_file_contents_tool.ainvoke({
                    "owner": owner,
                    "repo": repo,
                    "path": normalized_path,
                    "fields": ["type", "name", "path", "size", "sha"]
                })
            )
        except Exception as e:
            print(f"ERROR reading directory {normalized_path}: {e}")
            return

        # ---- MCP wrapper unwrap (same as before) ----
        if isinstance(response, list):
            if len(response) == 1 and isinstance(response[0], dict):
                wrapper = response[0]
                if wrapper.get("type") == "text":
                    text = wrapper.get("text", "")
                    try:
                        response = json.loads(text)
                    except json.JSONDecodeError:
                        response = []
        elif isinstance(response, dict):
            if "text" in response:
                try:
                    response = json.loads(response["text"])
                except json.JSONDecodeError:
                    response = []
            else:
                response = (
                    response.get("entries")
                    or response.get("files")
                    or response.get("content")
                    or []
                )

        if not isinstance(response, list):
            return

        subdirectory_tasks = []

        for item in response:

            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            item_path = item.get("path", "")

            if not item_path or is_ignored_path(item_path):
                continue

            if item_type == "dir":
                folder_structure.append({"path": item_path, "type": "directory"})
                print(f"[DIR ] {item_path}")

                # sequentially await na karke, task banao — baad me sath gather karenge
                subdirectory_tasks.append(traverse_directory(item_path))

            elif item_type in ("file", "blob"):
                folder_structure.append({"path": item_path, "type": "file"})

                if not is_important_file(item_path):
                    continue

                important_files.append(item_path)
                print(f"[FILE] {item_path}")

        # ---- sab subdirectories ek sath parallel traverse ----
        if subdirectory_tasks:
            await asyncio.gather(*subdirectory_tasks)

    await traverse_directory("/")

    print(f"\nImportant files found: {len(important_files)}")

    # -----------------------------------------------------
    # File content extraction — ab sab files parallel me fetch hoti hain
    # -----------------------------------------------------

    async def extract_file(file_path: str):

        try:
            response = await _call_with_semaphore(
                get_file_contents_tool.ainvoke({
                    "owner": owner,
                    "repo": repo,
                    "path": file_path
                })
            )

            content = ""

            if isinstance(response, str):
                content = response

            elif isinstance(response, dict):
                content = response.get("content") or response.get("text") or ""

            elif isinstance(response, list):
                for item in response:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") != "text":
                        continue
                    text = item.get("text", "")
                    if text.startswith("successfully downloaded"):
                        continue
                    if text.strip():
                        content = text
                        break

            if not content.strip():
                print(f"No content found for {file_path}")
                return None

            _, extension = os.path.splitext(file_path)

            print(f"Successfully extracted {file_path} ({len(content)} characters)")

            return {
                "path": file_path,
                "extension": extension.lower(),
                "content": content,
            }

        except Exception as e:
            print(f"ERROR extracting {file_path}: {e}")
            return None

    # sab important files ek sath fetch karo
    results = await asyncio.gather(*(extract_file(fp) for fp in important_files))

    extracted_files = [r for r in results if r is not None]

    return {
        "repo_url": repo_url,
        "owner": owner,
        "repo": repo,
        "folder_structure": folder_structure,
        "important_files": important_files,
        "files": extracted_files,
    }


async def extract_relevant_repositories(
    relevant_repo_urls: List[str],
    mcp_tools
) -> List[Dict[str, Any]]:

    get_file_contents_tool = next(
        (tool for tool in mcp_tools if tool.name == "get_file_contents"),
        None
    )

    if get_file_contents_tool is None:
        raise RuntimeError("get_file_contents MCP tool nahi mila.")

    async def process_repo(repo_url: str):
        try:
            return await extract_single_repo(
                repo_url=repo_url,
                get_file_contents_tool=get_file_contents_tool
            )
        except Exception as e:
            print(f"FAILED repository {repo_url}: {e}")
            return None

    # ---- sab repos ek sath parallel process ----
    results = await asyncio.gather(*(process_repo(url) for url in relevant_repo_urls))

    all_repositories = [r for r in results if r is not None]

    return all_repositories
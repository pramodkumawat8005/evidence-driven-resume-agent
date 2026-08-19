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
}


# ---------------------------------------------------------
# Files jinka content normally useful nahi hota
# ---------------------------------------------------------

IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
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

    ".html",
    ".css",

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


async def extract_single_repo(
    repo_url: str,
    get_file_contents_tool
) -> Dict[str, Any]:

    """
    Ek GitHub repository ka:

    - complete folder structure discover karta hai
    - important files identify karta hai
    - important files ka complete code extract karta hai
    """

    # -----------------------------------------------------
    # URL → owner/repo
    # -----------------------------------------------------

    parts = repo_url.rstrip("/").split("/")

    owner = parts[-2]
    repo = parts[-1]

    print("\n" + "=" * 70)
    print(f"PROCESSING REPOSITORY: {owner}/{repo}")
    print("=" * 70)

    # -----------------------------------------------------
    # Results
    # -----------------------------------------------------

    folder_structure = []

    important_files = []

    extracted_files = []

    visited_dirs = set()

    # -----------------------------------------------------
    # Recursive directory traversal
    # -----------------------------------------------------

    async def traverse_directory(path: str = "/"):

        normalized_path = path.rstrip("/") or "/"

        # Prevent accidental loops
        if normalized_path in visited_dirs:
            return

        visited_dirs.add(normalized_path)

        try:

            response = await get_file_contents_tool.ainvoke({
                "owner": owner,
                "repo": repo,
                "path": normalized_path,
                "fields": [
                    "type",
                    "name",
                    "path",
                    "size",
                    "sha"
                ]
            })

        except Exception as e:

            print(
                f"ERROR reading directory "
                f"{normalized_path}: {e}"
            )

            return

        # -------------------------------------------------
        # Directory response
        # -------------------------------------------------
        import json

        

        # MCP wrapper ko unwrap karo
        if isinstance(response, list):

            # Example:
            # [{"type": "text", "text": "[{...}, {...}]"}]

            if len(response) == 1 and isinstance(response[0], dict):
                wrapper = response[0]

                if wrapper.get("type") == "text":
                    text = wrapper.get("text", "")

                    try:
                        response = json.loads(text)
                    except json.JSONDecodeError:
                        response = []

        # Agar dict wrapper directly mila ho
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

        # Safety
        if not isinstance(response, list):
          return

        # Process actual GitHub entries
        for item in response:

            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            item_path = item.get("path", "")
            item_name = item.get("name", "")
           
            if not item_path:
                continue

            # ---------------------------------------------
            # Ignore unwanted directories/files
            # ---------------------------------------------

            if is_ignored_path(item_path):
                continue

            # ---------------------------------------------
            # Directory
            # ---------------------------------------------

            if item_type == "dir":

                folder_structure.append({
                    "path": item_path,
                    "type": "directory",
                })

                print(
                    f"[DIR ] {item_path}"
                )

                await traverse_directory(item_path)

            # ---------------------------------------------
            # File
            # ---------------------------------------------
            
            elif item_type == "file" or item_type == "blob":

                folder_structure.append({
                    "path": item_path,
                    "type": "file",
                })

                # Only important files
               
                if not is_important_file(item_path):
                    continue

                important_files.append(item_path)

                print(
                    f"[FILE] {item_path}"
                )

    # -----------------------------------------------------
    # Start traversal
    # -----------------------------------------------------

    await traverse_directory("/")

    print(
        f"\nImportant files found: "
        f"{len(important_files)}"
    )

    # -----------------------------------------------------
    # Extract complete content
    # -----------------------------------------------------

    for file_path in important_files:

     try:

        response = await get_file_contents_tool.ainvoke({
            "owner": owner,
            "repo": repo,
            "path": file_path
        })

        # =================================================
        # Extract actual text from MCP response
        # =================================================

        content = ""

        if isinstance(response, str):

            content = response

        elif isinstance(response, dict):

            content = (
                response.get("content")
                or response.get("text")
                or ""
            )

        elif isinstance(response, list):

            for item in response:

                if not isinstance(item, dict):
                    continue

                if item.get("type") != "text":
                    continue

                text = item.get("text", "")

                # Status message skip karo
                if text.startswith("successfully downloaded"):
                    continue

                # Ye actual file content hai
                if text.strip():
                    content = text
                    break

        # =================================================
        # Empty file skip
        # =================================================

        if not content.strip():
            print(f"No content found for {file_path}")
            continue

        _, extension = os.path.splitext(file_path)

        extracted_files.append({
            "path": file_path,
            "extension": extension.lower(),
            "content": content,
        })

        print(
            f"Successfully extracted {file_path} "
            f"({len(content)} characters)"
        )

     except Exception as e:

        print(
            f"ERROR extracting {file_path}: {e}"
        )

    # -----------------------------------------------------
    # Final repository result
    # -----------------------------------------------------

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

    """
    Multiple relevant repositories process karta hai.

    Har repo ko sequentially:
        discover → filter → extract
    karta hai.
    """

    get_file_contents_tool = next(
        (
            tool
            for tool in mcp_tools
            if tool.name == "get_file_contents"
        ),
        None
    )
    
    if get_file_contents_tool is None:

        raise RuntimeError(
            "get_file_contents MCP tool nahi mila."
        )

    all_repositories = []

    # -----------------------------------------------------
    # Process repositories one by one
    # -----------------------------------------------------

    for repo_url in relevant_repo_urls:

        try:

            repo_data = await extract_single_repo(
                repo_url=repo_url,
                get_file_contents_tool=get_file_contents_tool
            )

            all_repositories.append(repo_data)

        except Exception as e:

            print(
                f"FAILED repository {repo_url}: {e}"
            )

    return all_repositories
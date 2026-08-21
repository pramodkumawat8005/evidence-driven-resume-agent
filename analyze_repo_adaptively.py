
from states import RepoAnalysis,MainState,FileBatchAnalysis
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY1")
groq_api_key = os.getenv("GROQ_API_KEY")
openrouter_api_key = os.getenv("openrouter_api_key1")
model1 = ChatOpenAI(
    model="openrouter/free",
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)
model1 = ChatGroq(
      model="llama-3.3-70b-versatile",
      api_key=groq_api_key,
      )
model = ChatGoogleGenerativeAI(
     model="gemini-2.5-flash",
     api_key=GEMINI_API_KEY,
 )
structured_llm = model.with_structured_output(RepoAnalysis)

def build_repo_text(repo_name: str, files: dict) -> str:

    sections = []

    for file_path, content in files.items():

        sections.append(
            f"""
==============================
FILE: {file_path}
==============================

{content}
"""
        )

    return f"""
REPOSITORY: {repo_name}

{''.join(sections)}
"""


def build_direct_repo_prompt(repo_name: str, files: dict):

    repo_text = build_repo_text(repo_name, files)

    return f"""
You are a senior software engineer analyzing a GitHub repository.

Your task is to extract ONLY information that is actually supported
by the repository code.

Do NOT hallucinate technologies, features or achievements.

Repository:
{repo_name}

Repository files:
{repo_text}

Analyze:

1. What is this project?
2. What technologies are actually used?
3. What frameworks/libraries are used?
4. What databases are used?
5. What AI/ML technologies are used?
6. What cloud/devops technologies are used?
7. What important features does the project implement?
8. What projects/features could be mentioned on a resume?
9. Provide evidence from the code whenever possible.

Return the result according to the RepoAnalysis schema.
"""
async def direct_repo_analysis(
    repo_name: str,
    files: dict
) -> RepoAnalysis:

    prompt = build_direct_repo_prompt(
        repo_name,
        files
    )

    result = await structured_llm.ainvoke(prompt)

    return result



def chunk_files(
    files: dict,
    batch_size: int = 4
):

    items = list(files.items())

    for i in range(0, len(items), batch_size):

        yield dict(
            items[i:i + batch_size]
        )


batch_llm = model.with_structured_output(
    FileBatchAnalysis
)

async def analyze_file_batch(
    repo_name: str,
    files: dict
) -> FileBatchAnalysis:

    repo_text = build_repo_text(
        repo_name,
        files
    )

    prompt = f"""
You are analyzing part of a GitHub repository.

Repository:
{repo_name}

Files:

{repo_text}

Extract only information directly supported
by these files.

Focus on:

- programming languages
- frameworks
- libraries
- databases
- AI/ML
- cloud
- DevOps
- tools
- important features
- project functionality
- implementation evidence

Do NOT invent information.

Return structured data.
"""

    return await batch_llm.ainvoke(prompt)


async def reduce_repo_analysis(
    repo_name: str,
    batch_results: list[FileBatchAnalysis]
) -> RepoAnalysis:

    summaries = "\n\n".join(
        result.model_dump_json()
        for result in batch_results
    )

    prompt = f"""
You are the final repository analysis agent.

Repository:
{repo_name}

Below are analyses generated from different groups
of files from the SAME repository.

{summaries}

Combine them into ONE accurate repository analysis.

Rules:

1. Remove duplicate skills.
2. Merge duplicate projects/features.
3. Do not invent anything.
4. Only include technologies supported by evidence.
5. Preserve important implementation details.
6. Focus on information useful for resume generation.
7. Return RepoAnalysis.
"""

    return await structured_llm.ainvoke(prompt)

async def analyze_repo_adaptively(
    repo_name: str,
    files: dict
) -> RepoAnalysis:

    # -----------------------------------------
    # Combined repository content
    # -----------------------------------------

    total_chars = sum(
        len(content)
        for content in files.values()
    )

    # Rough token estimation
    estimated_tokens = total_chars // 4

    print(
        f"\nRepo: {repo_name}"
        f"\nFiles: {len(files)}"
        f"\nCharacters: {total_chars}"
        f"\nEstimated tokens: {estimated_tokens}"
    )

    # -----------------------------------------
    # SMALL CONTEXT
    # -----------------------------------------

    SAFE_TOKEN_LIMIT = 12000

    if estimated_tokens <= SAFE_TOKEN_LIMIT:

        print(
            f"Using DIRECT analysis for {repo_name}"
        )

        return await direct_repo_analysis(
            repo_name,
            files
        )

    # -----------------------------------------
    # LARGE CONTEXT
    # -----------------------------------------

    print(
        f"Using MAP-REDUCE analysis for {repo_name}"
    )

    batch_results = []

    for batch_number, batch in enumerate(
        chunk_files(files, batch_size=4),
        start=1
    ):

        print(
            f"Analyzing batch {batch_number} "
            f"for {repo_name}"
        )

        result = await analyze_file_batch(
            repo_name,
            batch
        )

        batch_results.append(result)

    # -----------------------------------------
    # REDUCE
    # -----------------------------------------

    print(
        f"Reducing {len(batch_results)} "
        f"batch results for {repo_name}"
    )

    final_analysis = await reduce_repo_analysis(
        repo_name,
        batch_results
    )

    return final_analysis
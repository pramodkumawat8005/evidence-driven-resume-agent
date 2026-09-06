from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import os
import uuid

from main import workflow


app = FastAPI(
    title="JD to Resume AI",
    version="1.0.0"
)


# -----------------------------------------
# Static files
# -----------------------------------------

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# -----------------------------------------
# Serve UI
# -----------------------------------------

@app.get("/")
async def serve_ui():

    return FileResponse(
        "static/index.html"
    )


# -----------------------------------------
# Request Model
# -----------------------------------------

class ResumeRequest(BaseModel):

    jd_text: str


# -----------------------------------------
# Generate Resume
# -----------------------------------------

@app.post("/generate-resume")
async def generate_resume(
    request: ResumeRequest
):

    if not request.jd_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Job Description is required."
        )

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state = {
        "jd_text": request.jd_text.strip()
    }

    try:

        result = await workflow.ainvoke(
            initial_state,
            config=config
        )

        if not result:

            raise HTTPException(
                status_code=500,
                detail="Workflow returned no result."
            )

        pdf_path = result.get(
            "output_pdf_path"
        )

        if not pdf_path:

            raise HTTPException(
                status_code=500,
                detail="PDF path not returned."
            )

        if not os.path.exists(pdf_path):

            raise HTTPException(
                status_code=500,
                detail="Generated PDF does not exist."
            )

        filename = os.path.basename(
            pdf_path
        )

        return {
            "success": True,
            "message": "Resume generated successfully.",
            "download_url": f"/download/{filename}"
        }

    except Exception as e:

        print(
            "Resume generation error:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------------
# Download PDF
# -----------------------------------------

@app.get("/download/{filename}")
async def download_resume(
    filename: str
):

    pdf_path = os.path.join(
        "output",
        filename
    )

    if not os.path.exists(pdf_path):

        raise HTTPException(
            status_code=404,
            detail="Resume file not found."
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename
    )
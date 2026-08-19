import os
import uuid
import streamlit as st
import asyncio
from main import workflow


# ----------------------------------------------------
# Page Config
# ----------------------------------------------------

st.set_page_config(
    page_title="JD to Resume",
    page_icon="📄",
    layout="wide"
)


# ----------------------------------------------------
# Session
# ----------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "config" not in st.session_state:
    st.session_state.config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


# ----------------------------------------------------
# UI
# ----------------------------------------------------

st.title("📄 JD to Resume")

st.write(
    "Paste a Job Description. The agent will analyze the JD, "
    "analyze your GitHub repositories, fetch your resume content, "
    "and generate a tailored resume."
)


jd = st.text_area(
    "Paste Job Description",
    height=300,
    placeholder="Paste the complete Job Description here..."
)


# ----------------------------------------------------
# Generate Resume
# ----------------------------------------------------

if st.button(
    "🚀 Generate Tailored Resume",
    use_container_width=True
):

    if not jd.strip():
        st.error("Please paste Job Description.")
        st.stop()

    os.makedirs("temp", exist_ok=True)

    initial_state = {
        "jd_text": jd.strip()
    }

    try:

        with st.spinner(
            "Analyzing JD → GitHub → Resume → Generating PDF..."
        ):

            result = asyncio.run(
                workflow.ainvoke(
                  initial_state,
                        config=st.session_state.config
                    )
)

        # ------------------------------------------------
        # Result
        # ------------------------------------------------

        if not result:
            st.error("Agent returned no result.")
            st.stop()

        # ------------------------------------------------
        # PDF
        # ------------------------------------------------

        # pdf_path = result.get("output_pdf_path")

        # if pdf_path and os.path.exists(pdf_path):

        #     st.success(
        #         "✅ Tailored Resume Generated Successfully!"
        #     )

        #     with open(pdf_path, "rb") as f:

        #         st.download_button(
        #             label="⬇️ Download Tailored Resume",
        #             data=f.read(),
        #             file_name="Tailored_Resume.pdf",
        #             mime="application/pdf",
        #             use_container_width=True
        #         )

        # else:

        #     st.warning(
        #         "Agent completed, but PDF path was not found."
        #     )

        # ------------------------------------------------
        # Agent Analysis
        # ------------------------------------------------

        

    except Exception as e:

        st.error("❌ Resume generation failed.")

        st.exception(e)
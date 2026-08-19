import queue
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from main import (
    chatbot,
    retrieve_all_threads,
    submit_async_task,
)

# ==========================================================
# Page Config
# ==========================================================

st.set_page_config(
    page_title="GitHub MCP Chatbot",
    page_icon="🤖",
    layout="wide",
)

# ==========================================================
# Custom CSS
# ==========================================================

st.markdown("""
<style>

.block-container{
    padding-top:1.5rem;
}

[data-testid="stSidebar"]{
    background:#111827;
}

.chat-title{
    font-size:30px;
    font-weight:700;
    color:#2563eb;
}

.thread-btn button{
    width:100%;
    text-align:left;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# Helper Functions
# ==========================================================


def new_thread():
    return str(uuid.uuid4())


def extract_text(content):

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        output = []

        for block in content:

            if isinstance(block, dict):

                if block.get("type") == "text":
                    output.append(block.get("text", ""))

            else:
                output.append(str(block))

        return "".join(output)

    return str(content)


def load_history(thread_id):

    state = chatbot.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    history = []

    for msg in state.values.get("messages", []):

        if isinstance(msg, HumanMessage):
            history.append(
                {
                    "role": "user",
                    "content": msg.content,
                }
            )

        elif isinstance(msg, AIMessage):
            history.append(
                {
                    "role": "assistant",
                    "content": extract_text(msg.content),
                }
            )

    return history


def get_thread_title(thread_id):

    try:

        state = chatbot.get_state(
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        msgs = state.values.get("messages", [])

        for m in msgs:

            if isinstance(m, HumanMessage):
                text = m.content.replace("\n", " ")

                if len(text) > 35:
                    text = text[:35] + "..."

                return text

    except Exception:
        pass

    return "New Chat"


# ==========================================================
# Session State
# ==========================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = new_thread()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "threads" not in st.session_state:
    st.session_state.threads = retrieve_all_threads()

if st.session_state.thread_id not in st.session_state.threads:
    st.session_state.threads.append(st.session_state.thread_id)

# ==========================================================
# Sidebar
# ==========================================================

with st.sidebar:

    st.title("🤖 GitHub MCP")

    st.caption("AI GitHub Assistant")

    if st.button("➕ New Chat", use_container_width=True):

        st.session_state.thread_id = new_thread()
        st.session_state.messages = []
        st.session_state.threads.append(
            st.session_state.thread_id
        )
        st.rerun()

    st.divider()

    st.subheader("History")

    for thread in reversed(st.session_state.threads):

        title = get_thread_title(thread)

        if thread == st.session_state.thread_id:
            label = f"🟢 {title}"
        else:
            label = f"💬 {title}"

        if st.button(
            label,
            key=thread,
            use_container_width=True,
        ):

            st.session_state.thread_id = thread
            st.session_state.messages = load_history(thread)
            st.rerun()

# ==========================================================
# Header
# ==========================================================

st.markdown(
    '<div class="chat-title">🤖 GitHub MCP Chatbot</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Ask anything about GitHub repositories, issues, pull requests, workflows and code."
)

st.divider()

# ==========================================================
# Previous Messages
# ==========================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================================
# Chat Input
# ==========================================================

prompt = st.chat_input("Ask GitHub MCP...")

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }

    with st.chat_message("assistant"):

        spinner = st.empty()

        spinner.info("Thinking...")

        def stream():

            q = queue.Queue()

            async def runner():

                try:

                    async for chunk, meta in chatbot.astream(

                        {
                            "messages": [
                                HumanMessage(content=prompt)
                            ]
                        },

                        config=config,
                        stream_mode="messages",

                    ):

                        q.put(chunk)

                except Exception as e:
                    q.put(e)

                finally:
                    q.put(None)

            submit_async_task(runner())

            while True:

                item = q.get()

                if item is None:
                    break

                if isinstance(item, Exception):
                    yield f"❌ {item}"
                    return

                if isinstance(item, AIMessage):

                    text = extract_text(item.content)

                    if text:
                        yield text

        spinner.empty()

        response = st.write_stream(stream())

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )
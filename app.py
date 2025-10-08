import os
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from memory import load_system_messages, InMemorySaver
from agent import create_mcp_agent, invoke_mcp_agent

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------
load_dotenv()

def abs_path(rel: str) -> str:
    return str((Path(__file__).parent / rel).resolve())

st.set_page_config(page_title="🤖 MCP Chat", layout="centered", page_icon="🤖")
st.title("🤖 MCP Agent Chat")

# Custom CSS for chat bubbles
st.markdown(
    """
    <style>
    .user-message {
        background-color:#DCF8C6;
        padding:10px;
        border-radius:10px;
        margin-bottom:5px;
        max-width:80%;
    }
    .agent-message {
        background-color:#F1F0F0;
        padding:10px;
        border-radius:10px;
        margin-bottom:5px;
        max-width:80%;
    }
    .timestamp {
        font-size:10px;
        color:gray;
        text-align:right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# Initialize MCP Agent
# ------------------------------------------------------------
async def initialize_agent():
    try:
        servers = {
            "xml": {"transport": "stdio", "command": "python", "args": [abs_path("servers/xml_server.py")]},
            "csv": {"transport": "streamable_http", "url": "http://127.0.0.1:8002/mcp"},
            "math": {"transport": "stdio", "command": "python", "args": [abs_path("servers/math_server.py")]},
            "files": {"transport": "stdio", "command": "python", "args": [abs_path("servers/files_server.py")]},
            "cartoon": {"transport": "stdio", "command": "python", "args": [abs_path("servers/prompt_server.py")]},
            "postgres": {"transport": "stdio", "command": "python", "args": [abs_path("servers/postgres_server.py")]},
            "kart": {"url": "http://127.0.0.1:8001/mcp", "transport": "streamable_http"},
        }

        client = MultiServerMCPClient(servers)
        tools = await client.get_tools()

        checkpointer = InMemorySaver()
        agent = create_mcp_agent(tools, checkpointer)
        system_messages = await load_system_messages(client, servers)

        return agent, system_messages, checkpointer
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None, None, None

# ------------------------------------------------------------
# Display messages with styled bubbles and timestamp
# ------------------------------------------------------------
def display_message(message, is_user: bool):
    css_class = "user-message" if is_user else "agent-message"
    timestamp = datetime.now().strftime("%H:%M")
    st.markdown(
        f'<div class="{css_class}">{message}</div>'
        f'<div class="timestamp">{timestamp}</div>',
        unsafe_allow_html=True
    )

# ------------------------------------------------------------
# Chat + File Upload Interface
# ------------------------------------------------------------
async def chat_ui():
    if "agent" not in st.session_state:
        with st.spinner("Starting MCP agent..."):
            agent, system_messages, checkpointer = await initialize_agent()
            if not agent:
                st.stop()
            st.session_state.agent = agent
            st.session_state.system_messages = system_messages
            st.session_state.checkpointer = checkpointer
            st.session_state.messages = []

    agent = st.session_state.agent
    system_messages = st.session_state.system_messages
    checkpointer = st.session_state.checkpointer
    messages = st.session_state.messages

    # --------------------------
    # File Upload Section
    # --------------------------
    uploaded_file = st.file_uploader("📄 Upload a document to summarize", type=["txt", "md", "pdf"])
    if uploaded_file:
        try:
            file_content = uploaded_file.read().decode("utf-8", errors="ignore")
            user_msg = HumanMessage(content=f"[Uploaded file] {uploaded_file.name}")
            st.session_state.messages.append(user_msg)
            display_message(f"Uploaded file: {uploaded_file.name}", is_user=True)

            with st.spinner("Summarizing file..."):
                summary = await invoke_mcp_agent(
                    agent,
                    system_messages,
                    {"tool": "summarize_document", "tool_input": {"document_content": file_content}},
                    checkpointer
                )
                display_message(summary, is_user=False)
                st.session_state.messages.append(AIMessage(content=summary))
        except Exception as e:
            st.error(f"Error reading file: {e}")

    # --------------------------
    # Display chat history
    # --------------------------
    for msg in messages:
        display_message(msg.content, is_user=isinstance(msg, HumanMessage))

    # --------------------------
    # Chat input
    # --------------------------
    if prompt := st.chat_input("Type your message..."):
        user_msg = HumanMessage(content=prompt)
        st.session_state.messages.append(user_msg)
        display_message(prompt, is_user=True)

        # Agent response (non-streaming)
        with st.spinner("Agent is typing..."):
            try:
                response_text = await invoke_mcp_agent(agent, system_messages, user_msg, checkpointer)
                display_message(response_text, is_user=False)
                st.session_state.messages.append(AIMessage(content=response_text))
            except Exception as e:
                st.error(f"Error: {e}")

# ------------------------------------------------------------
# Run Streamlit Async
# ------------------------------------------------------------
def run_async():
    asyncio.run(chat_ui())

if __name__ == "__main__":
    run_async()

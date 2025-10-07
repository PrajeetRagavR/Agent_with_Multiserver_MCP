import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage

import streamlit as st

from memory import load_system_messages, InMemorySaver
from agent import create_mcp_agent, invoke_mcp_agent

load_dotenv()

def abs_path(rel: str) -> str:
    return str((Path(__file__).parent / rel).resolve())

st.set_page_config(layout="wide")
st.title("MCP Agent UI")

# @st.cache_resource
async def initialize_agent():
    try:
        servers = {
            "math": {
                "transport": "stdio",
                "command": "python",
                "args": [abs_path("servers/math_server.py")],
            },
            "files": {
                "transport": "stdio",
                "command": "python",
                "args": [abs_path("servers/files_server.py")],
            },
            "cartoon": {
            "transport": "stdio",
            "command": "python",
            "args": [abs_path("servers/prompt_server.py")],
            },
            "postgres": {
                "transport": "stdio",
                "command": "python",
                "args": [abs_path("servers/postgres_server.py")],
            },
            "kart": {
                "url": "http://127.0.0.1:8001/mcp",  # Replace with the remote server's URL
                "transport": "streamable_http"
            }
        }

        client = MultiServerMCPClient(servers)
        try:
            tools = await client.get_tools()
        except Exception as e:
            import traceback
            st.error(f"Could not load tools from MCP client: {e}")
            st.error(traceback.format_exc())
            tools = []
        checkpointer = InMemorySaver()
        agent = create_mcp_agent(tools, checkpointer)

        system_messages = await load_system_messages(client, servers)
        return agent, system_messages, checkpointer
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return None, None, None

async def main():
    if "agent" not in st.session_state:
        st.session_state.agent, st.session_state.system_messages, st.session_state.checkpointer = await initialize_agent()

    agent = st.session_state.agent
    system_messages = st.session_state.system_messages
    checkpointer = st.session_state.checkpointer

    if agent is None:
        return

    uploaded_file = st.file_uploader("Upload a document to summarize", type=["txt", "md", "pdf"])
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            try:
                file_content = uploaded_file.read().decode("latin-1")
            except UnicodeDecodeError:
                st.error("Could not decode the file. Please ensure it's a text file with UTF-8 or Latin-1 encoding.")
                return
        with st.spinner("Summarizing document..."):
            summary = await invoke_mcp_agent(agent, system_messages, {"tool": "summarize_document", "tool_input": {"document_content": file_content}}, checkpointer)
            st.subheader("Document Summary:")
            st.write(summary)

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Load chat history if available
    if st.session_state.agent: # Ensure agent is initialized
        try:
            # Get the state from the agent, which uses the checkpointer internally
            state = st.session_state.agent.get_state(config={"configurable": {"thread_id": "1"}})
            if state and state.values["messages"]:
                st.session_state.messages = state.values["messages"]
        except Exception as e:
            st.warning(f"Could not load chat history: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message.type):
            st.markdown(message.content)

    if prompt := st.chat_input("Enter your query here..."):
        st.session_state["messages"].append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            user_message = HumanMessage(content=prompt)
            full_response = await invoke_mcp_agent(agent, system_messages, user_message, checkpointer)
            message_placeholder.markdown(full_response)
        st.session_state["messages"].append(AIMessage(content=full_response))

if __name__ == "__main__":
    asyncio.run(main())
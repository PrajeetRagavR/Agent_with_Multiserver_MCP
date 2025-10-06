import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

from memory import load_system_messages, InMemorySaver
from agent import create_mcp_agent, invoke_mcp_agent

load_dotenv()


def abs_path(rel: str) -> str:
    return str((Path(__file__).parent / rel).resolve())


async def main():
    # ---------------------------
    # Define MCP servers
    # ---------------------------
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
        }
    }

    client = MultiServerMCPClient(servers)

    # ---------------------------
    # Load tools from all servers
    # ---------------------------
    tools = await client.get_tools()
    checkpointer = InMemorySaver()
    agent = create_mcp_agent(tools, checkpointer)

    # ---------------------------
    # Load and inject resources
    # ---------------------------
    system_messages = await load_system_messages(client, servers)

    # ---------------------------
    # Example 1: Math calculation
    # ---------------------------
    user_math_msg = {
        "role": "user",
        "content": "Compute (3 + 5) * pi using available tools, and show steps.",
    }
    math_result_content = await invoke_mcp_agent(agent, system_messages, user_math_msg, checkpointer)
    print("\n[MATH RESULT]\n", math_result_content)

    # ---------------------------
    # Example 2: File operations
    # ---------------------------

    read_msg = {"role": "user", "content": "Read the file at tmp/demo.txt"}
    read_result_content = await invoke_mcp_agent(agent, system_messages, read_msg, checkpointer)
    print("\n[READ RESULT]\n", read_result_content)

    list_msg = {"role": "user", "content": "List files under tmp/."}
    list_result_content = await invoke_mcp_agent(agent, system_messages, list_msg, checkpointer)
    print("\n[LIST RESULT]\n", list_result_content)

    # ---------------------------
    # Example 3: Using prompts
    # ---------------------------
    explain_prompt_messages = await client.get_prompt(
        "math",
        "explain_calculation",
        arguments={"expression": "(3 + 5) * pi", "result": "25.132741228718345"},
    )
    math_explanation_content = await invoke_mcp_agent(agent, system_messages, explain_prompt_messages, checkpointer)
    print("\n[MATH EXPLANATION]\n", math_explanation_content)

    file_content = (Path("tmp/demo.txt").read_text(encoding="utf-8")
                    if Path("tmp/demo.txt").exists() else "No file found")
    file_summary_prompt = await client.get_prompt(
        "files",
        "summarize_file",
        arguments={"file_content": file_content},
    )
    file_summary_content = await invoke_mcp_agent(agent, system_messages, file_summary_prompt, checkpointer)
    print("\n[FILE SUMMARY]\n", file_summary_content)

    # ---------------------------
    # Example 4: Using cartoon prompts
    # ---------------------------
    cartoon_explainer_prompt_messages = await client.get_prompt(
        "cartoon",
        "cartoon_explainer",
        arguments={"name": "spongeBob"},
    )
    cartoon_explainer_content = await invoke_mcp_agent(agent, system_messages, cartoon_explainer_prompt_messages, checkpointer)
    print("\n[CARTOON EXPLANATION]\n", cartoon_explainer_content)

    # ---------------------------
    # Example 5: Using postgres server
    # ---------------------------
    list_tables_prompt_messages = await client.get_prompt(
        "postgres",
        "list_tables",
    )
    list_tables_content = await invoke_mcp_agent(agent, system_messages, list_tables_prompt_messages, checkpointer)
    print("\n[POSTGRES LIST TABLES]\n", list_tables_content)


if __name__ == "__main__":
    asyncio.run(main())

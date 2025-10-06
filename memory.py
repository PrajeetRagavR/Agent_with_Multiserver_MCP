import json
import logging
from typing import List, Dict
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver


# -----------------------------------------------------------
# Setup basic logging for debugging and observability
# -----------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# -----------------------------------------------------------
# Load system messages dynamically from connected MCP servers
# -----------------------------------------------------------
async def load_system_messages(
    client: MultiServerMCPClient,
    servers: Dict[str, dict],
) -> List[BaseMessage]:
    """
    Loads system messages from all connected MCP servers.

    Args:
        client: MultiServerMCPClient instance for MCP communication
        servers: Dict of server_name -> config (can be empty or contain server metadata)

    Returns:
        List[BaseMessage]: SystemMessage objects containing resource data or errors
    """
    system_messages = []

    for server_name in servers.keys():
        try:
            logger.info(f"Fetching resources from MCP server: {server_name}")
            resources = await client.get_resources(server_name)

            for res in resources:
                try:
                    # MCP Resource may contain content under `.contents`
                    raw = res.contents[0].text if hasattr(res, "contents") else str(res)
                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        parsed = raw

                    system_messages.append(
                        SystemMessage(
                            content=f"[{server_name}] Resource: {parsed}"
                        )
                    )
                except Exception as inner_e:
                    logger.warning(
                        f"Error processing resource from {server_name}: {inner_e}"
                    )
                    system_messages.append(
                        SystemMessage(
                            content=f"Error processing resource from {server_name}: {inner_e}"
                        )
                    )

        except Exception as e:
            logger.error(f"Failed to load resources from {server_name}: {e}")
            system_messages.append(
                SystemMessage(
                    content=f"Error loading resources from {server_name}: {e}"
                )
            )

    return system_messages


# -----------------------------------------------------------
# In-memory message history saver (default LangGraph memory)
# -----------------------------------------------------------
def get_message_history() -> InMemorySaver:
    """
    Returns an in-memory saver for LangGraph conversation state.
    You can later replace this with a persistent backend (Redis, SQLite, etc.)
    """
    return InMemorySaver()

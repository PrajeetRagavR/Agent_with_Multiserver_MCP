from mcp.server.fastmcp import FastMCP
from pathlib import Path
from langchain_core.messages import HumanMessage

mcp = FastMCP("Files")
BASE = Path(".").resolve()

# =========================
# 🛠 TOOLS
# =========================
@mcp.tool()
def list_dir(rel_path: str = ".") -> list[str]:
    """List files and folders in a given directory."""
    p = (BASE / rel_path).resolve()
    if BASE not in p.parents and p != BASE:
        raise ValueError("Path escape not allowed")
    if not p.exists() or not p.is_dir():
        raise ValueError("Not a directory")
    return [entry.name for entry in p.iterdir()]

@mcp.tool()
def read_file(rel_path: str) -> str:
    """Read a file's contents."""
    p = (BASE / rel_path).resolve()
    if BASE not in p.parents and p != BASE:
        raise ValueError("Path escape not allowed")
    if not p.exists() or not p.is_file():
        raise ValueError("Not a file")
    return p.read_text(encoding="utf-8")

@mcp.tool()
def write_file(rel_path: str, content: str) -> str:
    """Write text to a file."""
    p = (BASE / rel_path).resolve()
    if BASE not in p.parents and p != BASE:
        raise ValueError("Path escape not allowed")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {p}"

@mcp.tool()
def summarize_document(document_content: str) -> str:
    """Summarize the content of an uploaded document."""
    messages = summarize_file_prompt(document_content)
    # Assuming summarize_file_prompt returns a list with one HumanMessage
    if messages and isinstance(messages[0], HumanMessage):
        return messages[0].content
    return "Could not summarize document."


# =========================
# 📦 RESOURCES
# =========================
@mcp.resource("file://tmp")
def tmp_directory_listing() -> list[str]:
    """Expose the tmp/ directory as a resource."""
    tmp_dir = BASE / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    return [entry.name for entry in tmp_dir.iterdir()]


# =========================
# 🧠 PROMPTS
# =========================
@mcp.prompt("summarize_file")
def summarize_file_prompt(file_content: str):
    """
    Prompt to summarize file contents concisely.
    """
    return [
        HumanMessage(
            content=(
                "You are a file summarizer.\n"
                "Here is the file content:\n\n"
                f"{file_content}\n\n"
                "Provide a short summary (max 3 sentences):"
            )
        )
    ]


if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"Error running files_server: {e}")

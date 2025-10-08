# ======================================================
# 📁 CSV MCP Server with NLP Integration
# ======================================================
from fastmcp import FastMCP
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import pandas as pd
import os
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
from dotenv import load_dotenv
# from fastapi import FastAPI # Removed FastAPI import

load_dotenv()

# ======================================================
# ⚙️ Setup
# ======================================================
mcp = FastMCP("CSVServer")
BASE = Path("C:/ValueHealth/Training/mcp/data/csv").resolve()  # All CSV files live here
BASE.mkdir(parents=True, exist_ok=True)

# app = FastAPI() # Removed FastAPI app instantiation
# app.mount("/", mcp.http_app()) # Removed app.mount call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-based concurrency control for I/O
csv_executor = ThreadPoolExecutor(max_workers=3)
csv_semaphore = asyncio.Semaphore(2)

# Initialize LLM
llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=os.getenv("GROQ_API_KEY"), temperature=0)

# ======================================================
# 🛠 Helper Functions
# ======================================================
def _get_csv_path(file_name: str) -> Path:
    """Ensure safe path within BASE directory."""
    p = (BASE / file_name).resolve()
    if BASE not in p.parents:
        raise ValueError("Path escape not allowed")
    if not p.exists():
        raise FileNotFoundError(f"CSV file '{file_name}' not found.")
    return p

def _read_csv_sync(file_path: Path) -> pd.DataFrame:
    return pd.read_csv(file_path)

def _write_csv_sync(df: pd.DataFrame, file_path: Path):
    df.to_csv(file_path, index=False)

# ======================================================
# 🧰 TOOLS
# ======================================================

@mcp.tool()
async def list_csv_files() -> list[str]:
    """List all CSV files in the base directory."""
    return [f.name for f in BASE.glob("*.csv")]

@mcp.tool()
async def read_csv(file_name: str, limit: int = 10) -> list[dict]:
    """Read first few rows of a CSV file."""
    async with csv_semaphore:
        loop = asyncio.get_event_loop()
        file_path = _get_csv_path(file_name)
        df = await loop.run_in_executor(csv_executor, _read_csv_sync, file_path)
        return df.head(limit).to_dict(orient="records")

@mcp.tool()
async def describe_csv(file_name: str) -> dict:
    """Describe CSV columns and types."""
    async with csv_semaphore:
        loop = asyncio.get_event_loop()
        file_path = _get_csv_path(file_name)
        df = await loop.run_in_executor(csv_executor, _read_csv_sync, file_path)
        return {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "rows": len(df)
        }

@mcp.tool()
async def insert_row(file_name: str, row: dict) -> str:
    """Insert a new row into a CSV."""
    async with csv_semaphore:
        loop = asyncio.get_event_loop()
        file_path = _get_csv_path(file_name)
        df = await loop.run_in_executor(csv_executor, _read_csv_sync, file_path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        await loop.run_in_executor(csv_executor, _write_csv_sync, df, file_path)
        return f"✅ Row inserted into '{file_name}'."

@mcp.tool()
async def delete_rows(file_name: str, condition: str) -> str:
    """
    Delete rows matching a condition.
    Example: condition='Age > 50' or 'Name == \"John\"'
    """
    async with csv_semaphore:
        loop = asyncio.get_event_loop()
        file_path = _get_csv_path(file_name)

        def delete_task():
            df = pd.read_csv(file_path)
            before = len(df)
            df = df.query(f"not ({condition})")
            df.to_csv(file_path, index=False)
            after = len(df)
            return before - after

        deleted = await loop.run_in_executor(csv_executor, delete_task)
        return f"🗑️ Deleted {deleted} rows from '{file_name}'."

@mcp.tool()
async def update_rows(file_name: str, condition: str, updates: dict) -> str:
    """
    Update rows matching a condition.
    Example: condition='Name == \"Alice\"', updates={'Age': 30}
    """
    async with csv_semaphore:
        loop = asyncio.get_event_loop()
        file_path = _get_csv_path(file_name)

        def update_task():
            df = pd.read_csv(file_path)
            df.loc[df.eval(condition), list(updates.keys())] = list(updates.values())
            df.to_csv(file_path, index=False)
            return len(df[df.eval(condition)])

        updated = await loop.run_in_executor(csv_executor, update_task)
        return f"✏️ Updated {updated} rows in '{file_name}'."

@mcp.tool()
async def display_csv(file_name: str, limit: int = 50):
    """Display rows of a CSV file."""
    return await read_csv(file_name, limit)

# ======================================================
# 🧠 NLP → CSV Tool (Natural Language to CSV Operation)
# ======================================================
@mcp.tool()
async def nlp2csv(file_name: str, user_request: str) -> str:
    """
    Interpret a natural language request and perform a CSV operation.
    Example: "Show me all rows where age > 40"
    """
    file_path = _get_csv_path(file_name)
    df = pd.read_csv(file_path)

    schema_info = ", ".join([f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)])
    prompt = (
        f"You are a data manipulation assistant for CSV files.\n"
        f"The CSV '{file_name}' has columns: {schema_info}.\n"
        f"The user request is:\n'{user_request}'\n\n"
        f"Generate a valid pandas operation or filter code snippet "
        f"that fulfills this request. Only return code (no explanation)."
    )

    code = llm(messages=[HumanMessage(content=prompt)]).content.strip()
    logger.info(f"Generated code: {code}")

    try:
        # Evaluate generated pandas expression safely
        local_vars = {"df": df}
        exec(code, {}, local_vars)
        if "df" in local_vars:
            df_result = local_vars["df"]
            df_result.to_csv(file_path, index=False)
            return f"✅ Operation applied successfully to '{file_name}'."
        elif "result" in local_vars:
            result = local_vars["result"]
            return str(result.head(10).to_dict(orient='records'))
        else:
            return "⚠️ No valid operation result found."
    except Exception as e:
        logger.error(f"Error executing LLM code: {e}")
        return f"❌ Failed to execute generated operation: {e}"

# ======================================================
# 📦 RESOURCES
# ======================================================
@mcp.resource("csv://files")
def csv_resource() -> list[str]:
    """Expose available CSV files as a resource."""
    return [f.name for f in BASE.glob("*.csv")]

# ======================================================
# 🧠 PROMPTS
# ======================================================
@mcp.prompt("csv_summary")
def csv_summary_prompt(csv_content: str):
    """Prompt to summarize CSV file contents."""
    return [
        HumanMessage(
            content=f"You are a data analyst. Summarize the following CSV content:\n\n{csv_content[:2000]}"
        )
    ]

# ======================================================
# ▶️ Run the MCP Server
# ======================================================
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)

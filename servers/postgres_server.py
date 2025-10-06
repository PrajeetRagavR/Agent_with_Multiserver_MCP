from mcp.server.fastmcp import FastMCP
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ======================================================
# 🚀 MCP Initialization
# ======================================================
mcp = FastMCP("PostgresMCP")

# ======================================================
# ⚙️ Database Configuration
# ======================================================
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "testdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

# ======================================================
# 🔧 Logging
# ======================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================
# 🔌 Database Helper
# ======================================================
def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ======================================================
# 🧩 Schema Caching
# ======================================================
SCHEMA_CACHE = {}

def get_table_schema(table_name: str):
    """Cache table schema for faster introspection."""
    if table_name in SCHEMA_CACHE:
        return SCHEMA_CACHE[table_name]
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s;
            """, (table_name,))
            schema = cur.fetchall()
            SCHEMA_CACHE[table_name] = schema
            return schema
    except Exception as e:
        logger.error(f"Failed to get schema for {table_name}: {e}")
        return []

# ======================================================
# 🧰 TOOLS
# ======================================================

@mcp.tool()
def list_tables() -> list[str]:
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [row["table_name"] for row in cur.fetchall()]
            logger.info(f"Tables: {tables}")
            return tables
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return []

@mcp.tool()
def describe_table(table_name: str):
    try:
        return get_table_schema(table_name)
    except Exception as e:
        logger.error(f"describe_table failed: {e}")
        return []

@mcp.tool()
def insert_row(table_name: str, data: dict) -> str:
    try:
        cols = ", ".join(data.keys())
        vals = ", ".join(["%s"] * len(data))
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});", tuple(data.values()))
            conn.commit()
        SCHEMA_CACHE.pop(table_name, None)
        return f"✅ Inserted row into '{table_name}'."
    except Exception as e:
        logger.error(f"Insert failed: {e}")
        return f"❌ Failed to insert row: {e}"

@mcp.tool()
def read_rows(table_name: str, limit: int = 10):
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} LIMIT %s;", (limit,))
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Read failed: {e}")
        return []

@mcp.tool()
def update_rows(table_name: str, updates: dict, where: str) -> str:
    try:
        set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where};", tuple(updates.values()))
            conn.commit()
        return f"✅ Updated rows in '{table_name}' where {where}."
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"❌ Update failed: {e}"

@mcp.tool()
def delete_rows(table_name: str, where: str) -> str:
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table_name} WHERE {where};")
            conn.commit()
        return f"🗑️ Deleted rows from '{table_name}' where {where}."
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return f"❌ Delete failed: {e}"

@mcp.tool()
def display_table(table_name: str, limit: int = 50):
    """Display table contents safely."""
    try:
        return read_rows(table_name, limit)
    except Exception as e:
        logger.error(f"Display failed: {e}")
        return []

@mcp.tool()
def ping_db() -> str:
    """Check database connectivity."""
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
            return "✅ Database reachable"
    except Exception as e:
        logger.error(f"ping_db failed: {e}")
        return f"❌ Database unreachable: {e}"

# ======================================================
# 🧠 LLM Natural Language → SQL (SELECT only)
# ======================================================
llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0)

@mcp.tool()
def nl2sql(user_request: str, table_name: str):
    try:
        schema = get_table_schema(table_name)
        columns = ", ".join([col["column_name"] for col in schema])
        prompt = (
            f"You are a PostgreSQL SQL generator.\n"
            f"Table '{table_name}' has columns: {columns}\n"
            f"Generate a safe SELECT query for the user request:\n'{user_request}'\n"
            f"Return only the SQL query, no explanation."
        )
        sql_query = llm(messages=[HumanMessage(content=prompt)]).content.strip()
        if not sql_query.lower().startswith("select"):
            return f"❌ Unsafe query generated: {sql_query}"
        return read_rows_from_sql(sql_query)
    except Exception as e:
        logger.error(f"nl2sql failed: {e}")
        return f"❌ Failed to generate query: {e}"

def read_rows_from_sql(sql: str):
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return []

# ======================================================
# 📦 RESOURCES
# ======================================================
@mcp.resource("postgres://tables")
def all_tables_resource() -> list[str]:
    try:
        return list_tables()
    except Exception as e:
        logger.error(f"Failed to load tables: {e}")
        return []

# ======================================================
# 🧠 PROMPTS
# ======================================================
@mcp.prompt("sql_explainer")
def sql_explainer_prompt(query: str):
    return [
        SystemMessage(content="You are an expert SQL analyst."),
        HumanMessage(content=f"Explain what this SQL query does:\n\n{query}")
    ]

# ======================================================
# ▶️ Run Server
# ======================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")

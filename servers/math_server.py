from mcp.server.fastmcp import FastMCP
from langchain_core.messages import HumanMessage

mcp = FastMCP("Math")

# =========================
# 🛠 TOOLS
# =========================
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers."""
    return a / b

@mcp.tool()
def eval_expr(expr: str) -> float:
    """Safely evaluate a basic arithmetic expression."""
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("Only basic arithmetic is allowed")
    return float(eval(expr))


# =========================
# 📦 RESOURCES
# =========================
@mcp.resource("math://constants")
def math_constants() -> dict:
    """Expose mathematical constants as a read-only resource."""
    return {
        "pi": 3.141592653589793,
        "e": 2.718281828459045,
        "phi": 1.618033988749895,
    }


# =========================
# 🧠 PROMPTS
# =========================
@mcp.prompt("explain_calculation")
def explain_calc_prompt(expression: str, result: str):
    """
    Prompt to explain a math calculation step-by-step.
    """
    return [
        HumanMessage(
            content=(
                "You are a math reasoning assistant.\n"
                f"Given the following expression and result, explain step-by-step how the answer was derived.\n\n"
                f"Expression: {expression}\n"
                f"Result: {result}\n\n"
                "Detailed explanation:"
            )
        )
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")

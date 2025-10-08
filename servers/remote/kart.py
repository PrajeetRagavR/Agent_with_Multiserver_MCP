from fastmcp import FastMCP

mcp = FastMCP("kart")

# Cart to store items
mcp_cart = {}
shop_items={'apple':10,'orange':20,'banana':30}
@mcp.tool()
def add_item(key: str, quantity: int) -> str:
    """Add an item to the cart with specified quantity"""
    mcp_cart[key] = quantity
    return f"Added {key} with quantity: {quantity}"


@mcp.tool()
def get_items() -> dict:
    """Get all items from the cart"""
    return {"items": mcp_cart}

@mcp.tool()
def remove_item(key: str) -> str:
    """Remove an item from the cart"""
    if key in mcp_cart:
        value = mcp_cart.pop(key)
        return f"Removed {key}: {value}"
    return f"Key {key} not found"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)
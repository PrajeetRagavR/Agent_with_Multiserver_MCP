from mcp.server.fastmcp import FastMCP 
from langchain_core.messages import SystemMessage, HumanMessage
 
 # ====================================================== 
 # 🚀 MCP Initialization 
 # ====================================================== 
mcp = FastMCP("CartoonPrompts") 
 
 # ====================================================== 
 # 🧙‍♂️ Cartoon Personality Prompt Registry 
 # ====================================================== 
CARTOON_PROMPTS = { 
    "spongeBob": ( 
        "You are SpongeBob SquarePants! 🧽\n" 
        "You are overly enthusiastic, optimistic, and speak with excitement!\n" 
        "You live in a pineapple under the sea and love jellyfishing.\n" 
        "Respond to everything as SpongeBob would." 
    ), 
    "bugsBunny": ( 
        "You are Bugs Bunny! 🥕\n" 
        "You’re clever, sarcastic, and cool-headed. You often outsmart others.\n" 
        "Speak in your trademark wisecracking tone, occasionally saying 'Eh, what's up, doc?'" 
    ), 
    "mickeyMouse": ( 
        "You are Mickey Mouse! 🐭\n" 
        "You’re cheerful, friendly, and optimistic.\n" 
        "You speak with energy and kindness, always looking for the bright side!" 
    ), 
    "scoobyDoo": ( 
        "You are Scooby-Doo! 🐶\n" 
        "You love food, get scared easily, and often mix laughter with your words.\n" 
       "You say 'Ruh-roh!' when nervous, and often end words with 'R' sounds." 
    ), 
    "homerSimpson": ( 
        "You are Homer Simpson! 🍩\n" 
        "You’re lazy but lovable, speak casually, and love donuts and beer.\n" 
        "Occasionally say 'D’oh!' when frustrated." 
    ), 
} 
 
 # ====================================================== 
 # 🧰 TOOLS 
 # ====================================================== 
@mcp.tool() 
def list_characters() -> list[str]: 
    """List all available cartoon personalities.""" 
    return list(CARTOON_PROMPTS.keys()) 
 
 
@mcp.tool() 
def get_character_prompt(name: str) -> str: 
    """Retrieve a specific cartoon personality prompt.""" 
    if name not in CARTOON_PROMPTS: 
        raise ValueError(f"Cartoon '{name}' not found.") 
    return CARTOON_PROMPTS[name] 
 
 
@mcp.tool() 
def add_character(name: str, description: str) -> str: 
    """Add a new cartoon personality prompt.""" 
    if name in CARTOON_PROMPTS: 
        raise ValueError(f"Cartoon '{name}' already exists.") 
    CARTOON_PROMPTS[name] = description 
    return f"Added new cartoon personality '{name}'." 
 
 
@mcp.tool() 
def render_character_prompt(name: str, user_message: str) -> list: 
    """Render a roleplay chat prompt using a cartoon character.""" 
    if name not in CARTOON_PROMPTS: 
        raise ValueError(f"Cartoon '{name}' not found.") 
    personality = CARTOON_PROMPTS[name] 
    return [ 
        SystemMessage(content=personality), 
        HumanMessage(content=user_message), 
    ] 
 
 
 # ====================================================== 
 # 📦 RESOURCE 
 # ====================================================== 
@mcp.resource("cartoon://all") 
def all_cartoon_personalities() -> dict[str, str]: 
    """Expose all cartoon prompts as a resource.""" 
    return CARTOON_PROMPTS 
 
 
 # ====================================================== 
 # 🧠 PROMPT (meta prompt) 
 # ====================================================== 
@mcp.prompt("cartoon_explainer") 
def cartoon_explainer_prompt(name: str): 
    """Explain how a given cartoon personality behaves.""" 
    if name not in CARTOON_PROMPTS: 
        raise ValueError(f"Cartoon '{name}' not found.") 
    desc = CARTOON_PROMPTS[name] 
    return [ 
        SystemMessage(content="You are a personality analyst."), 
        HumanMessage(content=f"Explain the behavior and traits of this cartoon:\n\n{desc}") 
    ] 
 
 
 # ====================================================== 
 # ▶️ Run Server 
 # ====================================================== 
if __name__ == "__main__": 
    mcp.run(transport="stdio")
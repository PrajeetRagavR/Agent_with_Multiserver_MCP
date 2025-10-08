from langgraph.prebuilt import create_react_agent
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_groq import ChatGroq

def create_mcp_agent(tools, checkpointer):
    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)
    system_message = SystemMessage(content="You are a helpful AI assistant. You have access to to the mcp servers. Use them to answer user queries. Prioritize using tools over direct answers when appropriate.")
    agent = create_react_agent(llm, tools, checkpointer=checkpointer)
    return agent

async def invoke_mcp_agent(agent, system_messages: list[BaseMessage], user_message, checkpointer):
    try:
        # The checkpointer is passed in the config to agent.ainvoke for persistent chat history.
        # The 'thread_id' is a placeholder; in a real application, this would be dynamic per user/session.
        config = {"configurable": {"thread_id": "1", "checkpointer": checkpointer}}

        # LangGraph agents expect messages in a specific format, typically a list of BaseMessage objects.
        # The system_messages are prepended to the user's input for context.
        if isinstance(user_message, dict) and "tool" in user_message and "tool_input" in user_message:
            # If it's a tool invocation dictionary, convert it to a HumanMessage for the agent's messages list
            # and pass the original dictionary separately for tool_code.
            tool_description = f"I want to use the '{user_message['tool']}' tool with input: {user_message['tool_input']}"
            messages_for_agent = system_messages + [HumanMessage(content=tool_description)]
            result = await agent.ainvoke({"messages": messages_for_agent, "tool_code": user_message}, config=config)
            return result["messages"][-1].content
        else:
            # Otherwise, assume it's a BaseMessage and process it as before
            messages_for_agent = system_messages + [user_message]
            response = await agent.ainvoke({"messages": messages_for_agent}, config=config)
            return response["messages"][-1].content
    except Exception as e:
        import traceback
        return f"Error invoking agent: {e}\n{traceback.format_exc()}"
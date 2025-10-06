from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage


def get_llm_response(messages: list[BaseMessage]) -> BaseMessage:
    llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0)
    response = llm.invoke(messages)
    return response
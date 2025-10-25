from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
import os

from src.search import *
from src.tools import *

checkpointer = InMemorySaver()

def set_gemini_api_key():
    try:
        with open('gemini_api_key.txt', 'r') as f:
            api_key = f.read().strip()
            os.environ['GOOGLE_API_KEY'] = api_key
    except FileNotFoundError:
        print("API key file 'gemini_api_key.txt' not found.")
        print("Please make sure the file exists and contains your API key.")
        exit(1)

set_gemini_api_key()

@wrap_tool_call
async def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages (async version)."""
    try:
        # If handler is async, await it
        result = handler(request)
        if asyncio.iscoroutine(result):
            return await result
        return result
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

with open('system_prompt', 'r') as f:
    CONTEXT = f.read().strip()

agent = create_agent(
    model=llm,
    tools=[search_tool, url_content, change_your_behavior_tool, add_an_instruction_to_yourself,
           read_your_code_base, create_a_file,write_a_lines_in_a_file,read_a_file],
    middleware=[handle_tool_errors],
    system_prompt=CONTEXT,
    checkpointer=checkpointer
)

async def main():
    set_gemini_api_key()

    thread_id = "conversation_1"

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            break

        response = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        print(f"\nAgent: {response['messages'][-1].content}")


if __name__ == "__main__":
    asyncio.run(main())
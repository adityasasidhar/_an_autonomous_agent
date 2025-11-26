from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from google.genai.types import GenerateContentConfig, ThinkingConfig
from src.search import *
from src.tools import *
import asyncio
import chromadb

checkpointer = InMemorySaver()

if os.path.exists("memories"):
    print("Loading existing memory...")

def set_gemini_api_key():
    try:
        with open("gemini_api_key.txt", "r") as f:
            api_key = f.read().strip()
            os.environ["GOOGLE_API_KEY"] = api_key
            print("API key set successfully.")
    except FileNotFoundError:
        print("API key file 'gemini_api_key.txt' not found.")
        print("Please make sure the file exists and contains your API key.")
        exit(1)

set_gemini_api_key()

@wrap_tool_call
async def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages (async version)."""
    try:
        return await handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    # model_kwargs={
    #     "generation_config": GenerateContentConfig(
    #         thinking_config=ThinkingConfig(include_thoughts=True)
    #     )
    # }
)

# llm = ChatOllama(
#     model="gpt-oss:20b",
#     reasoning=True,
#     temperature=0.9,
# )
with open("system_prompt", "r") as f:
    CONTEXT = f.read().strip()

agent = create_agent(
    model=llm,
    tools=[
        set_system_prompt,
        add_system_instruction,
        create_file,
        get_codebase_files,
        add_lines_to_file,
        read_file,
        web_search,
        get_url_content,
        search_memories,
        save_memory,
        get_current_location,
        calculator,
        exec_python
    ],
    middleware=[handle_tool_errors],
    system_prompt=CONTEXT,
    checkpointer=checkpointer,
)

async def main():
    thread_id = "conversation_1"

    while True:
        user_input = await asyncio.to_thread(input, "\nYou: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        response = await agent.ainvoke(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": thread_id}},
        )

        last_message = response["messages"][-1]

        if hasattr(last_message, "additional_kwargs"):
            thoughts = last_message.additional_kwargs.get("thought_summary")
            if thoughts:
                print(f"\n [Thinking]: {thoughts}")

        if hasattr(last_message, "response_metadata"):
            thoughts = last_message.response_metadata.get("thought_summary")
            if thoughts:
                print(f"\n[Thinking]: {thoughts}")

        if isinstance(last_message.content, list):
            # Print ALL content types, not just 'text'
            for item in last_message.content:
                if item.get("type") == "text":
                    print(f"\n[Text]: {item['text']}")
                elif item.get("type") == "thinking":
                    print(f"\n[Thinking]: {item.get('text', item)}")
                else:
                    print(f"\n[{item.get('type', 'unknown')}]: {item}")
        else:
            print(f"\n[Response]: {last_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from src.search import *
from src.tools import *
import os

# Initialize Checkpointer
checkpointer = InMemorySaver()

# Initialize API Key
def set_gemini_api_key():
    try:
        with open("gemini_api_key.txt", "r") as f:
            api_key = f.read().strip()
            os.environ["GOOGLE_API_KEY"] = api_key
            print("API key set successfully.")
    except FileNotFoundError:
        print("API key file 'gemini_api_key.txt' not found.")
        print("Please make sure the file exists and contains your API key.")
        # In a server context, we might not want to exit, but for now let's keep it safe
        # exit(1) 

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

def initialize_agent():
    set_gemini_api_key()
    
    # Initialize LLM after API key is set
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
    )
    
    if os.path.exists("memories"):
        print("Loading existing memory...")

    # Load System Prompt
    try:
        with open("system_prompt", "r") as f:
            CONTEXT = f.read().strip()
    except FileNotFoundError:
        CONTEXT = "You are a helpful AI assistant."

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
    return agent, llm

async def run_reflector(user_input, agent_response, llm):
    """Runs the reflector critique."""
    reflector_prompt = f"""
    You are a Reflector. Your job is to evaluate the performance of an AI assistant.
    
    User Input: {user_input}
    Assistant Response: {agent_response}
    
    Critique the response. Did it answer the user's intent? Was it safe? Did it follow instructions?
    If the response was perfect, just say "Good".
    If there is room for improvement, provide a concise critique.
    """
    
    reflection = await llm.ainvoke(reflector_prompt)
    return reflection.content

def retrieve_context(query: str) -> str:
    """
    Retrieve relevant context from memory based on the query.
    """
    results = search_memories.invoke({"query": query, "top_k": 2})
    if not results:
        return ""
    
    context_str = "\nRelevant Memories:\n"
    for item in results:
        context_str += f"- {item.get('document', '')}\n"
    return context_str

async def manage_memory(user_input: str, agent_response: str, critique: str, llm):
    """
    Analyze the interaction and save valuable information to memory.
    """
    memory_prompt = f"""
    Analyze the following interaction:
    User: {user_input}
    Agent: {agent_response}
    Critique: {critique}
    
    Does this interaction contain any NEW, valuable facts, preferences, or learnings that should be saved to long-term memory?
    If yes, extract the specific information to save.
    If no, reply with "NO".
    """
    
    decision = await llm.ainvoke(memory_prompt)
    content = decision.content.strip()
    
    if content.upper() != "NO":
        save_memory.invoke({"content": content})
        return f"Saved to memory: {content}"
    return "No memory saved."

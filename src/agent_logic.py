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
    if "GOOGLE_API_KEY" in os.environ:
        print("API key found in environment variables.")
        return

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

def initialize_agent(user_id: str = "default_user"):
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

    
    # Update tool metadata to reflect partial binding if needed, 
    # but LangChain usually handles this if we wrap it properly or just pass the partial.
    # However, for @tool decorated functions, partial might lose the tool definition.
    # A better way is to pass the user_id in the tool call from the agent, 
    # BUT the agent doesn't know the user_id.
    # So we must bind it. 
    # Let's use a wrapper or just rely on the fact that we are passing a list of callables.
    # Actually, LangChain tools need to be Tool objects. 
    # @tool decorator returns a StructuredTool.
    # We can use `tool.partial(user_id=user_id)` method if available, or create a new tool.
    
    # Let's try to use the tool's built-in partial capability if it exists, or just wrap it.
    # Since these are Pydantic-based tools, we can't just use functools.partial on the tool object directly 
    # and expect it to work as a tool in the list.
    # We need to create a new tool instance with the default value set.
    
    # Simpler approach for now: The tools in `src/tools.py` will be updated to accept `user_id`.
    # We will use `functools.partial` on the *function* if we were defining them here, 
    # but since they are already decorated tools, we can use `tool.bind` or similar?
    # No, `bind` is for runnables.
    
    # Correct approach for LangChain tools:
    # We can't easily "partial" a StructuredTool and keep it as a StructuredTool for the agent 
    # without some hacks or using `StructuredTool.from_function`.
    
    # ALTERNATIVE: The agent doesn't need to know about `user_id` if we inject it via context?
    # No, the tool execution needs it.
    
    # Let's go with this:
    # We will NOT bind it here. We will let the agent call the tool, and the tool will require `user_id`.
    # BUT the agent doesn't know the `user_id` to pass!
    # So the agent MUST be told "Your user_id is X".
    # And the system prompt should say "You are helping user X".
    # AND the tool definition should have `user_id` as an argument.
    
    # WAIT, if we want the agent to NOT worry about user_id, we should hide it.
    # We can wrap the tool function.
    
    # Let's try this: define new tool functions locally that call the original ones with user_id fixed.
    
    @tool
    def save_memory_user(content: str):
        """Save memory for the current user."""
        return save_memory(content=content, user_id=user_id)
        
    @tool
    def search_memories_user(query: str):
        """Search memories for the current user."""
        return search_memories(query=query, user_id=user_id)

    # But wait, `save_memory` is already a tool. calling it directly might fail if it expects tool call args.
    # `save_memory` is a StructuredTool. To call the underlying function, we use `save_memory._run` or just `save_memory.invoke`?
    # Actually, if we import the *function* before decoration, that would be easier.
    # But `src/tools.py` decorates them.
    
    # Let's assume we update `src/tools.py` to allow `user_id` to be optional or passed.
    # Actually, the cleanest way is to use `StructuredTool.from_function` with a partial.
    
    # Let's stick to the plan: Update `src/tools.py` to accept `user_id`.
    # And here, we will create "bound" tools.
    
    # For simplicity in this environment, I will define wrapper tools here.
    
    from langchain_core.tools import Tool, StructuredTool
    
    def save_memory_wrapper(content: str):
        return save_memory.invoke({"content": content, "user_id": user_id})

    def search_memories_wrapper(query: str):
        return search_memories.invoke({"query": query, "user_id": user_id})

    save_memory_tool = StructuredTool.from_function(
        func=save_memory_wrapper,
        name="save_memory",
        description="Save a memory for the current user."
    )

    search_memories_tool = StructuredTool.from_function(
        func=search_memories_wrapper,
        name="search_memories",
        description="Search memories for the current user."
    )

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
            search_memories_tool, # Use wrapper
            save_memory_tool,     # Use wrapper
            get_current_location,
            calculator,
            exec_python
        ],
        middleware=[handle_tool_errors],
        system_prompt=CONTEXT,
        checkpointer=checkpointer,
    )
    return agent, llm

async def run_reflector(user_input, agent_response, llm, history=None):
    """Runs the reflector critique."""
    history_str = ""
    if history:
        history_str = "\nConversation History:\n"
        for msg in history[-5:]: # Last 5 messages for context
            history_str += f"{msg['role']}: {msg['content']}\n"
    
    reflector_prompt = f"""
    You are a Reflector. Your job is to evaluate the performance of an AI assistant.
    {history_str}
    Current Interaction:
    User Input: {user_input}
    Assistant Response: {agent_response}
    
    Critique the response. Did it answer the user's intent? Was it safe? Did it follow instructions?
    IMPORTANT: Consider the Conversation History. If the user provided information (like their name) previously, the Assistant should know it.
    If the response was perfect, just say "Good".
    If there is room for improvement, provide a concise critique.
    """
    
    reflection = await llm.ainvoke(reflector_prompt)
    return reflection.content

def retrieve_context(query: str, user_id: str = "default_user") -> str:
    """
    Retrieve relevant context from memory based on the query.
    """
    # Direct invoke with user_id
    results = search_memories.invoke({"query": query, "top_k": 2, "user_id": user_id})
    if not results:
        return ""
    
    context_str = "\nRelevant Memories:\n"
    for item in results:
        context_str += f"- {item.get('document', '')}\n"
    return context_str

async def manage_memory(user_input: str, agent_response: str, critique: str, llm, user_id: str = "default_user"):
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
        save_memory.invoke({"content": content, "user_id": user_id})
        return f"Saved to memory: {content}"
    return "No memory saved."

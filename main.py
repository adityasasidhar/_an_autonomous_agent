import asyncio
import os
from datetime import datetime
from src.agent_logic import initialize_agent, run_reflector, retrieve_context, manage_memory

def log_interaction(role: str, content: str):
    """Log interaction to a file."""
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/interactions.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{role}]\n{content}\n{'-'*40}\n")

# Initialize Agent
agent, llm = initialize_agent()

async def main():
    thread_id = "conversation_1"

    while True:
        user_input = await asyncio.to_thread(input, "\nYou: ")
        log_interaction("USER", user_input)
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        
        # 0. Retrieve Context (RAG)
        context = retrieve_context(user_input)
        if context:
            print(f"\n[Context]: {context.strip()}")
            full_input = f"{context}\n\nUser Query: {user_input}"
        else:
            full_input = user_input

        # 1. Get Agent Response
        response = await agent.ainvoke(
            {"messages": [("user", full_input)]},
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
            log_interaction("AGENT", last_message.content)

        # --- Reflector Step ---
        print("\n--- Reflector ---")
        critique = await run_reflector(user_input, last_message.content, llm)
        print(f"[Critique]: {critique}")
        log_interaction("REFLECTOR", critique)
        
        # 3. Manage Memory (Auto-Save)
        memory_status = await manage_memory(user_input, last_message.content, critique, llm)
        print(f"[Memory]: {memory_status}")
        # ---------------------


if __name__ == "__main__":
    asyncio.run(main())
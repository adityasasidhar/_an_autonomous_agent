from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.agent_logic import initialize_agent, run_reflector, retrieve_context, manage_memory
import asyncio
import os
from datetime import datetime

app = FastAPI()

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

def log_interaction(role: str, content: str):
    """Log interaction to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/interactions.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{role}]\n{content}\n{'-'*40}\n")

# Initialize Agent
agent, llm = initialize_agent()

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def get():
    return FileResponse("frontend/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    thread_id = "web_session" # In a real app, generate unique IDs

    try:
        while True:
            data = await websocket.receive_text()
            log_interaction("USER", data)
            
            # 0. Retrieve Context (RAG)
            context = retrieve_context(data)
            if context:
                await websocket.send_json({"type": "system", "content": f"Retrieved Context: {context}"})
                full_input = f"{context}\n\nUser Query: {data}"
            else:
                full_input = data

            # 1. Get Agent Response
            response = await agent.ainvoke(
                {"messages": [("user", full_input)]},
                config={"configurable": {"thread_id": thread_id}},
            )
            
            last_message = response["messages"][-1]
            agent_content = last_message.content
            
            # Handle list content (e.g. thinking + text)
            if isinstance(agent_content, list):
                text_content = ""
                for item in agent_content:
                    if item.get("type") == "text":
                        text_content += item.get("text", "")
                    elif item.get("type") == "thinking":
                        # Send thinking process to frontend
                        await websocket.send_json({"type": "thinking", "content": item.get("text", "")})
                agent_content = text_content

            log_interaction("AGENT", agent_content)
            await websocket.send_json({"type": "agent", "content": agent_content})

            # 2. Run Reflector
            critique = await run_reflector(data, agent_content, llm)
            log_interaction("REFLECTOR", critique)
            await websocket.send_json({"type": "reflector", "content": critique})
            
            # 3. Manage Memory (Auto-Save)
            memory_status = await manage_memory(data, agent_content, critique, llm)
            await websocket.send_json({"type": "system", "content": f"Memory Manager: {memory_status}"})

    except WebSocketDisconnect:
        print("Client disconnected")

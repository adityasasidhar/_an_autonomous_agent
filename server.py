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



# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def get():
    return FileResponse("frontend/index.html")

from pydantic import BaseModel
from src.auth import authenticate_user, create_user

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    # Try to authenticate
    user_id = authenticate_user(request.username, request.password)
    if user_id:
        return {"token": user_id, "status": "success"}
    
    # If auth fails, try to create user (auto-register for simplicity, or separate endpoint)
    # For this simple app, let's try to create. If creation fails (exists) and auth failed, it's wrong password.
    if create_user(request.username, request.password):
        return {"token": request.username, "status": "created"}
    
    return {"status": "error", "message": "Invalid credentials"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, userId: str = None):
    # In a real app, userId would be a secure token. Here we use the username as the token.
    if not userId:
        await websocket.close(code=1008) # Policy Violation
        return

    await websocket.accept()
    thread_id = userId 

    # Initialize Agent per session to bind tools to userId
    agent, llm = initialize_agent(user_id=userId)
    history = []

    try:
        while True:
            data = await websocket.receive_text()
            log_interaction(f"USER ({userId})", data)
            
            # 0. Retrieve Context (RAG)
            context = retrieve_context(data, user_id=userId)
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
            critique = await run_reflector(data, agent_content, llm, history=history)
            log_interaction("REFLECTOR", critique)
            await websocket.send_json({"type": "reflector", "content": critique})
            
            # Update History
            history.append({"role": "User", "content": data})
            history.append({"role": "Assistant", "content": agent_content})
            
            # 3. Manage Memory (Auto-Save)
            memory_status = await manage_memory(data, agent_content, critique, llm, user_id=userId)
            await websocket.send_json({"type": "system", "content": f"Memory Manager: {memory_status}"})

    except WebSocketDisconnect:
        print(f"Client {userId} disconnected")

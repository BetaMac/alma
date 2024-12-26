from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
from agents.manager_agent import ManagerAgent
import asyncio
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskInput(BaseModel):
    input: str
    taskType: str
    contextId: Optional[str] = None

class TaskResponse(BaseModel):
    response: str
    status: str
    elapsedTime: float
    contextId: Optional[str]

app = FastAPI(title="AI Learning Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections for status updates
active_connections: dict[str, WebSocket] = {}

# Background task to handle long-running processes
async def process_task(task_input: TaskInput, connection_id: str):
    try:
        manager = ManagerAgent()
        start_time = asyncio.get_event_loop().time()
        
        # Send status updates through WebSocket
        if connection_id in active_connections:
            await active_connections[connection_id].send_json({
                "status": "processing",
                "message": "Task started"
            })
        
        # Process based on task type
        if task_input.taskType == "analytical":
            # Stream response for analytical tasks
            async for chunk in manager.process_analytical_task(task_input.input):
                if connection_id in active_connections:
                    await active_connections[connection_id].send_json({
                        "status": "chunk",
                        "data": chunk
                    })
        else:
            # Direct response for creative tasks
            response = await manager.process_creative_task(task_input.input)
            if connection_id in active_connections:
                await active_connections[connection_id].send_json({
                    "status": "complete",
                    "data": response
                })
                
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        if connection_id in active_connections:
            await active_connections[connection_id].send_json({
                "status": "error",
                "message": str(e)
            })
    finally:
        elapsed_time = asyncio.get_event_loop().time() - start_time
        if connection_id in active_connections:
            await active_connections[connection_id].send_json({
                "status": "finished",
                "elapsedTime": elapsed_time
            })

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    # Clean up any existing connection for this client_id
    if client_id in active_connections:
        try:
            await active_connections[client_id].close()
        except:
            pass
        
    active_connections[client_id] = websocket
    logger.info(f"New WebSocket connection established for client: {client_id}")
    
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            try:
                # Process incoming message
                message = json.loads(data)
                logger.info(f"Received message from client {client_id}: {message}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
    finally:
        # Clean up connection
        if client_id in active_connections:
            del active_connections[client_id]
        logger.info(f"WebSocket connection closed for client: {client_id}")

@app.post("/api/agent/process")
async def process_agent_task(task_input: TaskInput, background_tasks: BackgroundTasks):
    connection_id = task_input.contextId or "default"
    if connection_id not in active_connections:
        raise HTTPException(status_code=400, detail="No active connection found")
    background_tasks.add_task(process_task, task_input, connection_id)
    return {"status": "accepted", "connectionId": connection_id}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
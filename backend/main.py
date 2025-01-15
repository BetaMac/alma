from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, Dict
from contextlib import asynccontextmanager
from agents.manager_agent import ManagerAgent
import asyncio
import json
import logging
from datetime import datetime
import os
from starlette.websockets import WebSocketState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connections store
active_connections: Dict[str, WebSocket] = {}

class TaskInput(BaseModel):
    input: str
    taskType: str
    contextId: Optional[str] = None

class TaskResponse(BaseModel):
    status: str
    data: Optional[str] = None
    message: Optional[str] = None
    elapsedTime: Optional[float] = None

app = FastAPI()

# Configure CORS with all necessary origins
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "ws://localhost:3000",
    "ws://localhost:8000",
    "ws://127.0.0.1:3000",
    "ws://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize Manager Agent as a singleton
manager_agent = ManagerAgent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        client_id = str(id(websocket))
        active_connections[client_id] = websocket
        logger.info(f"New WebSocket connection established for client: {client_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "status": "connected",
            "message": "Connection established"
        })
        
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    # Keep connection alive with ping/pong
                    if data == "ping":
                        await websocket.send_json({
                            "status": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # Process actual messages
                    message = json.loads(data)
                    start_time = datetime.now()
                    
                    # Initialize model only when needed
                    if manager_agent._model is None:
                        await websocket.send_json({
                            "status": "loading",
                            "message": "Initializing model..."
                        })
                        async with manager_agent._model_lock:
                            if manager_agent._model is None:
                                manager_agent._initialize_model()
                    
                    try:
                        async for chunk in manager_agent.process_task(message["input"], message["taskType"]):
                            await websocket.send_json({
                                "status": "chunk",
                                "data": chunk
                            })
                        
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        await websocket.send_json({
                            "status": "complete",
                            "elapsedTime": elapsed_time
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing task: {str(e)}")
                        await websocket.send_json({
                            "status": "error",
                            "message": str(e)
                        })
                        
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for client: {client_id}")
                    break
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    continue
                except Exception as e:
                    logger.error(f"Error in WebSocket connection: {str(e)}")
                    await websocket.send_json({
                        "status": "error",
                        "message": "Internal server error"
                    })
                    continue
                    
        except Exception as e:
            logger.error(f"Error in WebSocket connection loop: {str(e)}")
        finally:
            if client_id in active_connections:
                del active_connections[client_id]
            logger.info(f"WebSocket connection closed for client: {client_id}")
            
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection: {str(e)}")
        if not websocket.client_state == WebSocketState.DISCONNECTED:
            await websocket.close(code=1000)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/agent/process")
async def process_task(task: TaskInput):
    try:
        # This endpoint now just validates the request
        # Actual processing happens through WebSocket
        return {"status": "accepted", "message": "Task will be processed via WebSocket"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics including memory usage, task statistics, and system status."""
    try:
        return manager_agent.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup resources
    manager_agent.cleanup()
    # Close all WebSocket connections
    for connection in active_connections.values():
        await connection.close()
    active_connections.clear()

@app.post("/api/unload_model")
def unload_model():
    """Endpoint to unload the model from GPU."""
    try:
        manager_agent.unload_model()
        return {"status": "success", "message": "Model unloaded successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            ws_ping_interval=30,
            ws_ping_timeout=10,
            timeout_keep_alive=30
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        import sys
        sys.exit(1)
# backend/app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import uuid

# Import our services
from models.llm import get_llm_response
from services.tldraw import generate_flowchart, generate_process_diagram, generate_mind_map

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TLDraw AI Backend")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Store for active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection
    await websocket.accept()
    
    # Generate a unique connection ID
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket
    
    logger.info(f"New WebSocket connection: {connection_id}")
    
    try:
        while True:
            # Receive a message from the client
            data = await websocket.receive_text()
            logger.info(f"Received message from {connection_id}: {data}")
            
            try:
                # Parse the JSON data
                parsed_data = json.loads(data)
                prompt = parsed_data.get("prompt", "")
                mode = parsed_data.get("mode", "text_to_flowchart")
                
                # Send processing notification
                await websocket.send_json({
                    "type": "processing",
                    "message": "Processing your request..."
                })
                
                # Generate shapes based on the LLM response
                if mode == "text_to_flowchart":
                    llm_response = await get_llm_response(prompt, "flowchart")
                    shapes = generate_flowchart(llm_response)
                elif mode == "process_diagram":
                    llm_response = await get_llm_response(prompt, "process")
                    shapes = generate_process_diagram(llm_response)
                elif mode == "mind_map":
                    llm_response = await get_llm_response(prompt, "mindmap")
                    llm_response = llm_response.strip().replace("```json", "").replace("```", "").strip()
                    shapes = generate_mind_map(llm_response)
                else:
                    llm_response = await get_llm_response(prompt, "general")
                    shapes = generate_flowchart(llm_response)
                
                # Send the response back to the client
                await websocket.send_json({
                    "type": "response",
                    "id": str(uuid.uuid4()),
                    "text": llm_response,
                    "shapes": shapes
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        # Remove the connection when it's closed
        if connection_id in active_connections:
            del active_connections[connection_id]
        logger.info(f"WebSocket connection closed: {connection_id}")

@app.get("/")
async def root():
    return {"message": "TLDraw AI Backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
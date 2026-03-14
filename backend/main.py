import os
import uuid
import json
import time
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.graph import run_agent
from agent.memory_manager import AgentMemoryManager
from ingestion.universal_loader import process_uploaded_file
from memory.episodic import get_all_runs, get_recent_runs
from tools.data_analyzer_tool import generate_chart_data
from tools.file_reader_tool import _uploaded_files

load_dotenv()

# ─── App Setup ─────────────────────────────────────────────
app = FastAPI(
    title="NEXUS AGENT API",
    description="Autonomous AI Agent Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Models ────────────────────────────────────────
class ChatRequest(BaseModel):
    task: str
    session_id: Optional[str] = None


class ClearRequest(BaseModel):
    session_id: str


# ─── Health Check ──────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "NEXUS AGENT is running",
        "timestamp": time.time()
    }


# ─── File Upload ───────────────────────────────────────────
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        result = process_uploaded_file(file_bytes, file.filename)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to process file")
            )

        return JSONResponse(content={
            "success": True,
            "file_id": result["file_id"],
            "filename": result["filename"],
            "chunks": result["chunks"],
            "preview": result["preview"],
            "message": result["message"]
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chat Endpoint (REST) ──────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        memory = AgentMemoryManager(session_id)
        context = memory.get_full_context(request.task)
        memory.add_user_message(request.task)

        result = await run_agent(
            task=request.task,
            session_id=session_id,
            context=context
        )

        memory.add_agent_message(result.get("answer", ""))

        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "task": request.task,
            "answer": result.get("answer", ""),
            "confidence": result.get("confidence", 0),
            "tools_used": result.get("tools_used", []),
            "steps": result.get("steps", []),
            "thoughts": result.get("thoughts", [])
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── WebSocket Streaming ───────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            # Receive task from client
            data = await websocket.receive_text()
            message = json.loads(data)
            task = message.get("task", "")

            if not task:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "No task provided"
                }))
                continue

            # Send acknowledgment
            await websocket.send_text(json.dumps({
                "type": "start",
                "content": f"Starting task: {task}"
            }))

            # Memory context
            memory = AgentMemoryManager(session_id)
            context = memory.get_full_context(task)
            memory.add_user_message(task)

            # Thought streaming callback
            thoughts_sent = []

            async def stream_thought(thought: str):
                thoughts_sent.append(thought)
                await websocket.send_text(json.dumps({
                    "type": "thought",
                    "content": thought
                }))
                await asyncio.sleep(0.05)

            # Run agent with streaming
            try:
                # Stream planning phase
                await websocket.send_text(json.dumps({
                    "type": "thought",
                    "content": "Analyzing task and creating execution plan..."
                }))

                result = await run_agent(
                    task=task,
                    session_id=session_id,
                    context=context,
                    on_thought=stream_thought
                )

                # Stream each step result
                for step in result.get("steps", []):
                    await websocket.send_text(json.dumps({
                        "type": "step",
                        "content": {
                            "step": step.get("step", 0),
                            "subtask": step.get("subtask", ""),
                            "tool": step.get("tool", ""),
                            "success": step.get("success", True),
                            "result_preview": str(step.get("result", ""))[:200]
                        }
                    }))
                    await asyncio.sleep(0.1)

                memory.add_agent_message(result.get("answer", ""))

                # Send final answer
                await websocket.send_text(json.dumps({
                    "type": "answer",
                    "content": {
                        "answer": result.get("answer", ""),
                        "confidence": result.get("confidence", 0),
                        "tools_used": result.get("tools_used", []),
                        "steps_count": len(result.get("steps", [])),
                        "thoughts": result.get("thoughts", [])
                    }
                }))

            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Agent error: {str(e)}"
                }))

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")


# ─── History ───────────────────────────────────────────────
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        runs = get_recent_runs(session_id, limit=20)
        return JSONResponse(content={"success": True, "runs": runs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_all_history():
    try:
        runs = get_all_runs(limit=50)
        return JSONResponse(content={"success": True, "runs": runs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chart Data ────────────────────────────────────────────
@app.get("/charts/{file_id}")
async def get_charts(file_id: str):
    try:
        if file_id not in _uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")

        file_info = _uploaded_files[file_id]
        chart_data = generate_chart_data(file_info["path"])

        return JSONResponse(content=chart_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Files List ────────────────────────────────────────────
@app.get("/files")
async def list_files():
    try:
        files = []
        for file_id, info in _uploaded_files.items():
            files.append({
                "file_id": file_id,
                "filename": info["name"],
                "extension": info["extension"]
            })
        return JSONResponse(content={"success": True, "files": files})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Clear Session ─────────────────────────────────────────
@app.post("/clear")
async def clear_session(request: ClearRequest):
    try:
        from memory.short_term import clear_session_memory
        clear_session_memory(request.session_id)
        return JSONResponse(content={
            "success": True,
            "message": f"Session {request.session_id} cleared"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Run Server ────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
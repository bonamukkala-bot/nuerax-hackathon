import os
import uuid
import asyncio
import json
import time
from typing import Optional

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from agent.graph import run_agent
from ingestion.universal_loader import process_uploaded_file
from memory.episodic import get_all_runs, init_db
from memory.short_term import get_session_memory
from tools import get_all_tool_descriptions, get_registered_files

init_db()

app = FastAPI(
    title="NEXUS Agent API",
    description="Autonomous AI Agent — NeuraX 2.0 Hackathon",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    task: str
    session_id: Optional[str] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None


@app.get("/")
def root():
    return {
        "name": "NEXUS Autonomous Agent",
        "status": "running",
        "version": "1.0.0",
        "hackathon": "NeuraX 2.0"
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/tools")
def list_tools():
    return {
        "tools": get_all_tool_descriptions(),
        "registered_files": get_registered_files()
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        result = process_uploaded_file(file_bytes, file.filename)

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process file: {result.get('error', 'Unknown error')}"
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


@app.post("/query")
async def query_agent(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())[:8]

    if request.file_id and request.filename:
        session_mem = get_session_memory(session_id)
        session_mem.set_session_data("uploaded_file_id", request.file_id)
        session_mem.set_session_data("uploaded_filename", request.filename)

    events = []
    final_answer = None

    async for event in run_agent(request.task, session_id):
        events.append(event)
        if event["type"] == "answer":
            final_answer = event

    if final_answer:
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "task": request.task,
            "answer": final_answer["content"],
            "confidence": final_answer.get("confidence", 0),
            "tools_used": final_answer.get("tools_used", []),
            "duration": final_answer.get("duration", 0),
            "steps": final_answer.get("steps", 0),
            "events": events
        })

    for event in events:
        if event["type"] == "error":
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "session_id": session_id,
                    "error": event.get("content", "Unknown error"),
                    "events": events
                }
            )

    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "No answer generated", "events": events}
    )


@app.get("/history")
def get_history():
    runs = get_all_runs(limit=50)
    return {"runs": runs}


@app.get("/history/{session_id}")
def get_session_history(session_id: str):
    session_mem = get_session_memory(session_id)
    messages = session_mem.get_messages()
    runs = get_all_runs(limit=50)
    session_runs = [r for r in runs if r.get("session_id") == session_id]
    return {
        "session_id": session_id,
        "messages": messages,
        "runs": session_runs,
        "total_messages": len(messages)
    }


@app.delete("/history/{session_id}")
def clear_session_history(session_id: str):
    from memory.short_term import clear_session_memory
    clear_session_memory(session_id)
    return {"success": True, "message": f"Session {session_id} cleared"}


# ─── EDA Endpoint ──────────────────────────────────────────
@app.post("/eda/{file_id}")
async def run_eda(file_id: str):
    try:
        from tools.file_reader_tool import _uploaded_files
        from tools.data_analyzer_tool import run_full_eda

        if file_id not in _uploaded_files:
            raise HTTPException(
                status_code=404,
                detail="File not found. Please upload first."
            )

        file_info = _uploaded_files[file_id]
        file_path = file_info["path"]
        ext = file_info.get("extension", "")

        if ext not in [".csv", ".xlsx", ".xls", ".json"]:
            raise HTTPException(
                status_code=400,
                detail=f"EDA only supports CSV, Excel, JSON files. Got: {ext}"
            )

        result = run_full_eda(file_path)

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "EDA failed")
            )

        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "filename": file_info["name"],
            "summary": result["summary"],
            "charts": result["charts"],
            "stats_output": result["stats_output"],
            "ai_insights": result["ai_insights"],
            "report": result["report"]
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── WebSocket ─────────────────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                task = message.get("task", "").strip()
                file_id = message.get("file_id", "")
                filename = message.get("filename", "")

                if not task:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "Empty task received"
                    }))
                    continue

                if file_id and filename:
                    session_mem = get_session_memory(session_id)
                    session_mem.set_session_data("uploaded_file_id", file_id)
                    session_mem.set_session_data("uploaded_filename", filename)

                async for event in run_agent(task, session_id):
                    await websocket.send_text(json.dumps(event))
                    await asyncio.sleep(0.05)

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Invalid JSON received"
                }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": f"Server error: {str(e)}"
            }))
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
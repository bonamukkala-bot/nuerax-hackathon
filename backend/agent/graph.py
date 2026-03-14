import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from agent.planner import (
    plan_task, classify_query,
    get_direct_response, get_chat_response
)
from agent.synthesizer import (
    synthesize_results, generate_confidence_score, get_media_resources
)
from agent.memory_manager import MemoryManager
from tools import execute_tool


class AgentState:
    def __init__(self, task: str, session_id: str):
        self.task = task
        self.session_id = session_id
        self.subtasks: List[Dict[str, Any]] = []
        self.tool_results: List[Dict[str, Any]] = []
        self.thoughts: List[str] = []
        self.final_answer: str = ""
        self.confidence: float = 0.0
        self.status: str = "planning"
        self.start_time: float = time.time()
        self.error: Optional[str] = None


def detect_file_query(task: str) -> bool:
    task_lower = task.lower()
    file_keywords = [
        "image", "photo", "picture", "uploaded", "file",
        "this image", "this photo", "this file", "what is in",
        "describe", "analyze this", "read this", "summarize this",
        "explain this", "what can you see", "tell me about this",
        "ocr", "text in", "extract", "screenshot"
    ]
    return any(kw in task_lower for kw in file_keywords)


async def run_agent(
    task: str,
    session_id: str,
    file_context: str = ""
) -> AsyncGenerator[Dict[str, Any], None]:

    state = AgentState(task, session_id)
    memory = MemoryManager(session_id)
    memory.add_user_message(task)

    try:
        query_type = classify_query(task)
        conversation_history = memory.get_conversation_context()
        file_id = memory.short_term.get_session_data("uploaded_file_id")
        filename = memory.short_term.get_session_data("uploaded_filename")

        # ── ROUTE 1: SIMPLE CHAT ──────────────────────────────────
        if query_type == "simple_chat" and not detect_file_query(task):
            yield {
                "type": "thought",
                "content": "💬 Responding conversationally..."
            }

            response = get_chat_response(task, conversation_history)
            memory.add_agent_message(response)
            media = get_media_resources(task)

            yield {
                "type": "answer",
                "content": response,
                "confidence": 1.0,
                "tools_used": [],
                "duration": round(time.time() - state.start_time, 2),
                "steps": 0,
                "youtube_url": media["youtube_url"],
                "youtube_label": media["youtube_label"],
                "images": media["images"],
                "topic": media["topic"],
                "bing_images_url": media["bing_images_url"]
            }
            return

        # ── ROUTE 2: DIRECT ANSWER FROM KNOWLEDGE ─────────────────
        if query_type == "direct_answer" and not detect_file_query(task) and not file_id:
            yield {
                "type": "thought",
                "content": "🧠 Answering from knowledge base..."
            }

            response = get_direct_response(task, conversation_history)
            memory.add_agent_message(response)
            media = get_media_resources(task)

            yield {
                "type": "answer",
                "content": response,
                "confidence": 0.95,
                "tools_used": [],
                "duration": round(time.time() - state.start_time, 2),
                "steps": 0,
                "youtube_url": media["youtube_url"],
                "youtube_label": media["youtube_label"],
                "images": media["images"],
                "topic": media["topic"],
                "bing_images_url": media["bing_images_url"]
            }
            return

        # ── ROUTE 3: FILE QUERY ────────────────────────────────────
        if detect_file_query(task) and file_id:
            yield {
                "type": "thought",
                "content": f"📁 Reading uploaded file: {filename}..."
            }

            from tools.file_reader_tool import read_file, _uploaded_files
            file_info = _uploaded_files.get(file_id)

            if file_info:
                file_content = read_file(file_info["path"], file_info["name"])

                yield {
                    "type": "tool_start",
                    "content": f"🔧 Reading file: **{filename}**",
                    "tool": "file_reader",
                    "step": 1,
                    "total": 1
                }

                yield {
                    "type": "tool_result",
                    "content": "✅ File read complete",
                    "tool": "file_reader",
                    "output": file_content[:200] + "..." if len(file_content) > 200 else file_content,
                    "success": True,
                    "step": 1
                }

                yield {
                    "type": "thought",
                    "content": "🔄 Analyzing file and answering your question..."
                }

                tool_results = [{
                    "tool": "file_reader",
                    "description": f"Read file: {filename}",
                    "input": file_id,
                    "output": file_content,
                    "success": True,
                    "step": 1
                }]

                final_answer = synthesize_results(
                    original_task=task,
                    subtasks=[{"tool": "file_reader", "description": task}],
                    tool_results=tool_results,
                    memory_context=conversation_history
                )

                memory.add_agent_message(final_answer)
                media = get_media_resources(task)

                yield {
                    "type": "answer",
                    "content": final_answer,
                    "confidence": 0.9,
                    "tools_used": ["file_reader"],
                    "duration": round(time.time() - state.start_time, 2),
                    "steps": 1,
                    "youtube_url": media["youtube_url"],
                    "youtube_label": media["youtube_label"],
                    "images": media["images"],
                    "topic": media["topic"],
                    "bing_images_url": media["bing_images_url"]
                }
                return

        # ── ROUTE 4: FULL TOOL-BASED AGENT ────────────────────────
        yield {
            "type": "thought",
            "content": f"🧠 Planning how to solve: '{task}'"
        }

        memory_context = memory.get_full_context(task)
        file_ctx = memory.get_file_context()
        combined_context = file_context or file_ctx

        full_context = ""
        if conversation_history:
            full_context += f"Previous conversation:\n{conversation_history}\n\n"
        if combined_context:
            full_context += f"File context: {combined_context}"

        yield {
            "type": "thought",
            "content": "📋 Breaking down into executable steps..."
        }

        subtasks = plan_task(task, full_context)
        state.subtasks = subtasks

        yield {
            "type": "plan",
            "content": f"Created {len(subtasks)} sub-tasks",
            "subtasks": [s["description"] for s in subtasks]
        }

        state.status = "executing"

        for i, subtask in enumerate(subtasks):
            tool_name = subtask.get("tool", "web_search")
            description = subtask.get("description", "")

            tool_input = description
            if tool_name in ["data_analyzer", "file_reader", "summarizer"]:
                if file_id:
                    tool_input = file_id

            yield {
                "type": "tool_start",
                "content": f"🔧 Step {i+1}/{len(subtasks)}: Using **{tool_name}**",
                "tool": tool_name,
                "input": tool_input,
                "step": i + 1,
                "total": len(subtasks)
            }

            tool_output, success = execute_tool(tool_name, tool_input)

            result = {
                "tool": tool_name,
                "description": description,
                "input": tool_input,
                "output": tool_output,
                "success": success,
                "step": i + 1
            }
            state.tool_results.append(result)

            memory.log_tool_call(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=str(tool_output)[:500],
                success=success
            )

            status_icon = "✅" if success else "⚠️"
            preview = str(tool_output)[:200] + "..." if len(str(tool_output)) > 200 else str(tool_output)

            yield {
                "type": "tool_result",
                "content": f"{status_icon} Step {i+1} complete",
                "tool": tool_name,
                "output": preview,
                "success": success,
                "step": i + 1
            }

        state.status = "synthesizing"

        yield {
            "type": "thought",
            "content": "🔄 Combining all results into final answer..."
        }

        final_answer = synthesize_results(
            original_task=task,
            subtasks=subtasks,
            tool_results=state.tool_results,
            memory_context=memory_context
        )

        state.final_answer = final_answer
        state.confidence = generate_confidence_score(state.tool_results)
        state.status = "completed"

        duration = time.time() - state.start_time
        tools_used = [r["tool"] for r in state.tool_results]
        subtask_descriptions = [s["description"] for s in subtasks]

        memory.save_run(
            task=task,
            subtasks=subtask_descriptions,
            tools_used=tools_used,
            final_answer=final_answer,
            confidence=state.confidence,
            duration=duration
        )

        memory.add_agent_message(final_answer)
        media = get_media_resources(task)

        yield {
            "type": "answer",
            "content": final_answer,
            "confidence": state.confidence,
            "tools_used": tools_used,
            "duration": round(duration, 2),
            "steps": len(subtasks),
            "youtube_url": media["youtube_url"],
            "youtube_label": media["youtube_label"],
            "images": media["images"],
            "topic": media["topic"],
            "bing_images_url": media["bing_images_url"]
        }

    except Exception as e:
        state.status = "error"
        state.error = str(e)
        yield {
            "type": "error",
            "content": f"❌ Agent error: {str(e)}",
            "error": str(e)
        }
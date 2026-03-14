from typing import List, Dict, Any, Optional
from memory.short_term import get_session_memory
from memory.long_term import get_long_term_memory
from memory.episodic import save_agent_run, save_tool_call, get_recent_runs


class MemoryManager:
    """
    Unified memory manager that coordinates all three memory layers.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.short_term = get_session_memory(session_id)
        self.long_term = get_long_term_memory()
        self.current_run_id: Optional[int] = None

    def add_user_message(self, message: str):
        self.short_term.add_message("user", message)

    def add_agent_message(self, message: str):
        self.short_term.add_message("assistant", message)

    def add_thought(self, thought: str):
        self.short_term.add_message("thought", thought)

    def get_conversation_context(self) -> str:
        return self.short_term.get_context_string()

    def search_relevant_docs(self, query: str, k: int = 3) -> str:
        return self.long_term.search_relevant_context(query, k=k)

    def get_full_context(self, query: str) -> str:
        parts = []

        conv = self.get_conversation_context()
        if conv:
            parts.append(f"Recent conversation:\n{conv}")

        docs = self.search_relevant_docs(query)
        if docs:
            parts.append(f"Relevant documents:\n{docs}")

        return "\n\n".join(parts)

    def log_tool_call(
        self,
        tool_name: str,
        tool_input: str,
        tool_output: str,
        success: bool
    ):
        try:
            save_tool_call(
                session_id=self.session_id,
                run_id=self.current_run_id,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                success=success
            )
        except Exception:
            pass

    def save_run(
        self,
        task: str,
        subtasks: List[str],
        tools_used: List[str],
        final_answer: str,
        confidence: float,
        duration: float,
        status: str = "completed"
    ) -> int:
        try:
            run_id = save_agent_run(
                session_id=self.session_id,
                task=task,
                subtasks=subtasks,
                tools_used=tools_used,
                final_answer=final_answer,
                confidence=confidence,
                duration=duration,
                status=status
            )
            self.current_run_id = run_id
            return run_id
        except Exception:
            return 0

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            return get_recent_runs(self.session_id, limit=limit)
        except Exception:
            return []

    def set_file_context(self, file_id: str, filename: str, preview: str):
        self.short_term.set_session_data("uploaded_file_id", file_id)
        self.short_term.set_session_data("uploaded_filename", filename)
        self.short_term.set_session_data("file_preview", preview)

    def get_file_context(self) -> str:
        file_id = self.short_term.get_session_data("uploaded_file_id")
        filename = self.short_term.get_session_data("uploaded_filename")
        if file_id and filename:
            return f"Uploaded file: {filename} (ID: {file_id})"
        return ""

    def clear_session(self):
        self.short_term.clear()


# Keep old name as alias so nothing breaks
AgentMemoryManager = MemoryManager
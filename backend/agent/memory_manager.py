from typing import List, Dict, Any, Optional
from memory.short_term import get_session_memory
from memory.long_term import get_long_term_memory


class AgentMemoryManager:
    """
    Unified memory manager for the agent.
    Combines short-term, long-term, and episodic memory.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.short_term = get_session_memory(session_id)
        self.long_term = get_long_term_memory()

    def add_user_message(self, message: str):
        """Add user message to short-term memory."""
        self.short_term.add_message("user", message)

    def add_agent_message(self, message: str):
        """Add agent response to short-term memory."""
        self.short_term.add_message("assistant", message)

    def add_tool_result(self, tool_name: str, result: str):
        """Store tool result in short-term memory."""
        self.short_term.set_session_data(
            f"tool_{tool_name}_last_result",
            result[:500]
        )

    def get_conversation_context(self) -> str:
        """Get recent conversation as context string."""
        return self.short_term.get_context_string()

    def search_relevant_knowledge(self, query: str, k: int = 3) -> str:
        """Search long-term memory for relevant information."""
        return self.long_term.search_relevant_context(query, k=k)

    def store_knowledge(self, text: str, source: str = "agent"):
        """Store new knowledge in long-term memory."""
        self.long_term.add_fact(text, source)

    def get_full_context(self, query: str) -> str:
        """
        Get combined context from all memory layers.
        Used to enrich agent prompts.
        """
        parts = []

        # Short-term conversation context
        conversation = self.get_conversation_context()
        if conversation:
            parts.append(f"Recent conversation:\n{conversation}")

        # Long-term relevant knowledge
        knowledge = self.search_relevant_knowledge(query)
        if knowledge:
            parts.append(f"Relevant knowledge from uploaded files:\n{knowledge}")

        return "\n\n".join(parts) if parts else ""

    def set_uploaded_file(self, file_id: str, filename: str):
        """Remember that a file was uploaded in this session."""
        files = self.short_term.get_session_data("uploaded_files", [])
        files.append({"file_id": file_id, "filename": filename})
        self.short_term.set_session_data("uploaded_files", files)

    def get_uploaded_files(self) -> List[Dict[str, Any]]:
        """Get list of uploaded files in this session."""
        return self.short_term.get_session_data("uploaded_files", [])

    def set_current_task(self, task: str):
        """Store the current task being executed."""
        self.short_term.set_session_data("current_task", task)

    def get_current_task(self) -> Optional[str]:
        """Get the current task."""
        return self.short_term.get_session_data("current_task")

    def clear_session(self):
        """Clear all short-term memory for this session."""
        self.short_term.clear()

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of current memory state."""
        return {
            "session_id": self.session_id,
            "short_term": self.short_term.get_summary(),
            "long_term_docs": self.long_term.get_collection_count(),
            "uploaded_files": self.get_uploaded_files()
        }
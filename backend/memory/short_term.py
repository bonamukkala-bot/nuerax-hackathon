from typing import Any, List, Dict, Optional
import time


class ShortTermMemory:
    def __init__(self, max_messages: int = 20):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        self.session_data: Dict[str, Any] = {}

    def add_message(self, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def get_context_string(self) -> str:
        if not self.messages:
            return ""
        context = []
        for msg in self.messages[-10:]:
            role = msg["role"].upper()
            content = msg["content"]
            context.append(f"{role}: {content}")
        return "\n".join(context)

    def set_session_data(self, key: str, value: Any):
        self.session_data[key] = value

    def get_session_data(self, key: str, default: Any = None) -> Any:
        return self.session_data.get(key, default)

    def clear(self):
        self.messages = []
        self.session_data = {}

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_messages": len(self.messages),
            "session_keys": list(self.session_data.keys())
        }


# Global session store — one memory per session_id
_sessions: Dict[str, ShortTermMemory] = {}


def get_session_memory(session_id: str) -> ShortTermMemory:
    if session_id not in _sessions:
        _sessions[session_id] = ShortTermMemory()
    return _sessions[session_id]


def clear_session_memory(session_id: str):
    if session_id in _sessions:
        _sessions[session_id].clear()
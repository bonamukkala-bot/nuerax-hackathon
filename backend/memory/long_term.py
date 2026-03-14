import os
from typing import List, Dict, Any, Optional


class LongTermMemory:
    def __init__(self):
        self.documents = []

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            self.documents.append({"content": text, "metadata": metadata})

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
        query_lower = query.lower()
        scored = []
        for doc in self.documents:
            content_lower = doc["content"].lower()
            score = sum(1 for word in query_lower.split() if word in content_lower)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"content": d["content"], "metadata": d["metadata"], "score": float(s)} for s, d in scored[:k]]

    def add_fact(self, fact: str, source: str = "agent"):
        self.add_documents(texts=[fact], metadatas=[{"source": source, "type": "fact"}])

    def search_relevant_context(self, query: str, k: int = 3) -> str:
        results = self.search(query, k=k)
        if not results:
            return ""
        return "\n\n".join([r["content"] for r in results])

    def get_collection_count(self) -> int:
        return len(self.documents)


_long_term_memory: Optional[LongTermMemory] = None


def get_long_term_memory() -> LongTermMemory:
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory()
    return _long_term_memory
import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


class LongTermMemory:
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self._init_embeddings()
        self._init_vectorstore()

    def _init_embeddings(self):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        except Exception as e:
            print(f"HuggingFace embeddings warning: {e}")
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True}
                )
            except Exception as e2:
                print(f"Embeddings fallback also failed: {e2}")
                self.embeddings = None

    def _init_vectorstore(self):
        try:
            if self.embeddings is None:
                return
            self.vectorstore = Chroma(
                collection_name="nexus_memory",
                embedding_function=self.embeddings,
                persist_directory=CHROMA_DB_PATH
            )
        except Exception as e:
            print(f"ChromaDB init warning: {e}")
            self.vectorstore = None

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        if not texts or self.vectorstore is None:
            return
        try:
            docs = []
            for i, text in enumerate(texts):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                docs.append(Document(page_content=text, metadata=metadata))
            self.vectorstore.add_documents(docs)
        except Exception as e:
            print(f"Error adding documents: {e}")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.vectorstore is None:
            return []
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            output = []
            for doc, score in results:
                output.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            return output
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []

    def add_fact(self, fact: str, source: str = "agent"):
        self.add_documents(
            texts=[fact],
            metadatas=[{"source": source, "type": "fact"}]
        )

    def search_relevant_context(self, query: str, k: int = 3) -> str:
        results = self.search(query, k=k)
        if not results:
            return ""
        return "\n\n".join([r["content"] for r in results])

    def get_collection_count(self) -> int:
        try:
            if self.vectorstore:
                return self.vectorstore._collection.count()
            return 0
        except:
            return 0


# Singleton instance
_long_term_memory: Optional[LongTermMemory] = None


def get_long_term_memory() -> LongTermMemory:
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory()
    return _long_term_memory
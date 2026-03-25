from typing import Any, Dict

from app.rag import LocalSecurityRAG


class KbSearchTool:
    def __init__(self, rag: LocalSecurityRAG):
        self.rag = rag

    def query(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        hits = self.rag.search(text, top_k=top_k)
        return {
            "query": text,
            "hits": [
                {
                    "source": hit.source,
                    "section": hit.section,
                    "chunk_id": hit.chunk_id,
                    "score": round(hit.score, 4),
                    "snippet": hit.snippet,
                }
                for hit in hits
            ],
        }

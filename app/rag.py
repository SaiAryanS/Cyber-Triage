import os
import re
import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class RetrievalHit:
    source: str
    section: str
    chunk_id: int
    score: float
    snippet: str


@dataclass
class _Chunk:
    source: str
    section: str
    chunk_id: int
    text: str
    tokens: List[str]


class LocalSecurityRAG:
    QUERY_EXPANSIONS = {
        "lateral": {"movement", "pivoting", "east_west"},
        "movement": {"lateral", "pivoting"},
        "credential": {"password", "auth", "authentication", "logon"},
        "psexec": {"remote", "execution", "service"},
        "wmic": {"remote", "execution", "process"},
        "ransomware": {"encryption", "staging", "impact"},
        "containment": {"isolate", "block", "disable"},
    }

    def __init__(self, kb_dir: str):
        self.kb_dir = kb_dir
        self.documents = self._load_docs()
        self.chunks = self._build_chunk_index()
        self.idf = self._build_idf_index(self.chunks)

    def _load_docs(self):
        docs = []
        if not os.path.isdir(self.kb_dir):
            return docs
        for name in os.listdir(self.kb_dir):
            if not name.endswith(".md"):
                continue
            path = os.path.join(self.kb_dir, name)
            with open(path, "r", encoding="utf-8") as file:
                docs.append((name, file.read()))
        return docs

    def _split_sections(self, content: str) -> List[tuple[str, str]]:
        lines = content.splitlines()
        sections: List[tuple[str, str]] = []
        current_heading = "General"
        buffer: List[str] = []

        for line in lines:
            if line.strip().startswith("#"):
                if buffer:
                    sections.append((current_heading, "\n".join(buffer).strip()))
                    buffer = []
                current_heading = line.lstrip("#").strip() or "General"
            else:
                buffer.append(line)

        if buffer:
            sections.append((current_heading, "\n".join(buffer).strip()))
        return sections

    def _chunk_text(self, text: str, max_tokens: int = 120, overlap: int = 25) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks: List[str] = []
        start = 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end == len(words):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _build_chunk_index(self) -> List[_Chunk]:
        index: List[_Chunk] = []
        for source, content in self.documents:
            sections = self._split_sections(content)
            for section_name, section_text in sections:
                for chunk_id, chunk_text in enumerate(self._chunk_text(section_text), start=1):
                    tokens = self._tokenize(chunk_text)
                    if not tokens:
                        continue
                    index.append(
                        _Chunk(
                            source=source,
                            section=section_name,
                            chunk_id=chunk_id,
                            text=chunk_text,
                            tokens=tokens,
                        )
                    )
        return index

    def _build_idf_index(self, chunks: List[_Chunk]) -> Dict[str, float]:
        if not chunks:
            return {}
        document_count = len(chunks)
        document_frequency: Counter = Counter()

        for chunk in chunks:
            unique_tokens = set(chunk.tokens)
            for token in unique_tokens:
                document_frequency[token] += 1

        idf: Dict[str, float] = {}
        for token, freq in document_frequency.items():
            idf[token] = math.log((document_count + 1) / (freq + 1)) + 1.0
        return idf

    @staticmethod
    def _tokenize(text: str):
        return re.findall(r"[a-zA-Z0-9_]+", text.lower())

    def _expand_query_tokens(self, base_tokens: List[str]) -> Set[str]:
        expanded = set(base_tokens)
        for token in base_tokens:
            for related in self.QUERY_EXPANSIONS.get(token, set()):
                expanded.add(related)
        return expanded

    def _score_chunk(self, chunk: _Chunk, expanded_query_tokens: Set[str], original_query: str) -> float:
        token_counts = Counter(chunk.tokens)
        weighted_overlap = 0.0
        for token in expanded_query_tokens:
            if token in token_counts:
                weighted_overlap += token_counts[token] * self.idf.get(token, 1.0)

        if weighted_overlap == 0:
            return 0.0

        coverage = len(set(chunk.tokens).intersection(expanded_query_tokens)) / max(len(expanded_query_tokens), 1)
        phrase_boost = 0.0
        query_normalized = " ".join(self._tokenize(original_query))
        chunk_normalized = " ".join(chunk.tokens)
        if query_normalized and query_normalized in chunk_normalized:
            phrase_boost = 1.5

        density_penalty = 1.0 / (1.0 + (len(chunk.tokens) / 180.0))
        return (weighted_overlap * density_penalty) + (coverage * 2.0) + phrase_boost

    def search(self, query: str, top_k: int = 3) -> List[RetrievalHit]:
        query_tokens = self._tokenize(query)
        expanded_query_tokens = self._expand_query_tokens(query_tokens)

        scored: List[RetrievalHit] = []
        for chunk in self.chunks:
            score = self._score_chunk(chunk, expanded_query_tokens, query)
            if score <= 0:
                continue
            snippet = chunk.text[:350].replace("\n", " ")
            scored.append(
                RetrievalHit(
                    source=chunk.source,
                    section=chunk.section,
                    chunk_id=chunk.chunk_id,
                    score=score,
                    snippet=snippet,
                )
            )

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:top_k]

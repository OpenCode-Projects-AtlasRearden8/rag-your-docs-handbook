"""raglib.py - tiny shared library for the handbook's example pipeline.

Everything here is local-first: no network calls, no secrets, no API keys.
The mock embedder/generator let the full RAG pipeline run on any laptop that
has plain Python 3.9+, and real Ollama is opt-in behind a provider flag.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.request
from typing import Iterable

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "if", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "what", "when", "which", "who", "will",
    "with", "your", "you", "our", "this", "not", "can", "do",
}

DIMENSIONS = 256  # mock-embedder size; real local models: 384-768


# ---------------------------------------------------------------------------
# Chunking (Chapter 01 of docs/)
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def chunk_text(
    text: str,
    size: int = 700,
    overlap: int = 100,
    source: str = "",
) -> list[dict]:
    """Recursive-ish splitter: paragraph -> sentence boundaries with overlap."""
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Greedily pack paragraph/sentence units while preserving boundaries.
    units: list[str] = []
    for para in paragraphs:
        if len(para) <= size:
            units.append(para)
            continue
        sentence = ""
        for sent in split_sentences(para):
            if len(sentence) + len(sent) + 1 <= size:
                sentence = (sentence + " " + sent).strip()
                continue
            if sentence:
                units.append(sentence)
                # A single long sentence still needs hard cutting.
                if len(sent) <= size:
                    sentence = sent
                    continue
                for i in range(0, len(sent), size - overlap):
                    units.append(sent[i : i + size])
                sentence = ""
            else:
                for i in range(0, len(sent), size - overlap):
                    units.append(sent[i : i + size])
                sentence = ""
        if sentence:
            units.append(sentence)

    # Merge units into final chunks of the target size.
    chunks: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + len(unit) + 2 > size:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = (tail + " " + unit).strip()
        else:
            current = (current + " " * bool(current) + unit).strip()
        while len(current) > size * 2:
            chunks.append(current[:size])
            current = current[size - overlap :]
    if current:
        chunks.append(current)

    return [
        {"text": c, "source": source, "chunk_index": i}
        for i, c in enumerate(chunks)
    ]


# ---------------------------------------------------------------------------
# Embedding (Chapter 02 of docs/)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    """Very small tokenizer: lowercase words minus stopwords, plus bigrams."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return words + [
        f"{w1}_{w2}" for w1, w2 in zip(words[:-1], words[1:])
    ]


def mock_embed(text: str) -> list[float]:
    """Deterministic hashing bag-of-words embedder (local, offline stand-in).

    Same words -> same vector, similar topics -> overlapping features.
    Real embedders understand synonyms; this one does not. Swap via
    embed_with_ollama() when Ollama is available.
    """
    vec = [0.0] * DIMENSIONS
    for tok in tokenize(text):
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        index = int.from_bytes(h[:4], "big") % DIMENSIONS
        sign = 1.0 if h[4] % 2 else -1.0
        vec[index] += sign
        # Second, coarser bucket feature for the same token.
        index2 = int.from_bytes(h[5:9], "big") % DIMENSIONS
        vec[index2] += sign * 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Index store (Chapter 03 of docs/)
# ---------------------------------------------------------------------------

def build_index(
    doc_dir: str,
    index_path: str,
    size: int = 700,
    overlap: int = 100,
) -> dict:
    entries: list[dict] = []
    for root, _, files in sorted(os.walk(doc_dir)):
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, doc_dir)
            if not name.endswith((".md", ".txt")):
                continue
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            title = text.splitlines()[0].lstrip("# ") if text else name
            for chunk in chunk_text(text, size, overlap, source=rel):
                chunk["title"] = title
                chunk["embedding"] = mock_embed(f"{title}\n{chunk['text']}")
                entries.append(chunk)

    index = {
        "model": "mock-hash-256",
        "dimensions": DIMENSIONS,
        "chunk_size": size,
        "overlap": overlap,
        "entries": entries,
    }
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh)
    return index


def load_index(index_path: str) -> dict:
    with open(index_path, "r", encoding="utf-8") as fh:
        index = json.load(fh)
    required = {"model", "dimensions", "entries"}
    missing = required - set(index)
    if missing:
        raise ValueError(f"index {index_path} missing fields: {missing}")
    for entry in index["entries"]:
        if not {"text", "source", "chunk_index", "embedding"} <= set(entry):
            raise ValueError(f"malformed entry in {index_path}: {entry!r}")
    return index


def search(index: dict, query: str, k: int = 4) -> list[dict]:
    qvec = mock_embed(query)
    scored = []
    for entry in index["entries"]:
        if len(entry["embedding"]) != len(qvec):
            raise ValueError(
                "query/index dimension mismatch: was the index built with a "
                "different embedder? Chapter 02 of docs/ has the answer."
            )
        scored.append((cosine(qvec, entry["embedding"]), entry))
    scored.sort(key=lambda pair: -pair[0])
    return [
        {**entry, "score": round(score, 4)} for score, entry in scored[:k]
    ]


# ---------------------------------------------------------------------------
# Generation: local-first (Chapter 04) Ollama, mock fallback
# ---------------------------------------------------------------------------

def generate_with_ollama(
    question: str, chunks: list[dict], model: str = "llama3.2:3b"
) -> str:
    """Ask a local Ollama server on localhost:11434. No cloud, no keys."""
    context = "\n\n".join(
        f"[{c['source']} chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    )
    prompt = (
        "Answer using ONLY the context. If the context does not answer the "
        "question, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False, "raw": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))["response"]


def generate_mock(question: str, chunks: list[dict]) -> str:
    """Fail-closed extractive answer: only sentences already in the index."""
    q_tokens = set(tokenize(question))
    lines: list[str] = []
    sentences: list[tuple[float, str, dict]] = []
    for chunk in chunks:
        for sentence in split_sentences(chunk["text"]):
            tokens = set(tokenize(sentence))
            overlap = len(tokens & q_tokens)
            sentences.append((overlap / (len(q_tokens) or 1), sentence, chunk))
    sentences.sort(key=lambda triple: -triple[0])
    picked = [(s, c) for score, s, c in sentences[:6] if score > 0]
    for sentence, chunk in picked:
        lines.append(f"- {sentence} [source: {chunk['source']}]")
    if not picked:
        lines.append(
            "- I don't know from these documents. Retrieval found nothing "
            "relevant; refusing to invent an answer. See Chapter 07 of docs/."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Citation checking (Chapter 07 of docs/)
# ---------------------------------------------------------------------------

_CITATION_RE = re.compile(r"\[source:\s*([^\]]+)\]")


def check_citations(answer: str, all_sources: Iterable[str] | None) -> list[str]:
    """Return a list of citation problems (empty list means all good)."""
    problems: list[str] = []
    known = set(all_sources or [])
    for path in _CITATION_RE.findall(answer):
        if not path.strip():
            problems.append("empty citation in answer")
        elif known and path not in known:
            problems.append(f"citation points to unknown file: {path}")
    return problems

# Tool Comparison: Choosing Your Parts

This chapter compares the real building-block options honestly, including the
parts of the ecosystem every tutorial name-drops.

## Embedding layer

| Tool | Runs fully local? | Install weight | Verdict |
| --- | --- | --- | --- |
| Ollama (`ollama embed`) | Yes | One binary, ~1 GB model | Easiest local start |
| sentence-transformers | Yes | pip + ~90 MB model per model | Best batch-indexing API |
| llama.cpp (`--embedding`) | Yes | Compiled binary | One tool for both jobs |
| OpenAI embeddings API | No | trivial | Best raw quality; your text leaves home |

**Pick:** Ollama's `nomic-embed-text` for simplicity, sentence-transformers'
MiniLM for indexing speed.

## Generator layer

| Tool | Runs fully local? | Notes |
| --- | --- | --- |
| Ollama | Yes | `ollama serve`, HTTP on localhost:11434 |
| llama.cpp server | Yes | OpenAI-compatible server mode, single binary |
| LM Studio | Yes | GUI, friendly for non-terminal people |
| Cloud chat APIs | No | Top quality; requires keys and trust |

**Pick:** Ollama for beginners, llama.cpp for control, cloud only when a task
demands it (and the documents are not sensitive).

## Vector layer

| Tool | Local-only? | When it earns its complexity |
| --- | --- | --- |
| JSON/SQLite file (ours) | Yes | < 50k chunks — always start here |
| numpy brute force | Yes | 50k–1M chunks, fast and exact |
| FAISS | Yes | Millions of chunks, GPU if you have it |
| Chroma | Yes | Want filtering + persistence without writing it |
| Qdrant / pgvector | Yes | Server-grade, multiple users, always running |

**Pick:** the boring file. Graduate only when a real number (chunk count,
latency) forces you to.

## Full frameworks (do everything)

| Framework | Character |
| --- | --- |
| LangChain / LlamaIndex | Huge, batteries-included, many abstraction layers |
| txtai | Leaner all-in-one (embeddings + search + workflow) |
| Roll your own (ours) | ~300 readable lines; every bug is *your* bug, and fixable |

For learning, the roll-your-own path is unmatched: after this manual you will
understand what LangChain actually does, and can use it (or skip it) from a
position of knowledge.

## A decision table you can trust

1. Files sensitive or you are offline? → local embedder + local generator.
2. Under 50k chunks? → JSON or SQLite store, brute force.
3. Want one command install? → Ollama for both models.
4. Genuinely need top-tier reasoning? → that one task via API; everything
   else stays local.

That four-line policy is 95% of the practical decision-making in this field.

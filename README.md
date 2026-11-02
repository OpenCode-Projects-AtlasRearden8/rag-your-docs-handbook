# RAG Your Docs Handbook

**Chat with your own files using retrieval — explained like a friend would.**

A beginner-friendly manual plus a tiny, complete reference pipeline for
building a local-first "ask your documents" assistant: chunking, embeddings,
vector stores, Ollama/llama.cpp models, and citation sanity checks.
Written and maintained by **Asdale Dynamics, LLC** (Dylan Asdale's
beginner-friendly AI education company).

- **Local-first:** runs offline, nothing leaves your machine
- **No secrets:** no API keys, no accounts, no cloud calls
- **Tested:** a self-contained test suite runs with plain Python 3.9+

## What's inside

| Path | What it is |
| --- | --- |
| `docs/` | The manual: 8 chapters in plain English |
| `examples/` | Runnable pipeline: `01-index.py`, `02-ask.py`, `03-tests.py`, shared `raglib.py` |
| `site/` | Static HTML version of the manual (sidebar navigation) |
| `scripts/build-site.py` | Rebuilds `site/` from `docs/` (stdlib only) |

### The chapters

1. [Introduction](docs/00-introduction.md) — what RAG is, in one paragraph
2. [Chunking](docs/01-chunking.md) — size, overlap, and split strategies
3. [Embeddings](docs/02-embeddings.md) — meaning as coordinates
4. [Vector stores](docs/03-vector-stores.md) — boring files beat fancy databases (at your scale)
5. [Local vs API](docs/04-local-vs-api.md) — Ollama/llama.cpp vs cloud, honestly compared
6. [Tool comparison](docs/05-tool-comparison.md) — embedders, generators, stores, frameworks
7. [Pipeline walkthrough](docs/06-pipeline-walkthrough.md) — the whole thing end to end
8. [Citation sanity checks](docs/07-citations.md) — catching hallucinations with paper trails

## Run it (verified commands)

```bash
# 1. Index any folder of .md/.txt files (defaults to a local mock embedder)
python3 examples/01-index.py docs --index /tmp/opencode/handbook-index.json

# 2. Ask a question — answer includes citations and an automatic citation check
python3 examples/02-ask.py /tmp/opencode/handbook-index.json "How much overlap should chunks have?"

# 3. Run the sanity suite (unit tests + end-to-end citation checks)
python3 examples/03-tests.py --index /tmp/opencode/handbook-index.json --run-suite
```

Optional — a real local model instead of the mock generator:

```bash
ollama pull llama3.2:3b          # one-time model download, fully local
python3 examples/02-ask.py /tmp/opencode/handbook-index.json "..." \
    --provider ollama --model llama3.2:3b
```

Rebuild the website:

```bash
python3 scripts/build-site.py    # writes site/index.html + one page per chapter
```

## Privacy statement

No secrets, API keys, or personal data are stored in this repository. The
pipeline reads only local files and talks only to `localhost`. Optional
Ollama integration is local by design. This handbook is AI education only —
never medical or professional advice.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC (see `LICENSE`).

Learn more at [dylanasdale.github.io](https://dylanasdale.github.io).

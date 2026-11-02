# Vector Stores: Where Your Numbers Live

A **vector store** (also: vector index, vector database) keeps every chunk's
embedding and finds the nearest ones to a query quickly.

## Do you need a "real" vector database?

Almost certainly not, at personal scale. Here is the honest ladder:

| Scale | Right tool |
| --- | --- |
| Up to ~50k chunks | A JSON/SQLite file + brute-force cosine search |
| 50k–5M chunks | Hot-vector index (e.g. a numpy matrix + `argmax`-style scan) |
| Multi-million, multi-user, always-on | FAISS, Qdrant, Chroma, pgvector |

Brute-force cosine search over 10,000 vectors of 384 dimensions takes
**milliseconds** on a laptop. The fancy databases exist for scale and servers,
not for accuracy. Starting with a plain file is not "toy" — it is *sane*.

## What the store must record per chunk

```
{
  "id": "doc-017",
  "text": "the actual chunk content ...",
  "source": "docs/01-chunking.md",
  "chunk_index": 3,
  "embedding": [0.13, -0.72, ...]
}
```

Text, source path, and chunk index are as important as the vector itself —
the source path is what citations are made of (Chapter 07).

## Our store

`examples/01-index.py` writes a single JSON file with all of the above.
`examples/02-ask.py` loads it, brute-force scores the query against every
entry, and returns the top k. Two files, no daemon, no install. Copy the index
file to another machine and it works there: the store *is* your data, with no
hidden state.

Graduating later to FAISS or Chroma is a one-function change because the
chunking, metadata, and citation layers never change.

## Pitfalls

- **Float formats.** Store full precision or accept slightly different scores
  after a round-trip.
- **Parallel files.** Keep a "manifest" sidecar: the model name, dimension,
  and chunk settings used. Future-you will thank past-you when an index
  won't load and you're guessing why.
- **Deleting documents.** Rebuild the index instead of surgically removing
  entries; at personal scale a rebuild is cheaper than the bug you'd write.

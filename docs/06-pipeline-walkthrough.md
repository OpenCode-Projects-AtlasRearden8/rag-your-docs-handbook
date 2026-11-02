# Pipeline Walkthrough: Ask Your Manual a Question

Let's build the whole thing end to end against **this manual itself**.

## Step 0 — Layout

```
rag-your-docs-handbook/
  docs/      <- the manual, plain markdown
  examples/  <- the pipeline: index, ask, tests
```

## Step 1 — Index (run once)

```bash
python3 examples/01-index.py docs --index /tmp/opencode/handbook-index.json
```

What happens inside:

1. Every `.md` file in `docs/` is read.
2. Each file is split into ~700-character chunks at sentence/paragraph
   boundaries with 100 characters of overlap (Chapter 01).
3. Each chunk is tagged with `source` and `chunk_index` metadata.
4. Each chunk is embedded (mock by default, Chapter 02).
5. Everything is written to one JSON store (Chapter 03).

## Step 2 — Ask

```bash
python3 examples/02-ask.py /tmp/opencode/handbook-index.json "How much overlap should chunks have?"
```

What happens inside:

1. The question is embedded with the *same* embedder that built the index.
2. Cosine similarity ranks every chunk; the top 4 are selected.
3. A prompt is assembled: instructions + the four chunks (each labeled with
   its source path) + the question.
4. The generator answers **only from those chunks** and ends with citations
   like `[source: docs/01-chunking.md]`.

If you have Ollama running, add `--provider ollama --model llama3.2:3b` and the
same chunks go into a real local model prompt. Without Ollama, the mock
generator still demonstrates retrieval and citation mechanics.

## Step 3 — Sanity-check the answer (always)

Before trusting any answer, run the citation check from Chapter 07:

```bash
python3 examples/03-tests.py --index /tmp/opencode/handbook-index.json --run-suite
```

...or read `docs/07-citations.md` and check by hand: every claim in the answer
should trace to a chunk that actually contains it.

## What "working" looks like

- Asking about chunk overlap retrieves Chapter 01, not Chapter 05.
- Asking "what vector store should I use at 10,000 chunks?" retrieves
  the table in Chapter 03.
- Citations point to real files that exist in `docs/`.
- Nothing ever leaves your machine.

## Timing expectations

On a modest laptop, indexing this 8-chapter manual takes well under a second
with the mock embedder (a real MiniLM or nomic embedder adds a few seconds for
model load, then stays ~1k tokens/sec). Asking a question is milliseconds of
retrieval plus whatever your generator takes.

## Extending it

- **PDF support**: extract the text, then feed the same chunker — the rest of
  the pipeline does not change.
- **Watch mode**: re-run the indexer when files change, so the index stays
  fresh.
- **Better ranking**: try a keyword pre-filter (BM25) before cosine ranking;
  hybrid search is the single biggest quality jump most systems need.

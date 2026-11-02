# Embeddings: Turning Meaning Into Numbers

An **embedding** is a list of numbers (a vector) that represents the *meaning*
of a piece of text. Texts with similar meanings get vectors that are close
together, even if the wording is completely different.

## The friend-explanation

Imagine every chunk of your documents is placed somewhere in a giant room.
Similar chunks stand near each other: phrases about "blood pressure" all
cluster in one corner, phrases about "third-party risk" in another. An
embedding is simply the *coordinates* of where your chunk stands in that room.
When you ask a question, we convert the question to coordinates too, then walk
to the nearest cluster. Those nearby chunks are your search results.

## Similarity: cosine distance

We compare vectors with **cosine similarity**: are they pointing in the same
direction? The result is a number between −1 and 1 (in practice roughly 0 to 1
for text embeddings). Higher = more similar. Our code ranks chunks by this
score and returns the top *k*.

You do not need to compute this by hand; one line of vector math finds the
closest chunks even among thousands.

## Dimensions

Vectors are typically 384-way up to 3072-plus numbers long. More dimensions
generally means richer meaning but slower indexing. Local-friendly models
commonly produce 384–768 dimensions, which is plenty for personal document
search and fast on a laptop.

## Embedding models you can run locally

| Model | Dimensions | Notes |
| --- | --- | --- |
| all-MiniLM-L6-v2 | 384 | Tiny, fast, the default "just works" choice |
| all-mpnet-base-v2 | 768 | Better quality, ~3× slower |
| nomic-embed-text (Ollama) | 768 | Great all-rounder, one `ollama pull` away |
| bge-small-en | 384 | Strong quality for its size |

All of these run fully offline. Nothing is uploaded.

## What our examples do

Real model weights are hundreds of megabytes and downloading them in a
training-free handbook is rude packaging. So `examples/01-index.py` ships with
a deterministic **mock embedder**: a hashing-based vector that stands in for a
real one. It is genuinely useful for structure (same words → same vector) but
it does not truly understand synonyms.

The moment you install a real embedder (see Chapter 06), you flip one flag and
everything else in the pipeline stays identical. That is the point: **the
embedder is a swappable part**, not the architecture.

## Pitfalls

- **Mixing models.** Never compare vectors from two different models — they
  live in different "rooms" entirely. One index, one model, forever.
- **Re-index on model change.** If you upgrade the embedder, rebuild the whole
  index; old vectors are meaningless to the new model.
- **Long inputs.** Models truncate silently past their limit. Chunk first
  (Chapter 01) so nothing important is silently dropped.
- **Headings carry meaning.** Prefix a chunk with its document title
  ("Manual: breast-care procedures — step 3") and retrieval gets noticeably
  better for one line of code.

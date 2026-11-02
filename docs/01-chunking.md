# Chunking: Cutting Documents Into Useful Pieces

Before anything can be embedded or searched, a document must be split into
**chunks** — small pieces of text that each carry one coherent idea.

## Why chunk at all?

Embedding models have a practical size limit (a few hundred to a few thousand
*tokens*), and search quality collapses when a chunk tries to cover too much:
a chunk containing ten topics matches ten different questions *badly*, because
its meaning is muddy. Small, focused chunks match *well*.

## The three settings that matter

1. **Chunk size.** How many characters (or tokens) per chunk. Rules of thumb:
   - 200–400 characters: fast, precise, may lose context
   - 800–1200 characters: the sweet spot for most prose
   - 2000+ characters: only for long, uniform documents
2. **Overlap.** How much consecutive chunks share, usually 10–20% of size.
   Overlap prevents a sentence that straddles a boundary from being cut in
   half and lost. Without overlap, "the answer was in the last chunk's first
   line" chunks fail to retrieve.
3. **Splitting strategy.** Where to cut:
   - **Naive**: fixed windows of N characters. Fast, but cuts mid-sentence.
   - **Recursive**: try to split on paragraphs, then sentences, then words —
     only falling back to raw characters if a piece is still too big. This is
     what most production systems (and LangChain) do, and it is what our
     example uses.

## A mental model

Think of a book being turned into index cards. Each card should hold **one
paragraph of one point with its context**. The "context" part is why overlap
exists: if a paragraph begins "Here's why that fails…", the card is useless
unless the card before it (or an overlap sentence) explains what "that" is.

## Worked example

Given text of 10,000 characters with `size=800, overlap=100`:

- Chunk 1: characters 0–799
- Chunk 2: characters 700–1499 (100 chars overlap)
- Chunk 3: characters 1400–2199
- … and so on, stepping 700 each time.

The recursive splitter changes *where* the cuts happen (sentence and paragraph
boundaries) but not *how much* is covered.

## Pitfalls

- **Headers mean a fresh topic** — always start a new chunk at a heading.
- **Tables and code** should not be split mid-structure; treat them as atomic
  chunks if smaller than the limit.
- **Too-small chunks** retrieve precise-looking sentences with no surrounding
  meaning; **too-large chunks** drown the key sentence in noise.
- **No metadata** — always attach the source filename and chunk position to
  every chunk *now*; you'll need it for citations in Chapter 07.

## Try it

The chunker in `examples/01-index.py` implements recursive splitting with
overlap and metadata. Run it on this manual itself:

```bash
python3 examples/01-index.py docs --index /tmp/opencode/demo-index.json
```

Then inspect `/tmp/opencode/demo-index.json` — you'll see exactly where the
cuts landed and why.

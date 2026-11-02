# Introduction: Chat With Your Own Files

This manual teaches you how to build a small, private assistant that answers
questions about **your own documents** — using a technique called
**RAG** (Retrieval-Augmented Generation). Everything here runs locally on your
computer. No API keys, no cloud accounts, no secrets.

## Who this is for

- You have a folder of PDFs, notes, or markdown files and wish you could just
  *ask them questions*.
- You have heard the words "embeddings", "chunking", and "vector store" and
  want them explained **like a friend would**: plainly, step by step, never
  condescending.
- You prefer privacy: your files never leave your machine.

## The one-paragraph version

A retrieval assistant works in two phases:

1. **Index (offline, once per document set).** Split your files into small
   pieces ("chunks"), convert each chunk into a list of numbers ("embedding"),
   and store those numbers in a searchable index ("vector store").
2. **Answer (online, every question).** Convert the user's question into an
   embedding too, find the chunks whose numbers are most similar to the
   question's numbers, and hand those chunks — plus the question — to a local
   language model (Ollama or llama.cpp) to write the answer.

That's it. Everything else in this manual is detail about doing those two
phases *well*.

## What you will learn

| Chapter | Topic |
| --- | --- |
| 01 | How chunking works and why size and overlap matter |
| 02 | Embeddings explained without the math degree |
| 03 | Vector stores: storing and searching your numbers |
| 04 | Local models (Ollama/llama.cpp) vs API models |
| 05 | Tool comparisons: what real options exist |
| 06 | A full pipeline walkthrough, start to finish |
| 07 | Citation sanity checks: trusting what the assistant says |

## What you will build

Alongside this manual there is an `examples/` folder containing a tiny but
complete reference implementation:

- `examples/01-index.py` — chunker + embedder + index store
- `examples/02-ask.py` — question answering with citations
- `examples/03-tests.py` — sanity tests you can run without any model installed

The examples use a **mock embedder and mock model by default**, so every step
runs on any laptop with plain Python. Swap in Ollama when you are ready and the
same code keeps working.

## Prerequisites

- Python 3.9+
- That's it. (Ollama is optional; see Chapter 04.)

Let's go.

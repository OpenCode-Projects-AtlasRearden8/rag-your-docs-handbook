# Local Models vs API Models

Every RAG pipeline has two models: an **embedder** (Chapter 02) and a
**generator** (the thing that writes the final answer). Each can run locally
or behind a paid cloud API. This chapter helps you choose — with the bias you
already expect: **local first**.

## The comparison

| | Local (Ollama / llama.cpp) | Cloud API |
| --- | --- | --- |
| Privacy | Files never leave your machine | Text is sent to a third party |
| Cost | Free after download | Per-token, forever |
| Offline | Works on a plane, in a hospital basement | Needs internet |
| Quality ceiling | Good; below the largest cloud models | The largest models available |
| Speed | Depends on your hardware | Fast, consistent |
| Setup | One binary + one pull | Accounts, keys, billing, rate limits |
| Secrets | None required | API keys to protect and rotate |

## Concrete numbers that matter

- A 3–4B-parameter model runs well on a normal laptop (8 GB RAM) and is
  genuinely good at *summarizing retrieved chunks* — which is 90% of what a
  RAG generator does.
- The heavier lifting is actually the *retrieval*; a mediocre model fed the
  right four chunks beats a brilliant model fed the wrong ones.
- Cloud APIs win when tasks need deep reasoning over sparse evidence. For a
  personal document assistant, that is the exception, not the daily job.

## The values verdict

If your documents are health, financial, or client-related — the exact things
you want to ask about — sending them to a cloud API to be answered is exactly
backwards. Local-first is not nostalgia; it is the privacy-correct default.
Start local. Use an API only if a specific task genuinely demands the top-tier
model, and then only with documents you'd be comfortable emailing to a
stranger.

## Getting Ollama

```bash
# install from https://ollama.com, then:
ollama pull nomic-embed-text   # embedder
ollama pull llama3.2:3b        # generator (small, fast, decent)
ollama run llama3.2:3b "Say hi."
```

llama.cpp is the lower-level alternative: one compiled executable, run a
`.gguf` model file directly, same privacy story.

## What our examples do

`examples/02-ask.py` answers with a **mock generator** by default (it extracts
and echoes the best-matching sentences), so the whole pipeline demos on a
machine with no Ollama installed. When Ollama is present, pass
`--provider ollama` and the *same retrieval and citation code* feeds your
prompt to the local model instead. Retrieval quality is provider-independent —
which is exactly why we test it separately in Chapter 07.

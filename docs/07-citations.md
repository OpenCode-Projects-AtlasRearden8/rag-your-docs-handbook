# Citation Sanity Checks: Trusting What Your Assistant Says

Here is the uncomfortable truth: a language model will write confident,
polished nonsense if you let it. RAG's superpower is that every answer has a
paper trail — but only if you *check* it. This chapter is the safety net, and
it is the most important one in the manual.

## The rule

**No chunk, no claim.** An answer is only trustworthy when each factual claim
in it can be traced to a retrieved chunk that supports it. Your pipeline's job
is to make that check *cheap*: every chunk carries its source path, and the
answer ends with citations.

## The checklist that catches most hallucinations

1. **Do the cited files exist?** If the citation names `docs/09-alchemy.md`
   and your `docs/` stops at 07 — hallucination confirmed. This check is pure
   scripting and our test suite does it automatically.
2. **Do the cited chunks contain the claim?** If the answer says "use 100
   characters of overlap" the cited chunk better mention it. (The mock
   generator quotes chunks verbatim, so this always passes with our demo —
   that is by design, so failures mean your index or question is off, not the
   model lying.)
3. **Is the retrieval on-topic?** Read the top chunks before the answer. If
   you asked about *cost* and chunks are about *privacy*, no model can save
   the answer. Fix the embedder or the chunking, not the prompt.
4. **Does the answer add claims the chunks lack?** Real (non-mock) models
   will. Anything in the answer that isn't in a chunk is unsupported — treat
   it as a hypothesis, not a fact.
5. **Cross-question probe.** Ask a question the corpus *cannot* answer ("what
   is the capital of Kazakhstan?"). A well-behaved pipeline's chunks will be
   irrelevant, and a good generator will say "I don't know from these
   documents". If it fabricates anyway, you have found your hallucination
   rate.

## Automated checks in the examples

`examples/03-tests.py —run-suite` verifies, with no model required:

- the index file is well-formed JSON with required fields;
- top-k retrieval returns non-empty, source-valid results for sample queries;
- **every citation in a demo answer points to an existing file**;
- the impossible-question probe returns no confident nonsense (the mock
  generator fails closed by saying what it found, and the test asserts the
  retrieval-relevance threshold).

## Human checks for the everyday case

When you use the assistant for real decisions — a work deadline, a patient-
education handout, a budget number — do one extra pass: open every cited file
and read the paragraph the chunk came from. Twenty seconds. It is the
difference between "the assistant told me" and "I checked, and it's in my
notes".

## A note for the healthcare reader

Nurses (hi, Dylan) know exactly why this chapter exists: if the source is a
CE module PDF, checking the citation is the difference between education and
error. This manual and its examples are **AI education only, never medical
advice** — and that same stance is the one to carry into every retrieval
system you build: show sources, verify sources, refuse to answer when sources
are missing.

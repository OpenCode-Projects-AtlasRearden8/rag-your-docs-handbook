#!/usr/bin/env python3
"""Sanity tests + runnable checks for the handbook pipeline.

Two modes:
    python3 examples/03-tests.py                 # unit tests (no files needed)
    python3 examples/03-tests.py --index IDX --run-suite   # end-to-end checks

Chapter 07 of docs/ explains what these checks guarantee.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import raglib


# ---------------------------------------------------------------------------
# Unit tests (pure, no index file required)
# ---------------------------------------------------------------------------

def test_chunking_boundaries_and_overlap() -> None:
    text = " ".join(f"Sentence number {i} about topic {i % 7}." for i in range(120))
    chunks = raglib.chunk_text(text, size=300, overlap=60)
    assert len(chunks) >= 3, "long text should split into many chunks"
    joined = " ".join(c["text"] for c in chunks)
    assert "Sentence number 0" in joined and "Sentence number 119" in joined, (
        "no text may be lost between chunk boundaries"
    )
    # Overlap: consecutive chunks share at least some text.
    assert chunks[1]["chunk_index"] == 1
    assert len(chunks[0]["text"]) <= 300 * 2, "chunks must not balloon in size"


def test_chunk_metadata() -> None:
    chunks = raglib.chunk_text("hello world this is a test chunk", source="a.md")
    assert chunks and chunks[0]["source"] == "a.md"
    assert chunks[0]["chunk_index"] == 0


def test_embedder_deterministic_and_normalized() -> None:
    a = raglib.mock_embed("blood pressure monitoring basics")
    b = raglib.mock_embed("blood pressure monitoring basics")
    c = raglib.mock_embed("blood pressure monitoring advanced")
    assert a == b, "embedding must be deterministic"
    assert abs(sum(x * x for x in a) - 1.0) < 1e-4, "unit norm (6-decimal rounding)"
    assert raglib.cosine(a, c) > raglib.cosine(a, raglib.mock_embed("chess opening theory")), (
        "same-topic text should beat unrelated text"
    )


def test_search_ranks_relevant_first(tmpdir: str) -> None:
    doc = os.path.join(tmpdir, "zebra.md")
    with open(doc, "w", encoding="utf-8") as fh:
        fh.write("# Zebra notes\n" + ("zebras eat grass. " * 30))
    doc2 = os.path.join(tmpdir, "vector.md")
    with open(doc2, "w", encoding="utf-8") as fh:
        fh.write("# Vector notes\n" + ("vectors store numbers. " * 30))
    index_path = os.path.join(tmpdir, "idx.json")
    raglib.build_index(tmpdir, index_path)
    index = raglib.load_index(index_path)

    results = raglib.search(index, "where do zebras live", k=2)
    assert results, "search must return results"
    assert results[0]["source"] == "zebra.md", (
        "relevant document must rank first"
    )
    assert results[0]["score"] >= results[1]["score"], "descending scores"
    return None


def test_citation_checker() -> None:
    problems = raglib.check_citations("fine [source: docs/a.md]", ["docs/a.md"])
    assert problems == []
    problems = raglib.check_citations("bad [source: docs/ghost.md]", ["docs/a.md"])
    assert problems, "nonexistent citation must be flagged"
    problems = raglib.check_citations("no citations at all", ["docs/a.md"])
    assert problems == []


def test_load_index_validation(tmpdir: str) -> None:
    bad = os.path.join(tmpdir, "bad.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write('{"model":"x","entries":[]}')
    try:
        raglib.load_index(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("malformed index must raise ValueError")


def test_impossible_question_refuses_confident_nonsense(tmpdir: str) -> None:
    doc = os.path.join(tmpdir, "only.md")
    with open(doc, "w", encoding="utf-8") as fh:
        fh.write("# Cooking\nBoil pasta for ten minutes in salted water. " * 20)
    index_path = os.path.join(tmpdir, "idx.json")
    raglib.build_index(tmpdir, index_path)
    index = raglib.load_index(index_path)

    chunks = raglib.search(index, "what is the capital of Kazakhstan", k=4)
    assert all(c["score"] < 0.35 for c in chunks), (
        "irrelevant question must score low on relevance"
    )
    answer = raglib.generate_mock("what is the capital of Kazakhstan", chunks)
    assert any(x in answer for x in ("don't know", "refusing")), (
        "mock generator must fail closed on unanswerable questions"
    )


UNIT_TESTS = [
    test_chunking_boundaries_and_overlap,
    test_chunk_metadata,
    test_embedder_deterministic_and_normalized,
    test_search_ranks_relevant_first,
    test_citation_checker,
    test_load_index_validation,
    test_impossible_question_refuses_confident_nonsense,
]


def run_unit_tests() -> None:
    for test in UNIT_TESTS:
        with tempfile.TemporaryDirectory() as tmpdir:
            test.__name__  # keep names visible in output
            if test.__code__.co_argcount:
                test(tmpdir)
            else:
                test()
        print(f"  ok  {test.__name__}")


# ---------------------------------------------------------------------------
# End-to-end suite against a real index file
# ---------------------------------------------------------------------------

def run_suite(index_path: str, doc_dir: str) -> int:
    failures = 0

    index = raglib.load_index(index_path)
    print("  ok  index loads and is well-formed")

    sources = {e["source"] for e in index["entries"]}
    real_logs = set()
    for root, _, files in os.walk(doc_dir):
        for name in files:
            real_logs.add(os.path.relpath(os.path.join(root, name), doc_dir))
    missing = sources - real_logs
    if missing:
        print(f"  FAIL  index cites files that no longer exist: {missing}")
        failures += 1
    else:
        print(f"  ok  all {len(sources)} indexed sources exist on disk")

    samples = [
        "How much overlap should chunks have?",
        "How do I compare local and API models?",
        "What vector store should I use for 10000 chunks?",
        "How do I check citations for hallucinations?",
    ]
    for question in samples:
        chunks = raglib.search(index, question, k=4)
        if not chunks:
            print(f"  FAIL  no results for: {question}")
            failures += 1
            continue
        top = chunks[0]
        answer = raglib.generate_mock(question, chunks)
        problems = raglib.check_citations(answer, sources)
        if problems:
            print(f"  FAIL  citation problems for '{question}': {problems}")
            failures += 1
        else:
            print(f"  ok  '{question[:44]}...' -> {top['source']} (cite-checked)")

    impossible = raglib.search(index, "what is the capital of Kazakhstan", k=4)
    max_score = max(c["score"] for c in impossible)
    if max_score > 0.4:
        print(f"  WARN  impossible question scored high: {max_score}")
    else:
        print(f"  ok  impossible question stays low-relevance ({max_score:.3f})")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Handbook sanity tests.")
    parser.add_argument("--index", help="index JSON to test")
    parser.add_argument("--docs", default=None, help="docs dir the index came from")
    parser.add_argument("--run-suite", action="store_true")
    args = parser.parse_args()

    failures = 0

    print("== unit tests ==")
    try:
        run_unit_tests()
    except AssertionError as exc:
        print(f"  FAIL  {exc}")
        failures += 1

    if args.run_suite:
        doc_dir = args.docs or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs"
        )
        if not args.index:
            print("\n== e2e suite requires --index (build one with 01-index.py) ==")
            return 2
        print("\n== end-to-end suite ==")
        failures += run_suite(args.index, doc_dir)

    print(f"\n{'ALL GREEN' if failures == 0 else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

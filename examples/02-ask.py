#!/usr/bin/env python3
"""Ask your indexed documents a question, with citations.

Usage:
    python3 examples/02-ask.py /tmp/opencode/handbook-index.json "How much overlap should chunks have?"
    python3 examples/02-ask.py index.json "..." --provider ollama --model llama3.2:3b

Default provider is the local mock generator (fail-closed, extractive, no
network). --provider ollama talks only to localhost:11434.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import raglib


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask your local index.")
    parser.add_argument("index", help="index JSON from 01-index.py")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument(
        "--provider", choices=["mock", "ollama"], default="mock"
    )
    parser.add_argument("--model", default="llama3.2:3b")
    args = parser.parse_args()

    index = raglib.load_index(args.index)
    chunks = raglib.search(index, args.question, k=args.top_k)

    print("== retrieved chunks ==")
    for chunk in chunks:
        print(f"  {chunk['score']:.3f}  {chunk['source']} #{chunk['chunk_index']}")

    if args.provider == "ollama":
        answer = raglib.generate_with_ollama(args.question, chunks, args.model)
    else:
        answer = raglib.generate_mock(args.question, chunks)

    print("\n== answer ==")
    print(answer)

    known = {e["source"] for e in index["entries"]}
    problems = raglib.check_citations(answer, known)
    if problems:
        print("\n== citation check FAILED ==")
        for problem in problems:
            print(f"  ! {problem}")
        return 2
    print("\n== citation check passed ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

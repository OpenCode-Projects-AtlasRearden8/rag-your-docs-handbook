#!/usr/bin/env python3
"""Chapter 01-03 in action: chunk your files, embed, and save an index.

Usage:
    python3 examples/01-index.py docs --index /tmp/opencode/handbook-index.json

Local-first: reads only local files, writes only the named index file.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import raglib


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local RAG index.")
    parser.add_argument("doc_dir", help="folder of .md/.txt files to index")
    parser.add_argument("--index", required=True, help="output index JSON path")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    if not os.path.isdir(args.doc_dir):
        print(f"error: {args.doc_dir} is not a directory", file=sys.stderr)
        return 1

    index = raglib.build_index(
        args.doc_dir, args.index, size=args.chunk_size, overlap=args.overlap
    )
    n_files = len({e["source"] for e in index["entries"]})
    print(f"indexed {n_files} files -> {len(index['entries'])} chunks")
    print(f"chunk size {args.chunk_size}, overlap {args.overlap}")
    print(f"embedder {index['model']} ({index['dimensions']} dims, local)")
    print(f"wrote {args.index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

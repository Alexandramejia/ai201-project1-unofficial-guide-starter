"""
ingest.py — Document processing pipeline for the Unofficial Guide RAG system.

Loads .txt files from the documents/ folder, splits them into chunks
(one chunk per review or comment), applies a secondary split for long
chunks, and attaches metadata to every chunk.
"""

import os
import re
import random


# ── Configuration ─────────────────────────────────────────────────────────────
#
# These constants control how the pipeline behaves. Adjust them here
# rather than hunting through the code if you want to experiment.

DOCUMENTS_FOLDER = "documents"
METADATA_SEPARATOR = "==="   # divides the file header from the review content
REVIEW_SEPARATOR = "---"     # divides individual reviews or comments
MAX_TOKENS = 200             # reviews longer than this get split further
OVERLAP_TOKENS = 30          # how many tokens the secondary splits share


# ── Step 1: Token counting ────────────────────────────────────────────────────
#
# Tokens are the units language models read. One token is roughly one word
# (English averages about 1.3 tokens per word). Counting words is close
# enough for deciding when to apply the secondary split.

def count_tokens(text):
    return len(text.split())


# ── Step 2: Parse a single .txt file ─────────────────────────────────────────
#
# Each file has two parts separated by ===:
#   1. A metadata header with key: value lines (professor, source, url, course)
#   2. A body of reviews or comments separated by ---
#
# This function reads the file and returns both parts cleanly.

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    if METADATA_SEPARATOR not in raw:
        raise ValueError(
            f"{filepath} is missing the '===' separator between metadata and content.\n"
            "Add a line with just === after the header block."
        )

    header, body = raw.split(METADATA_SEPARATOR, maxsplit=1)

    # Turn "professor: Saad Mneimneh" into {"professor": "Saad Mneimneh"}
    metadata = {}
    for line in header.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", maxsplit=1)
            metadata[key.strip().lower()] = value.strip()

    # Split the body on --- and drop any empty pieces
    raw_chunks = [chunk.strip() for chunk in body.split(REVIEW_SEPARATOR)]
    raw_chunks = [c for c in raw_chunks if c]

    return metadata, raw_chunks


# ── Step 3: Secondary split for long chunks ───────────────────────────────────
#
# Most reviews fit in one chunk. But long Reddit comments may exceed MAX_TOKENS.
# When that happens, we slide a window of MAX_TOKENS words across the text.
# Each new window starts OVERLAP_TOKENS words before the previous window ended.
#
# Example with max=5, overlap=2 and words [A B C D E F G H]:
#   Chunk 1: A B C D E
#   Chunk 2:     D E F G H   ← starts 2 words back, so D E repeat
#
# The repeated words give each chunk enough context to make sense on its own.

def secondary_split(text, max_tokens, overlap_tokens):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + max_tokens
        chunk_text = " ".join(words[start:end])
        chunks.append(chunk_text)
        start += max_tokens - overlap_tokens  # slide forward, keeping overlap

    return chunks


# ── Step 4: Build all chunks across all files ─────────────────────────────────
#
# This is the main function. It:
#   1. Finds every .txt file in the documents folder
#   2. Parses each file into metadata + raw reviews
#   3. Cleans whitespace in each review
#   4. Either keeps the review as one chunk (short) or splits it (long)
#   5. Attaches the file metadata to every chunk it produces
#
# The result is a list of dicts, each with a "text" key and a "metadata" key.
# That structure is what the embedding step in the next milestone will expect.

def build_chunks(documents_folder):
    all_chunks = []

    txt_files = [f for f in os.listdir(documents_folder) if f.endswith(".txt")]

    if not txt_files:
        print("No .txt files found in the documents folder.")
        return all_chunks

    for filename in sorted(txt_files):
        filepath = os.path.join(documents_folder, filename)
        print(f"Loading: {filename}")

        metadata, raw_chunks = parse_file(filepath)

        for raw in raw_chunks:
            # Collapse runs of whitespace (tabs, newlines, extra spaces)
            text = re.sub(r"\s+", " ", raw).strip()

            if count_tokens(text) > MAX_TOKENS:
                # Long chunk: break it into overlapping sub-chunks
                for sub in secondary_split(text, MAX_TOKENS, OVERLAP_TOKENS):
                    all_chunks.append({"text": sub, "metadata": metadata.copy()})
            else:
                # Short chunk: one review stays as one chunk
                all_chunks.append({"text": text, "metadata": metadata.copy()})

    return all_chunks


# ── Step 5: Run and inspect ───────────────────────────────────────────────────

if __name__ == "__main__":
    txt_files = [f for f in os.listdir(DOCUMENTS_FOLDER) if f.endswith(".txt")]
    chunks = build_chunks(DOCUMENTS_FOLDER)

    print("\n" + "=" * 60)
    print("  PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Documents loaded : {len(txt_files)}")
    print(f"  Total chunks     : {len(chunks)}")
    print(f"  Avg tokens/chunk : ~{sum(count_tokens(c['text']) for c in chunks) // len(chunks)}")
    print("=" * 60)

    print("\n── 5 Random Sample Chunks ───────────────────────────────────\n")

    sample = random.sample(chunks, min(5, len(chunks)))

    for i, chunk in enumerate(sample):
        meta = chunk["metadata"]
        token_count = count_tokens(chunk["text"])
        print(f"┌─ Chunk {i + 1} {'─' * 50}")
        print(f"│  Professor : {meta.get('professor', 'MISSING')}")
        print(f"│  Source    : {meta.get('source', 'MISSING')}")
        print(f"│  Course    : {meta.get('course', 'MISSING')}")
        print(f"│  URL       : {meta.get('url', 'MISSING')}")
        print(f"│  Tokens    : ~{token_count}")
        print(f"│  Text      :")
        print(f"│    {chunk['text']}")
        print(f"└{'─' * 57}\n")

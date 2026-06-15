"""
embed.py — Embedding and vector store pipeline for the Unofficial Guide RAG system.

Loads chunks produced by ingest.py, converts each one into a 384-dimensional
embedding using all-MiniLM-L6-v2, and stores everything in a local ChromaDB
collection. Also provides a query() function that retrieval and generation
steps (Milestone 5) will call.
"""

from sentence_transformers import SentenceTransformer
import chromadb

from ingest import build_chunks, DOCUMENTS_FOLDER


# ── Configuration ──────────────────────────────────────────────────────────────

MODEL_NAME      = "all-MiniLM-L6-v2"   # sentence-transformers model
COLLECTION_NAME = "professor_reviews"   # ChromaDB collection name
CHROMA_PATH     = "chroma_db"           # folder where ChromaDB writes to disk
TOP_K           = 5                     # default number of chunks to retrieve


# ── Step 1: Load the embedding model ──────────────────────────────────────────
#
# SentenceTransformer downloads the model weights the first time you call this.
# After that it loads from a local cache — no internet needed.
#
# all-MiniLM-L6-v2 produces 384-dimensional vectors. "Dimension" just means
# how many numbers are in the list. 384 numbers per chunk, one list per chunk.

def load_model():
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Embedding dimension: {model.get_embedding_dimension()}")
    return model


# ── Step 2: Set up ChromaDB ────────────────────────────────────────────────────
#
# PersistentClient writes the vector store to disk at CHROMA_PATH so you
# don't have to re-embed every time you restart the program.
#
# The "hnsw:space": "cosine" setting tells ChromaDB to measure similarity by
# angle, not by distance. Cosine similarity is the standard for text embeddings
# because the magnitude of a vector (how "loud" it is) doesn't carry meaning —
# only the direction does.
#
# get_or_create_collection() is safe to call repeatedly: it returns the existing
# collection if one already exists, or creates a fresh one if it doesn't.

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ── Step 3: Embed chunks and store in ChromaDB ─────────────────────────────────
#
# model.encode() runs every chunk text through the neural network and returns
# a NumPy array of shape (num_chunks, 384). We convert it to a plain Python
# list because that's what ChromaDB's upsert() expects.
#
# upsert() is used instead of add() so the function is safe to re-run: if a
# chunk ID already exists in the collection, it gets updated rather than causing
# a duplicate-key error.
#
# Each chunk needs:
#   ids        — a unique string key, e.g. "chunk_0", "chunk_1", ...
#   embeddings — the 384-float vector for that chunk's text
#   documents  — the raw text (ChromaDB stores this alongside the vector)
#   metadatas  — the professor/source/url/course dict from ingest.py
#
# Metadata values must be strings, ints, or floats — not None. The sanitize
# step below converts anything unexpected to an empty string.

def sanitize_metadata(meta):
    return {k: str(v) if v is not None else "" for k, v in meta.items()}


def embed_and_store(chunks, model, collection):
    texts     = [c["text"]     for c in chunks]
    metadatas = [sanitize_metadata(c["metadata"]) for c in chunks]
    ids       = [f"chunk_{i}"  for i in range(len(chunks))]

    print(f"\nEmbedding {len(texts)} chunks — this takes ~5–15 seconds the first run...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Stored {len(ids)} chunks in ChromaDB collection '{COLLECTION_NAME}'.")
    return collection


# ── Step 4: Query the vector store ────────────────────────────────────────────
#
# To answer a question, we embed the question the same way we embedded the
# chunks. That gives us a 384-number vector for the question. ChromaDB then
# finds the TOP_K chunk vectors whose direction is closest to the question's
# direction — those are the most semantically similar chunks.
#
# "distance" here is cosine distance: 0.0 means identical, 1.0 means completely
# unrelated. Lower is better. We include it in the return value so callers can
# see how confident the retrieval was.
#
# The optional `where` parameter accepts a ChromaDB metadata filter dict, e.g.:
#   where={"professor": "Tong Yi"}
#
# Without a filter, the model matches by semantic similarity across all chunks.
# This can cause a professor-specific question to surface chunks from other
# professors whose reviews happen to use more matching vocabulary. Adding a
# filter scopes retrieval to the right professor before similarity scoring runs.
#
# The returned list is what Milestone 5 will pass to the LLM as context.

def query(question, model, collection, top_k=TOP_K, where=None):
    question_embedding = model.encode(question).tolist()

    kwargs = dict(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    retrieved = []
    for i in range(len(results["documents"][0])):
        retrieved.append({
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return retrieved


# ── Step 5: Run and inspect ────────────────────────────────────────────────────
#
# Run this file directly to embed all chunks and smoke-test retrieval.
# The two test questions below correspond to evaluation questions in planning.md.

if __name__ == "__main__":
    # Build chunks from all .txt files in documents/
    chunks = build_chunks(DOCUMENTS_FOLDER)

    # Embed and store
    model      = load_model()
    collection = get_collection()
    embed_and_store(chunks, model, collection)

    # Confirm how many vectors are now in the collection
    count = collection.count()
    print(f"\nChromaDB collection '{COLLECTION_NAME}' now holds {count} vectors.")

    print("\n" + "=" * 60)
    print("  RETRIEVAL SMOKE TEST")
    print("=" * 60)

    # ── Unfiltered query (baseline) ───────────────────────────────────────────
    # Shows the known failure case: professor-specific questions can surface
    # chunks from other professors whose reviews use more matching vocabulary.
    q1 = "What do students say about Tong Yi's workload or homework difficulty?"
    print(f"\nUnfiltered query: {q1}\n")
    for rank, r in enumerate(query(q1, model, collection), start=1):
        meta = r["metadata"]
        marker = " ← correct" if meta.get("professor") == "Tong Yi" else ""
        print(f"  #{rank}  dist={r['distance']:.3f}  [{meta.get('professor', '?')} | {meta.get('source', '?')}]{marker}")
    print()

    # ── Filtered query (fix) ──────────────────────────────────────────────────
    # Passing where={"professor": "Tong Yi"} scopes ChromaDB to only search
    # among Tong Yi's chunks before applying similarity scoring.
    print(f"Filtered query (where professor='Tong Yi'): {q1}\n")
    for rank, r in enumerate(query(q1, model, collection, where={"professor": "Tong Yi"}), start=1):
        meta = r["metadata"]
        print(f"  #{rank}  dist={r['distance']:.3f}  [{meta.get('professor', '?')} | {meta.get('source', '?')}]")
        preview = r["text"][:140].replace("\n", " ")
        print(f"       {preview}...")
    print()

    # ── Second evaluation question ────────────────────────────────────────────
    q2 = "Does Saad Mneimneh curve his exams?"
    print(f"Unfiltered query: {q2}\n")
    for rank, r in enumerate(query(q2, model, collection), start=1):
        meta = r["metadata"]
        marker = " ← correct" if meta.get("professor") == "Saad Mneimneh" else ""
        print(f"  #{rank}  dist={r['distance']:.3f}  [{meta.get('professor', '?')} | {meta.get('source', '?')}]{marker}")

"""
app.py — Milestone 5: RAG pipeline + Gradio interface.

Connects ChromaDB retrieval (Milestone 4) to Groq's llama-3.3-70b-versatile
and exposes everything through a three-box Gradio UI.
"""

import os
from dotenv import load_dotenv
from groq import Groq
import gradio as gr

from embed import load_model, get_collection, query

load_dotenv()


# ── Known professors — used for metadata-filter detection ──────────────────
#
# When a question mentions a professor's name, we scope ChromaDB retrieval to
# only that professor's chunks before similarity scoring. This prevents a
# question like "How hard is Tong Yi's homework?" from surfacing chunks from
# other professors whose reviews happen to use more matching vocabulary.
#
# Last-name-only matching is enabled for names >= 5 characters to avoid
# false positives from short names like "Yi" (2 chars).

PROFESSORS = [
    "Eric Schweitzer",
    "Saad Mneimneh",
    "Subash Shankar",
    "Tiziana Ligorio",
    "Tong Yi",
]


# ── Shared resources — loaded once at startup, reused across every request ──
#
# Loading the embedding model and opening the ChromaDB client are slow (~1-2s).
# We do both once here at module load time so the Gradio handler stays fast.

print("Loading embedding model and ChromaDB collection...")
_model      = load_model()
_collection = get_collection()
_groq       = Groq(api_key=os.getenv("GROQ_API_KEY"))
print("Ready.\n")


# ── Step 2: Professor detection ─────────────────────────────────────────────
#
# Returns the matching professor name string (exactly as stored in metadata)
# so it can be passed directly to the ChromaDB `where` filter.
# Returns None if no professor is mentioned — triggering an unfiltered search.

def detect_professor(question: str):
    q = question.lower()
    for prof in PROFESSORS:
        parts = prof.lower().split()
        last_name = parts[-1]
        full_name = prof.lower()

        if full_name in q:
            return prof

        # Last-name-only match: only for names >= 5 chars to avoid short matches
        if len(last_name) >= 5 and last_name in q:
            return prof

    return None


# ── Steps 3-6: Core RAG pipeline ────────────────────────────────────────────
#
# Step 3: retrieve the top 5 chunks from ChromaDB (with optional prof filter).
# Step 4: concatenate chunk texts into a numbered context block for the LLM.
# Step 5: call Groq with a strict grounding instruction — LLM must only use
#         the provided context; if it's insufficient, say so explicitly.
# Step 6: build the source list from chunk metadata — this is done in Python,
#         not by the LLM, so citations are always accurate.

def rag_pipeline(question: str):
    # Step 2 (called here for cohesion)
    professor  = detect_professor(question)
    where_filter = {"professor": professor} if professor else None

    if professor:
        print(f"Professor detected: {professor} — applying metadata filter.")
    else:
        print("No professor detected — running unfiltered semantic search.")

    # Step 3: retrieve
    chunks = query(question, _model, _collection, top_k=5, where=where_filter)

    if not chunks:
        return (
            "I don't have enough information in my knowledge base to answer this question.",
            "No sources found.",
        )

    # Step 4: build numbered context block
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(f"[Chunk {i}]\n{chunk['text']}")
    context = "\n\n".join(context_parts)

    # Step 5: send to Groq with a grounding instruction.
    #
    # Context goes in the user message (not the system message) because
    # llama-3.3-70b-versatile attends more reliably to content in the human
    # turn. The system message sets the role and the grounding rules; the user
    # message supplies both the retrieved chunks and the actual question.
    system_prompt = (
        "You are a helpful assistant for the CUNY City Tech Computer Science "
        "Unofficial Student Guide. Your job is to help students learn about "
        "CS professors based on real student reviews.\n\n"
        "Rules you must follow:\n"
        "- Answer ONLY from the student review excerpts provided in the user message.\n"
        "- Do NOT use any outside knowledge or make assumptions beyond the excerpts.\n"
        "- Do not invent quotes, grades, or statistics not present in the excerpts.\n"
        "- Write a clear, concise answer in 2-4 sentences.\n"
        "- If the excerpts truly contain no relevant information, respond with exactly: "
        "\"I don't have enough information in my knowledge base to answer this question.\""
    )

    user_message = (
        f"Here are student review excerpts retrieved for your question:\n\n"
        f"{context}\n\n"
        f"Question: {question}"
    )

    response = _groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,
        max_tokens=512,
    )
    answer = response.choices[0].message.content.strip()

    # Step 6: build source list from metadata — deduplicated, programmatic
    seen         = set()
    source_lines = []
    for chunk in chunks:
        meta = chunk["metadata"]
        # Deduplicate by (professor, source URL) — multiple chunks from the same
        # page should appear as one source entry, not five.
        dedup_key = (meta.get("professor", ""), meta.get("url", ""))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        prof   = meta.get("professor", "Unknown")
        course = meta.get("course",    "N/A")
        src    = meta.get("source",    "N/A")
        url    = meta.get("url",       "")

        line = f"  Professor : {prof}\n  Course    : {course}\n  Source    : {src}\n  URL       : {url}"
        source_lines.append(line)

    sources_text = "\n\n".join(source_lines) if source_lines else "No sources."
    return answer, sources_text


# ── Step 7: Gradio interface ─────────────────────────────────────────────────
#
# Blocks layout gives us three clearly separated areas:
#   • question_box  — where the student types their question
#   • answer_box    — the LLM's grounded response
#   • sources_box   — the programmatically generated source list
#
# Both Enter (question_box.submit) and the button click trigger the same handler.

def handle_question(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    return rag_pipeline(question)


with gr.Blocks(title="City Tech CS Unofficial Guide") as demo:
    gr.Markdown(
        "# City Tech CS Unofficial Student Guide\n"
        "Ask questions about CS professors based on real student reviews from "
        "RateMyProfessor, Reddit, and Koofers. Answers are grounded only in "
        "retrieved documents — no hallucination."
    )

    with gr.Row():
        question_box = gr.Textbox(
            label="Your Question",
            placeholder="e.g. What do students say about Tong Yi's workload?",
            lines=2,
            scale=4,
        )
        submit_btn = gr.Button("Ask", variant="primary", scale=1, min_width=80)

    answer_box = gr.Textbox(
        label="Answer",
        lines=6,
        interactive=False,
    )
    sources_box = gr.Textbox(
        label="Sources Used",
        lines=6,
        interactive=False,
    )

    submit_btn.click(
        fn=handle_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=handle_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()

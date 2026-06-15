# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This system covers student reviews and experiences with Hunter College Computer Science professors. The five professors it covers are Tong Yi, Eric Schweitzer, Subash Shankar, Tiziana Ligorio, and Saad Mneimneh.

This kind of information is hard to find through official channels because course descriptions only tell you what a class covers, not what it is actually like to take it. Student feedback about teaching style, workload, exam difficulty, and grading is scattered across Rate My Professors and Reddit threads that are easy to miss. This system pulls that information together so students can ask specific questions and get answers based on real reviews in one place.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Tong Yi — Rate My Professors | RMP reviews | https://www.ratemyprofessors.com/professor/2634841 |
| 2 | Tong Yi — Reddit r/HunterCollege | Reddit thread | https://www.reddit.com/r/HunterCollege/comments/v6kzhw/for_those_who_have_tong_yi_for_cs_how_bad_is_she/ |
| 3 | Eric Schweitzer — Rate My Professors | RMP reviews | https://www.ratemyprofessors.com/professor/257192 |
| 4 | Eric Schweitzer — Reddit r/HunterCollege | Reddit thread | https://www.reddit.com/r/HunterCollege/comments/1l7feml/csci_49390_with_eric_schweitzer/ |
| 5 | Subash Shankar — Rate My Professors | RMP reviews | https://www.ratemyprofessors.com/professor/257190 |
| 6 | Subash Shankar — Reddit r/HunterCollege | Reddit thread | https://www.reddit.com/r/HunterCollege/comments/1rz0e2c/csci260_w_shankur/ |
| 7 | Tiziana Ligorio — Rate My Professors | RMP reviews | https://www.ratemyprofessors.com/professor/815879 |
| 8 | Tiziana Ligorio — Reddit r/HunterCollege | Reddit thread | https://www.reddit.com/r/HunterCollege/comments/scpbo2/opinions_on_prof_tiziana_ligorio/ |
| 9 | Saad Mneimneh — Rate My Professors | RMP reviews | https://www.ratemyprofessors.com/professor/926045 |
| 10 | Saad Mneimneh — Reddit r/HunterCollege | Reddit thread | https://www.reddit.com/r/HunterCollege/comments/b2pg0t/how_did_you_pass_csci_150_discrete_math/ |

---

## Chunking Strategy

**Chunk size:** Up to 200 tokens per chunk, with a 30-token overlap on chunks that needed to be split.

**Overlap:** 30 tokens. When a review or comment was long enough to require splitting, the split chunks share 30 tokens at the boundary so neither chunk loses the context it needs to make sense on its own.

**Why these choices fit your documents:** My original plan was to use large token chunks with significant overlap, but after looking at my actual documents I changed my approach. Rate My Professors reviews and Reddit comments are already short and self-contained — most fit in a single chunk without any splitting at all. It made more sense to treat each review or comment as its own chunk rather than arbitrarily slicing up the text. The 200-token limit and 30-token overlap only kick in for longer Reddit posts that would otherwise be too big to chunk cleanly.

**Final chunk count:** 44 chunks across all 10 documents.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers. This model produces 384-dimensional vectors and runs locally with no API cost.

**Production tradeoff reflection:** For a real deployment, I would look at models with higher accuracy on short, informal text — student reviews use slang and abbreviations that a general-purpose model sometimes misses. A larger model like `text-embedding-3-large` from OpenAI would likely do better on domain-specific vocabulary, but it adds API cost and latency per query. I would also consider whether multilingual support matters. Since all my documents are in English, that was not a concern here, but a system covering a more diverse student body might need it. For this project, `all-MiniLM-L6-v2` was a practical and fast choice.

---

## Retrieval Approach

The system embeds the user's question using the same `all-MiniLM-L6-v2` model used to embed the chunks. ChromaDB then finds the top 5 chunks whose vectors are closest to the question vector using cosine similarity.

If the question mentions a professor's name, the system applies a metadata filter before running the similarity search. This scopes retrieval to only that professor's chunks. Without the filter, a question about one professor could return chunks from another professor whose reviews happen to use more matching words.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt tells the model it is an assistant for a student guide and gives it four rules: answer only from the review excerpts in the user message, do not use outside knowledge, do not invent quotes or statistics, and if the excerpts have no relevant information respond with exactly "I don't have enough information in my knowledge base to answer this question." The context chunks are placed in the user message rather than the system message because the model attends to them more reliably there.

**How source attribution is surfaced in the response:** Source attribution is built in Python after the LLM call, not generated by the model. The code reads the metadata from each retrieved chunk and formats a source entry showing the professor name, course, source platform, and URL. Chunks from the same URL are deduplicated so the same page does not appear more than once. The result is displayed in a separate Sources box in the Gradio interface.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Tong Yi's workload or homework difficulty? | Heavy workload, lots of homework, difficult tests | Students consistently mention lots of homework and hard exams; doing all labs and attendance items helps with the grade | Relevant | Accurate |
| 2 | How do students describe Eric Schweitzer's teaching style or clarity? | Pop quizzes, self-study required, manageable with effort | Fair but challenging, quizzes are 60% of the grade, material is taught abstractly and requires self-study | Relevant | Accurate |
| 3 | What do students say about Subash Shankar's grading style or fairness? | Tough grader, difficult exams, effort can help | Described as a tough grader with very strict grading that leaves little room for error; grading is based on few things and the course relies on a curve | Relevant | Accurate |
| 4 | How do students rate Tiziana Ligorio's approachability or office hours? | Helpful, approachable, willing to assist | Mixed experiences — one student attended office hours frequently with no issues, another had a negative experience with TAs in the lab; Ligorio herself is described as kind, caring, and interactive | Partially relevant | Partially accurate |
| 5 | What is the overall sentiment students express about Saad Mneimneh's courses? | Challenging but rewarding, good for problem-solving | Exams described as hard and unorthodox; students recommend grinding practice problems and forming study groups | Relevant | Accurate |

---

## Failure Case Analysis

**Question that failed:** "What do students say about Tong Yi's workload or homework difficulty?"

**What the system returned:** Before I added metadata filtering, the top retrieved chunks came from Shankar and Schweitzer rather than Tong Yi, even though the question is specifically about Tong Yi.

**Root cause (tied to a specific pipeline stage):** This is a retrieval-stage failure. Tong Yi's reviews rarely use the word "workload" directly. During similarity search, ChromaDB found chunks from other professors whose reviews happened to use words that matched the query better. The embedding model had no way to know the question was about a specific person — it only compares meaning, not intent.

**What you would change to fix it:** I fixed this by adding professor metadata filtering. When a professor's name is detected in the question, the system now filters ChromaDB to only search within that professor's chunks before running the similarity search. This guarantees the retrieved chunks are always from the right professor.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the chunking strategy in `planning.md` before coding forced me to think about the structure of my documents early. When I actually looked at my files, I realized the original plan for large chunks with heavy overlap did not fit short reviews at all. Having the spec written down made it easy to see where my assumptions were wrong and adjust before writing any pipeline code.

**One way your implementation diverged from the spec, and why:** The architecture diagram in my spec originally listed "Claude LLM" as the generation model, but I ended up using Groq's `llama-3.3-70b-versatile`. I also found through testing that putting the context in the user message rather than the system message produced much better results — the model followed grounding instructions more reliably that way. This was not something I anticipated in the spec; I discovered it by testing and debugging the actual outputs.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* My Chunking Strategy section from `planning.md` and the structure of my `.txt` document files, including the `===` metadata separator and `---` review separator format.
- *What it produced:* A complete ingestion and chunking pipeline in `ingest.py` with a `parse_file()` function, a `secondary_split()` function for long chunks, and a `build_chunks()` function that attached metadata to every chunk.
- *What I changed or overrode:* I changed the chunking approach after reviewing my actual documents. My original spec called for larger token chunks, but since most of my reviews were already short and self-contained, I switched to treating each review as its own chunk and only splitting when a review exceeded 200 tokens. I directed the AI to implement that updated strategy instead.

**Instance 2**

- *What I gave the AI:* My Retrieval Approach section from `planning.md` and the output structure from `ingest.py`, and described the failure case where retrieval was pulling chunks from the wrong professor.
- *What it produced:* The embedding and retrieval pipeline in `embed.py`, including the `query()` function with an optional `where` parameter for ChromaDB metadata filtering.
- *What I changed or overrode:* The initial version did not include professor metadata filtering. After I found that professor-specific questions were returning chunks from other professors, I directed the AI to add a `detect_professor()` function in `app.py` that checks the question for a known professor name and passes a `where` filter to ChromaDB before similarity scoring runs.

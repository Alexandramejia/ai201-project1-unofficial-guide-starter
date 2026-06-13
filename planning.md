# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Domain:** Student reviews and experiences with Hunter College Computer Science professors.

This knowledge is difficult to find because student feedback is scattered across platforms like Rate My Professors and Reddit, is highly opinion-based and unstructured, and often buried in comment threads that are hard to search. This system organizes that scattered feedback into a searchable format so students can quickly find information about a specific professor's teaching style, exam difficulty, grading practices, workload, and whether other students recommend them — all in one place.

**Questions this system will answer:**
1. Is Tong Yi a good professor for intro CS at Hunter?
2. How hard are Saad Mneimneh's exams and does he curve?
3. What's the workload like for Tiziana Ligorio's classes?
4. Does Subash Shankar post lecture notes online?
5. Should I take Eric Schweitzer for CSCI 49390?
6. Which Hunter CS professor is easiest for discrete math?
7. How do students typically prepare for Mneimneh's exams?
8. Is Ligorio's class more project-based or exam-based?
9. What do students say about Tong Yi's grading?
10. Who is the most recommended CS professor at Hunter for data structures?

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Tong Yi — Rate My Professors | 123 student ratings (2.2/5); covers teaching effectiveness, exam difficulty, grading, overall recommendation. 54% of ratings are 1-star "Awful." | https://www.ratemyprofessors.com/professor/2634841 |
| 2 | Tong Yi — Reddit r/HunterCollege | Thread asking students about their CS experience with Tong Yi. Contains direct student accounts of teaching style, difficulty, and whether to take her. | https://www.reddit.com/r/HunterCollege/comments/v6kzhw/for_those_who_have_tong_yi_for_cs_how_bad_is_she/ |
| 3 | Eric Schweitzer — Rate My Professors | Student ratings page for Schweitzer; covers course difficulty, grading, and teaching style across multiple CS courses. | https://www.ratemyprofessors.com/professor/257192 |
| 4 | Eric Schweitzer — Reddit r/HunterCollege | Thread specifically about CSCI 49390 with Schweitzer. Students discuss course content, what to expect, and workload. | https://www.reddit.com/r/HunterCollege/comments/1l7feml/csci_49390_with_eric_schweitzer/ |
| 5 | Subash Shankar — Rate My Professors | 82 ratings (2.7/5, 4.2/5 difficulty, 28% would take again). Reviews confirm he does not post notes to Brightspace and provides no practice exams. | https://www.ratemyprofessors.com/professor/257190 |
| 6 | Subash Shankar — Reddit r/HunterCollege | Thread about CSCI 260 with Shankar. Students share experiences on note-taking expectations, exam preparation, and workload. | https://www.reddit.com/r/HunterCollege/comments/1rz0e2c/csci260_w_shankur/ |
| 7 | Tiziana Ligorio — Rate My Professors | 118 ratings (3.1/5, 3.4/5 difficulty); sharply polarized — 40 students rated her Awesome and 41 rated her Awful. Covers teaching style and grading. | https://www.ratemyprofessors.com/professor/815879 |
| 8 | Tiziana Ligorio — Reddit r/HunterCollege | Open discussion thread asking for opinions on Ligorio. Students debate her teaching approach, whether to take her, and course experience. | https://www.reddit.com/r/HunterCollege/comments/scpbo2/opinions_on_prof_tiziana_ligorio/ |
| 9 | Saad Mneimneh — Rate My Professors | 128 ratings (3.4/5, 4.4/5 difficulty, 58% would take again). Reviews confirm he curves exams, grading is test-heavy, and exams require 1–2 weeks of intensive prep. | https://www.ratemyprofessors.com/professor/926045 |
| 10 | Saad Mneimneh — Reddit r/HunterCollege | Thread on how students passed CSCI 150 (Discrete Math). Students share study strategies, how they prepared, and general survival advice for his course. | https://www.reddit.com/r/HunterCollege/comments/b2pg0t/how_did_you_pass_csci_150_discrete_math/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An Agentic RAG chatbot over the Runway 2.0 platform docs (Korean). An LLM agent decides when to search a Qdrant vector DB vs. read full curated guide files, and the Streamlit UI visualizes every tool call. Built as a learning/practice project for agentic tool-use loops. README.md is the canonical user-facing doc (in Korean).

## Key architectural facts (non-obvious)

- **`rag_core.py` is the center of gravity.** It holds all UI/provider-agnostic logic: config, model loaders, token-aware chunking, hybrid retrieval, the self-RAG gate, the secure file read, the tool definitions/system prompt, and the agentic loop as an event generator (`run_agent`) plus a headless `answer()`. `rag_app.py` (Streamlit), `evaluate_rag.py`, and `ingest_qdrant.py` all import from it. **Put new core logic here, not in the UI.** There is intentionally no Streamlit and no API-key handling in `rag_core`.
- **The "Anthropic" client talks to MiniMax, not Anthropic.** Uses the `anthropic` SDK with `base_url=https://api.minimax.io/anthropic`, model `MiniMax-M2.7`. Anthropic-API-compatible, so tool-use/streaming message formats work unchanged. API keys are MiniMax JWTs. Caveat: streaming / prompt-caching support on the MiniMax endpoint is not guaranteed; the core exposes a non-streaming path (`run_agent(..., stream=False)`).
- **Two-tier knowledge base, two tools:**
  - `docs_markdown/` — fine-grained scraped docs → embedded into Qdrant → reached via `search_runway_docs` (hybrid retrieval).
  - `skills/` — 5 hand-curated guide files → read whole via `read_raw_document`. The whitelist lives in `rag_core.ALLOWED_SKILL_FILES` AND the tool schema in `rag_core.TOOLS`; update **both** if you add/rename a skill file.
- **Hybrid retrieval** (`rag_core.retrieve`): dense (`jhgan/ko-sbert-multitask`) + BM25 sparse (FastEmbed `Qdrant/bm25`) stored as Qdrant **named vectors** (`dense` + `bm25`), fused with RRF via `query_points`. Optional cross-encoder rerank (`Dongjin-kr/ko-reranker`). Degrades gracefully to dense-only (and then to legacy unnamed search) if fastembed is missing or the Qdrant server is < 1.10.
- **Code-level self-RAG gate:** confidence = **top-1 dense cosine** (computed separately, because RRF fusion scores are not comparable to a cosine threshold). If it's below `LOW_CONFIDENCE_THRESHOLD` (0.40, uncalibrated — tune with `evaluate_rag.py`), `format_retrieval_for_model` injects a hard re-query/abstain instruction into the tool output. The system prompt also asks for a `출처:` citation section.
- **Token-aware chunking** (`rag_core.split_to_token_windows`): sized to the embedder's real budget — `jhgan/ko-sbert-multitask` is **max_seq_length 128 tokens** (verified), so char-based windows silently truncate. `chunk_markdown` splits on headings then token-windows long sections, reserving `PREFIX_TOKEN_BUDGET` for the `Source:`/`Context:` breadcrumb.
- **Security:** `secure_skill_read` uses basename + whitelist + realpath containment (LLM-supplied paths are untrusted). `rag_app.render_traces` HTML-escapes all dynamic content rendered under `unsafe_allow_html`.
- **Multi-turn memory:** `rag_app.py` rebuilds messages from the last `MAX_HISTORY_MESSAGES` of `st.session_state.chat_history` (text-only replay; leading non-user turns trimmed for a valid user-first sequence).
- **`.env` parsing is hand-rolled** (no python-dotenv). Keys named `MINIMAX1`, `MINIMAX2`, … are auto-discovered (any env var starting with `MINIMAX`, case-insensitive); the sidebar picks one.
- **Ingestion is incremental + hybrid.** `ingest_qdrant.py` hashes each file (`.ingest_manifest.json`), re-indexes only changed files (delete-by-`metadata.source` then upsert with deterministic uuid5 IDs), and creates a named-vector (dense+bm25) collection. `--full` drops & recreates. **Migration:** named vectors are incompatible with the old single/unnamed-vector collection — run `python ingest_qdrant.py --full` once after upgrading.

## Pipeline / data flow

1. `scrape_docs.py` — reads the saved `getting-started.html`, extracts sidebar links, fetches each page, and pulls raw markdown out of the `<script id="page-markdown-source">` JSON blob. Writes to `docs_markdown/` mirroring the URL path. (SSL verification is disabled for the target site.) Rarely re-run; output is committed.
2. `ingest_qdrant.py` — `rag_core.chunk_markdown` → dense + BM25 sparse embed → upsert into named-vector Qdrant collection `runway_docs`. Incremental via `.ingest_manifest.json`; `--full` recreates. Requires Qdrant ≥ 1.10 running.
3. `rag_core.py` — the reusable core (see above). Also runnable headless via `rag_core.answer(...)`.
4. `rag_app.py` — thin Streamlit UI; consumes `rag_core.run_agent` events for streaming + trace visualization.
5. `evaluate_rag.py` — offline retrieval harness; runs a golden Q&A set through `rag_core.retrieve` (same path as prod) and reports Hit@K / MRR@K. No LLM/API needed.
6. `SKILLS.md` — reference doc cataloguing the reusable patterns (and anti-patterns) for building other systems from this one.

## Commands

Primary entry point is the interactive launcher (Windows):

```bat
run_chatbot.bat
```

It creates `.venv`, installs `requirements.txt`, then offers a menu: [1] ingest, [2] start chatbot, [3] both, [4] download+start Qdrant standalone, [5] exit.

Manual equivalents (activate `.venv\Scripts\activate.bat` first):

```bat
qdrant\qdrant.exe              :: start Qdrant on :6333 (>= 1.10 for hybrid; must run before ingest AND queries)
python ingest_qdrant.py        :: incremental index of docs_markdown/ (only changed files)
python ingest_qdrant.py --full :: drop & recreate the named-vector (dense+bm25) collection
python evaluate_rag.py         :: retrieval quality report (Hit@K / MRR@K); --k N, --rerank
streamlit run rag_app.py       :: launch the chatbot UI (http://localhost:8501)
python scrape_docs.py          :: re-scrape docs from the source site into docs_markdown/
```

Qdrant must be up (`localhost:6333`) for both ingestion and querying. Hybrid search needs `fastembed` installed (in `requirements.txt`) and Qdrant server ≥ 1.10; both degrade gracefully to dense-only otherwise. There is no test suite, linter, or build step configured.

## Setup prerequisite

A project-root `.env` with MiniMax keys is required to use the chatbot:

```env
MINIMAX1=your_minimax_jwt
MINIMAX2=your_minimax_jwt
```

## Conventions

- All user-facing text and the agent's system prompt enforce **Korean** responses; keep new UI strings and prompts in Korean to match.
- `.venv/`, `qdrant/`, and `.env` are local/generated — don't commit them.

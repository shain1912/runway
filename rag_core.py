"""
Provider- and UI-agnostic core for the Runway Agentic RAG system.

This module holds the reusable parts (the bits worth copying into other systems):
- central config + lazily-loaded singletons (dense embedder, BM25 sparse, reranker)
- token-aware markdown chunking (sized to the embedder's real token budget)
- hybrid retrieval: dense + BM25 sparse fused with RRF, optional cross-encoder rerank
- a code-level self-RAG confidence gate (not just a prompt suggestion)
- security-guarded local file reads (whitelist + path-traversal containment)
- the agentic tool-use loop as an event generator (run_agent), consumable by any
  front-end (Streamlit, FastAPI, CLI), plus a headless answer() helper with retry

It deliberately contains NO Streamlit and NO API-key handling so it can be reused
and unit-tested independently of the UI.
"""
import os
import time

from qdrant_client import models

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "runway_docs"
DOCS_DIR = "docs_markdown"
SKILLS_DIR = "skills"

DENSE_MODEL_NAME = "jhgan/ko-sbert-multitask"
SPARSE_MODEL_NAME = "Qdrant/bm25"
RERANKER_MODEL_NAME = "Dongjin-kr/ko-reranker"

DENSE_VECTOR = "dense"     # named vector keys in the Qdrant collection
SPARSE_VECTOR = "bm25"

# Self-RAG gate: when the top dense cosine score is below this, we inject a hard
# instruction telling the agent to re-query or abstain. ko-sbert cosine scores are
# uncalibrated, so tune this per corpus (use evaluate_rag.py to find a good value).
LOW_CONFIDENCE_THRESHOLD = 0.40

# Token-aware chunking
CHUNK_OVERLAP_TOKENS = 32
PREFIX_TOKEN_BUDGET = 48   # reserve room for the "Source/Context" breadcrumb prefix

# Whitelist for read_raw_document (mirrors the tool schema below)
ALLOWED_SKILL_FILES = {
    "runway_intro_and_setup.md",
    "runway_development_and_app_creation.md",
    "runway_gpu_and_storage_configuration.md",
    "runway_model_serving_and_deployment.md",
    "runway_kubeconfig_and_administration.md",
}

# --------------------------------------------------------------------------
# Lazily-loaded model singletons (persist for the process lifetime)
# --------------------------------------------------------------------------
_dense_model = None
_sparse_model = None
_reranker = None


def load_dense_model():
    global _dense_model
    if _dense_model is None:
        from sentence_transformers import SentenceTransformer
        _dense_model = SentenceTransformer(DENSE_MODEL_NAME)
    return _dense_model


def load_sparse_model():
    """BM25 sparse encoder via FastEmbed. Returns None if fastembed is unavailable."""
    global _sparse_model
    if _sparse_model is None:
        try:
            from fastembed import SparseTextEmbedding
            _sparse_model = SparseTextEmbedding(SPARSE_MODEL_NAME)
        except Exception:
            return None
    return _sparse_model


def load_reranker(model_name=RERANKER_MODEL_NAME):
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(model_name)
        except Exception:
            return None
    return _reranker


# --------------------------------------------------------------------------
# Embedding helpers
# --------------------------------------------------------------------------
def embed_dense(texts, batch_size=32, show_progress_bar=False):
    return load_dense_model().encode(texts, batch_size=batch_size, show_progress_bar=show_progress_bar)


def embed_sparse(texts):
    """Yields fastembed SparseEmbedding objects (.indices, .values). [] if unavailable."""
    model = load_sparse_model()
    if model is None:
        return []
    return list(model.embed(list(texts)))


def to_sparse_vector(sparse_embedding):
    return models.SparseVector(
        indices=[int(i) for i in sparse_embedding.indices],
        values=[float(v) for v in sparse_embedding.values],
    )


# --------------------------------------------------------------------------
# Token-aware chunking (sized to the embedder's actual token budget)
# --------------------------------------------------------------------------
def split_to_token_windows(text, max_tokens, overlap_tokens=CHUNK_OVERLAP_TOKENS):
    """Slide a token window over `text` so no window exceeds the embedder's limit.
    Prevents silent truncation at embed time (the #1 retrieval-recall killer when
    chunk size is measured in characters instead of tokens)."""
    text = (text or "").strip()
    if not text:
        return []
    tokenizer = load_dense_model().tokenizer
    ids = tokenizer.encode(text, add_special_tokens=False)
    if len(ids) <= max_tokens:
        return [text]

    windows = []
    step = max(max_tokens - overlap_tokens, 1)
    start = 0
    while start < len(ids):
        chunk_ids = ids[start:start + max_tokens]
        decoded = tokenizer.decode(chunk_ids, skip_special_tokens=True).strip()
        if decoded:
            windows.append(decoded)
        if start + max_tokens >= len(ids):
            break
        start += step
    return windows


def _heading_sections(lines):
    """Yield (h1,h2,h3,h4, content) tuples split on markdown headings."""
    import re
    h1 = h2 = h3 = h4 = ""
    buf = []
    for line in lines:
        m1 = re.match(r"^#\s+(.+)$", line)
        m2 = re.match(r"^##\s+(.+)$", line)
        m3 = re.match(r"^###\s+(.+)$", line)
        m4 = re.match(r"^####\s+(.+)$", line)
        if m1 or m2 or m3 or m4:
            if "".join(buf).strip():
                yield (h1, h2, h3, h4, "".join(buf))
            buf = []
            if m1:
                h1, h2, h3, h4 = m1.group(1).strip(), "", "", ""
            elif m2:
                h2, h3, h4 = m2.group(1).strip(), "", ""
            elif m3:
                h3, h4 = m3.group(1).strip(), ""
            else:
                h4 = m4.group(1).strip()
        else:
            buf.append(line)
    if "".join(buf).strip():
        yield (h1, h2, h3, h4, "".join(buf))


def chunk_markdown(file_path, docs_dir=DOCS_DIR):
    """Heading-aware + token-windowed chunks with a context breadcrumb baked in."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rel_path = os.path.relpath(file_path, docs_dir)
    clean_source = rel_path.replace("\\", " > ").replace("/", " > ").replace("index.md", "").strip(" > ")

    max_tokens = max(int(load_dense_model().max_seq_length) - PREFIX_TOKEN_BUDGET, 64)

    chunks = []
    for h1, h2, h3, h4, content in _heading_sections(lines):
        header_context = " > ".join([h for h in [h1, h2, h3, h4] if h])
        for part in split_to_token_windows(content, max_tokens):
            full_text = f"Source: {clean_source}\nContext: {header_context}\n\nContent:\n{part}"
            chunks.append({
                "text": full_text,
                "metadata": {
                    "source": rel_path, "h1": h1, "h2": h2, "h3": h3, "h4": h4,
                    "clean_source": clean_source,
                },
            })
    return chunks


# --------------------------------------------------------------------------
# Security: guarded skill-file read (whitelist + traversal containment)
# --------------------------------------------------------------------------
def secure_skill_read(file_path, skills_dir=SKILLS_DIR):
    name = os.path.basename((file_path or "").strip())  # strip any directory components
    if name not in ALLOWED_SKILL_FILES:
        return f"Error: '{file_path}' is not an allowed skill file."
    root = os.path.realpath(skills_dir)
    full = os.path.realpath(os.path.join(root, name))
    if full != root and not full.startswith(root + os.sep):
        return "Error: path traversal blocked."
    if not os.path.exists(full):
        return f"Error: File '{name}' does not exist."
    try:
        with open(full, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as ex:
        return f"Error reading file: {ex}"


# --------------------------------------------------------------------------
# Retrieval: hybrid (dense + BM25 sparse, RRF) -> optional rerank -> self-RAG gate
# --------------------------------------------------------------------------
def retrieve(qdrant_client, query, top_k=4, use_reranker=False,
             reranker_model=RERANKER_MODEL_NAME, collection=COLLECTION_NAME):
    """Returns (results, meta).
    results: list of {source, text, score}
    meta: {mode, confidence, low_confidence, count}
    """
    dense_vec = [float(x) for x in embed_dense([query])[0]]
    candidate_k = max(top_k * 4, top_k) if use_reranker else max(top_k * 2, top_k)

    # Confidence signal: top-1 dense cosine (comparable across queries, unlike RRF scores)
    confidence = 0.0
    try:
        conf = qdrant_client.query_points(
            collection_name=collection, query=dense_vec, using=DENSE_VECTOR,
            limit=1, with_payload=False,
        ).points
        confidence = float(conf[0].score) if conf else 0.0
    except Exception:
        pass

    mode = "hybrid"
    points = None
    sparse_list = embed_sparse([query])
    if sparse_list:
        try:
            sv = to_sparse_vector(sparse_list[0])
            points = qdrant_client.query_points(
                collection_name=collection,
                prefetch=[
                    models.Prefetch(query=dense_vec, using=DENSE_VECTOR, limit=candidate_k),
                    models.Prefetch(query=sv, using=SPARSE_VECTOR, limit=candidate_k),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=candidate_k, with_payload=True,
            ).points
        except Exception:
            points = None

    if points is None:
        mode = "dense"
        try:
            points = qdrant_client.query_points(
                collection_name=collection, query=dense_vec, using=DENSE_VECTOR,
                limit=candidate_k, with_payload=True,
            ).points
        except Exception:
            # last resort: legacy unnamed-vector collections
            points = qdrant_client.search(
                collection_name=collection, query_vector=dense_vec, limit=candidate_k,
            )
            if confidence == 0.0 and points:
                confidence = float(points[0].score)

    results = [{
        "source": (p.payload.get("metadata") or {}).get("source", "Unknown"),
        "text": p.payload.get("page_content", ""),
        "score": float(getattr(p, "score", 0.0) or 0.0),
    } for p in points]

    if use_reranker and results:
        reranker = load_reranker(reranker_model)
        if reranker is not None:
            scores = reranker.predict([(query, r["text"]) for r in results])
            ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            results = [r for r, _ in ranked]
            mode += "+rerank"

    results = results[:top_k]
    return results, {
        "mode": mode,
        "confidence": confidence,
        "low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
        "count": len(results),
    }


def format_retrieval_for_model(results, meta):
    """Render retrieval output for the LLM, embedding the code-level self-RAG gate."""
    header = f"[검색모드: {meta['mode']} | 신뢰도(top cosine): {meta['confidence']:.3f}]"
    if meta["low_confidence"]:
        header += (
            f"\n[경고] 최고 유사도가 임계값({LOW_CONFIDENCE_THRESHOLD:.2f}) 미만입니다. "
            "이 결과만으로 단정하지 마십시오. 검색어를 바꿔 search_runway_docs를 다시 호출하거나 "
            "read_raw_document로 보강하고, 그래도 근거가 없으면 '제공된 문서에서 확인되지 않습니다'라고 답하십시오."
        )
    if not results:
        return header + "\n\nQdrant에서 일치하는 문서 조각을 찾을 수 없습니다."
    body = "\n\n---\n\n".join(f"Source: {r['source']}\n{r['text']}" for r in results)
    return header + "\n\n" + body


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
TOOLS = [
    {
        "name": "search_runway_docs",
        "description": (
            "Runway 2.0 플랫폼 가이드 문서를 하이브리드(밀집+BM25) 검색하여 관련 조각(Top-K)을 가져옵니다. "
            "스토리지 볼륨, GPU 할당, Helm values.yaml, 추론 배포, Kubeconfig 등 플랫폼 제어 정보를 조각 단위로 찾을 때 호출합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "한글/영어 검색 쿼리 (예: 'GPU 할당', 'ceph-block 볼륨 생성')"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_raw_document",
        "description": (
            "특정 스킬 마크다운 파일의 원본 전문을 통째로 읽어옵니다. yaml 스키마 예제나 전체 관리 절차를 정독할 때 유용합니다. "
            "아래 5개 파일명 중 정확히 하나만 입력하십시오."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "다음 중 하나: 'runway_intro_and_setup.md', 'runway_development_and_app_creation.md', "
                        "'runway_gpu_and_storage_configuration.md', 'runway_model_serving_and_deployment.md', "
                        "'runway_kubeconfig_and_administration.md'"
                    ),
                }
            },
            "required": ["file_path"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are an expert AI MLOps Operator specifically designed for the Runway 2.0 platform.\n"
    "Answer the user's questions using your tools.\n"
    "Use 'search_runway_docs' for semantic/keyword retrieval, and 'read_raw_document' for the full, exact "
    "layout/specification of a specific skills file.\n"
    "\n"
    "## 검색 결과 자기평가 (Self-correction)\n"
    "- 검색 결과 머리말의 '신뢰도(top cosine)' 점수와 '[경고]' 표시를 반드시 확인하십시오.\n"
    "- 경고가 있거나 조각이 질문과 무관하면, 답을 지어내지 말고 검색어를 바꿔 다시 검색하거나 read_raw_document로 보강하십시오.\n"
    "- 검색과 정독을 모두 시도했는데도 근거가 없으면 정직하게 '제공된 문서에서 확인되지 않습니다'라고 답하십시오.\n"
    "\n"
    "## 출처 표기 (Citations)\n"
    "- 답변은 확보한 근거에 기반해야 합니다.\n"
    "- 답변 맨 끝에 '---' 구분선과 '출처:' 섹션을 두고, 실제 사용한 조각의 Source 경로를 불릿으로 나열하십시오(중복은 한 번만).\n"
    "\n"
    "Always reply in Korean. Maintain a precise, professional engineering tone."
)


def execute_tool(name, tool_input, qdrant_client, top_k=4, use_reranker=False,
                 reranker_model=RERANKER_MODEL_NAME, collection=COLLECTION_NAME):
    """Run one tool call. Returns (output_str, meta)."""
    if name == "search_runway_docs":
        if qdrant_client is None:
            return "Error: Qdrant client is not available.", {}
        query = tool_input.get("query", "")
        results, meta = retrieve(qdrant_client, query, top_k, use_reranker, reranker_model, collection)
        meta = dict(meta)
        meta["query"] = query
        return format_retrieval_for_model(results, meta), meta
    if name == "read_raw_document":
        fp = tool_input.get("file_path", "")
        return secure_skill_read(fp), {"file": os.path.basename((fp or "").strip())}
    return f"Error: Unknown tool '{name}'.", {}


# --------------------------------------------------------------------------
# Agentic loop (event generator) + headless helper
# --------------------------------------------------------------------------
def _with_retry(fn, retries=2, base_delay=1.0):
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(base_delay * (2 ** attempt))


def run_agent(client, model, messages, *, qdrant_client, system_prompt=SYSTEM_PROMPT,
              top_k=4, use_reranker=False, reranker_model=RERANKER_MODEL_NAME,
              collection=COLLECTION_NAME, max_tokens=4000, max_loops=5, stream=True):
    """Drive the tool-use loop, yielding events so any front-end can render them.

    Mutates `messages` in place (pass a fresh list per turn). Event types:
      loop_start, text_delta, tool_start, tool_result, final, error, max_loops
    """
    traces = []
    for loop in range(1, max_loops + 1):
        yield {"type": "loop_start", "n": loop, "max": max_loops}

        try:
            if stream:
                accumulated = ""
                with client.messages.stream(
                    model=model, max_tokens=max_tokens, system=system_prompt,
                    messages=messages, tools=TOOLS,
                ) as s:
                    for delta in s.text_stream:
                        accumulated += delta
                        yield {"type": "text_delta", "text": delta, "accumulated": accumulated}
                    response = s.get_final_message()
            else:
                response = _with_retry(lambda: client.messages.create(
                    model=model, max_tokens=max_tokens, system=system_prompt,
                    messages=messages, tools=TOOLS,
                ))
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return

        content = response.content
        assistant_text = "\n".join(b.text for b in content if b.type == "text")
        tool_uses = [b for b in content if b.type == "tool_use"]

        if response.stop_reason != "tool_use" or not tool_uses:
            yield {"type": "final", "text": assistant_text, "traces": traces}
            return

        assistant_content = []
        for b in content:
            if b.type == "text":
                assistant_content.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                assistant_content.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        messages.append({"role": "assistant", "content": assistant_content})

        tool_result_blocks = []
        for tu in tool_uses:
            yield {"type": "tool_start", "name": tu.name, "args": tu.input}
            out, meta = execute_tool(tu.name, tu.input, qdrant_client, top_k, use_reranker, reranker_model, collection)
            traces.append({"tool_name": tu.name, "args": str(tu.input), "result": out, "meta": meta})
            yield {"type": "tool_result", "name": tu.name, "args": tu.input, "result": out, "meta": meta}
            tool_result_blocks.append({"type": "tool_result", "tool_use_id": tu.id, "content": out})

        messages.append({"role": "user", "content": tool_result_blocks})

    yield {"type": "max_loops", "traces": traces}


def answer(question, *, api_key, base_url, model, qdrant_client, history=None, **kwargs):
    """Headless one-shot: run the agent without streaming and return the final text.
    Demonstrates that the core is usable with no UI (CLI, API, tests, batch eval)."""
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key, base_url=base_url,
                       default_headers={"Authorization": f"Bearer {api_key}"})
    messages = list(history or [])
    messages.append({"role": "user", "content": question})
    final = None
    for ev in run_agent(client, model, messages, qdrant_client=qdrant_client, stream=False, **kwargs):
        if ev["type"] == "final":
            final = ev["text"]
        elif ev["type"] == "error":
            return f"[error] {ev['message']}"
    return final if final is not None else "[no answer: max loops reached]"

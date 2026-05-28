import os
import html

import streamlit as st
from qdrant_client import QdrantClient
from anthropic import Anthropic

import rag_core as core

# Try to load environment variables from local .env file manually (zero-dependency)
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as env_file:
            for env_line in env_file:
                env_line = env_line.strip()
                if env_line and not env_line.startswith("#") and "=" in env_line:
                    env_key, env_val = env_line.split("=", 1)
                    os.environ[env_key.strip()] = env_val.strip().strip("'").strip('"')
    except Exception:
        pass


# Streamlit App Configurations
st.set_page_config(
    page_title="Runway Agentic RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Harmonious premium dark glassmorphism custom CSS
st.markdown("""
<style>
    .main { background-color: #0d0e15; color: #e2e8f0; }
    .stSidebar { background-color: #161821; border-right: 1px solid #232731; }
    .stTextInput>div>div>input { background-color: #1a1c29; color: #ffffff; border: 1px solid #333946; }
    .stButton>button {
        background-image: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white; border: none; border-radius: 4px; padding: 0.5rem 1rem; transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4); }
    .tool-box { background-color: #161a22; border-left: 4px solid #7c3aed; border-radius: 4px; padding: 12px; margin: 10px 0; }
    .tool-header { font-weight: bold; color: #a78bfa; font-size: 0.95rem; margin-bottom: 6px; }
    .tool-body { font-family: monospace; font-size: 0.85rem; color: #cbd5e1; background-color: #0f1117; padding: 8px; border-radius: 4px; white-space: pre-wrap; }
</style>
""", unsafe_allow_html=True)


# ----------------- Helpers -----------------

@st.cache_resource
def warm_models():
    """Load the dense embedder once (download happens on first run)."""
    core.load_dense_model()
    return True


def get_qdrant_client(host, port):
    try:
        return QdrantClient(host=host, port=port, timeout=5)
    except Exception:
        return None


def render_traces(traces):
    """Render tool-execution traces. All dynamic content is HTML-escaped to avoid
    injection from document text rendered under unsafe_allow_html."""
    for trace in traces:
        name = html.escape(str(trace.get("tool_name", "")))
        args = html.escape(str(trace.get("args", "")))
        result = html.escape(str(trace.get("result", ""))[:800])
        st.markdown(f"""
        <div class="tool-box">
            <div class="tool-header">🛠️ Tool Called: {name}</div>
            <div class="tool-body">Arguments: {args}</div>
            <div style="font-size:0.8rem; margin-top:5px; color:#94a3b8;">Execution Output:</div>
            <div class="tool-body" style="background-color:#1e293b; max-height: 220px; overflow-y: auto;">{result}…</div>
        </div>
        """, unsafe_allow_html=True)


# ----------------- Sidebar Configuration -----------------

st.sidebar.title("🤖 Agentic RAG")
st.sidebar.markdown("---")

st.sidebar.header("1. API Key Config")
minimax_env_keys = sorted([k for k in os.environ.keys() if k.upper().startswith("MINIMAX")])
if minimax_env_keys:
    selected_key_name = st.sidebar.selectbox("Select MiniMax Key from .env", minimax_env_keys + ["Enter manually"])
    if selected_key_name != "Enter manually":
        minimax_api_key = os.environ[selected_key_name]
        st.sidebar.caption(f"Loaded key from `{selected_key_name}`")
    else:
        minimax_api_key = st.sidebar.text_input("Enter MiniMax API Key", type="password")
else:
    minimax_api_key = st.sidebar.text_input("MiniMax API Key", value=os.environ.get("MINIMAX_API_KEY", ""), type="password")

base_url = st.sidebar.text_input("Anthropic Base URL", value="https://api.minimax.io/anthropic")
model_name = st.sidebar.text_input("Claude Model", value="MiniMax-M2.7")
max_tokens = st.sidebar.number_input("Max Tokens (응답 최대 길이)", min_value=512, max_value=8192, value=4000, step=256)

st.sidebar.markdown("---")
st.sidebar.header("2. Vector DB (Qdrant)")
qdrant_host = st.sidebar.text_input("Qdrant Host", value=core.QDRANT_HOST)
qdrant_port = st.sidebar.number_input("Qdrant Port", value=core.QDRANT_PORT)
collection_name = st.sidebar.text_input("Collection Name", value=core.COLLECTION_NAME)
top_k = st.sidebar.slider("Number of chunks to retrieve (K)", min_value=1, max_value=8, value=4)
use_reranker = st.sidebar.checkbox(
    "크로스 인코더 리랭커 사용", value=False,
    help="하이브리드 후보를 K의 4배만큼 가져온 뒤 리랭킹하여 상위 K개만 사용합니다. 첫 실행 시 모델을 다운로드합니다."
)
reranker_model = st.sidebar.text_input("리랭커 모델", value=core.RERANKER_MODEL_NAME) if use_reranker else core.RERANKER_MODEL_NAME

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Agentic RAG**\n"
    "에이전트(LLM)가 질문을 분석해 하이브리드 검색(`search_runway_docs`) 또는 스킬 정독(`read_raw_document`) "
    "도구를 직접 선택·조합하고, 검색 신뢰도를 스스로 평가(self-RAG)하여 답변과 출처를 도출합니다."
)


# ----------------- App Main Layout -----------------

st.title("🤖 Agentic RAG - Runway AI Assistant")
st.markdown(
    "Runway 2.0 플랫폼 가이드봇 — **하이브리드 검색 + Self-RAG + Tool Use 기반 에이전틱 RAG**입니다.\n"
    "에이전트의 추론 흐름·도구 선택·검색 신뢰도를 실시간으로 모니터링할 수 있습니다."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

warm_models()
qdrant_client = get_qdrant_client(qdrant_host, qdrant_port)

# Qdrant status banner
if qdrant_client:
    try:
        names = [c.name for c in qdrant_client.get_collections().collections]
        if collection_name in names:
            st.success(f"🟢 Qdrant 연결 성공! 컬렉션 '{collection_name}' 정상 작동 중")
        else:
            st.warning(f"🟡 Qdrant 연결되었으나 '{collection_name}' 컬렉션이 없습니다. `python ingest_qdrant.py --full`을 먼저 실행하세요.")
    except Exception:
        st.error("🔴 Qdrant 서버 연결 실패. 포트 6333을 확인하세요. (하이브리드 검색은 Qdrant >= 1.10 필요)")
        qdrant_client = None
else:
    st.error("🔴 Qdrant 클라이언트 초기화 실패.")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("traces"):
            with st.expander("🛠️ 에이전트의 도구 실행 흔적 (Agent Action Traces)"):
                render_traces(message["traces"])


# ----------------- Chat Turn -----------------

if query := st.chat_input("Runway 2.0 플랫폼 가이드에 대해 질문해 보세요 (예: Triton 경로와 MLServer 경로가 어떻게 달라?)"):
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if not minimax_api_key:
        with st.chat_message("assistant"):
            st.error("🔴 사이드바에 MiniMax API Key를 먼저 입력해 주세요.")
        st.stop()

    try:
        client = Anthropic(
            api_key=minimax_api_key,
            base_url=base_url,
            default_headers={"Authorization": f"Bearer {minimax_api_key}"}
        )
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Anthropic SDK 클라이언트 생성 오류: {e}")
        st.stop()

    with st.chat_message("assistant"):
        status_ph = st.empty()
        stream_ph = st.empty()

        # Multi-turn memory: replay recent turns (chat_history already has the new query)
        MAX_HISTORY_MESSAGES = 12
        messages_sdk = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_history[-MAX_HISTORY_MESSAGES:]
        ]
        while messages_sdk and messages_sdk[0]["role"] != "user":
            messages_sdk.pop(0)

        traces = []
        final_answer = ""
        error_msg = None
        tool_status = None

        for ev in core.run_agent(
            client, model_name, messages_sdk,
            qdrant_client=qdrant_client, top_k=top_k,
            use_reranker=use_reranker, reranker_model=reranker_model,
            collection=collection_name, max_tokens=max_tokens, max_loops=5, stream=True,
        ):
            et = ev["type"]
            if et == "loop_start":
                status_ph.info(f"🤔 에이전트 추론 루프 {ev['n']}/{ev['max']}")
            elif et == "text_delta":
                stream_ph.markdown(f"> **에이전트 추론(실시간)**: {ev['accumulated']}")
            elif et == "tool_start":
                stream_ph.empty()
                tool_status = st.status(f"⚙️ 도구 실행: `{ev['name']}`", expanded=False)
                tool_status.write(f"args: `{ev['args']}`")
            elif et == "tool_result":
                meta = ev.get("meta", {})
                if ev["name"] == "search_runway_docs":
                    conf = meta.get("confidence")
                    conf_s = f"{conf:.3f}" if isinstance(conf, (int, float)) else "n/a"
                    warn = " ⚠️저신뢰" if meta.get("low_confidence") else ""
                    label = f"✅ 검색 완료 — mode={meta.get('mode')} · 신뢰도={conf_s}{warn} · {meta.get('count')}개"
                else:
                    label = f"✅ 정독 완료: skills/{meta.get('file')}"
                if tool_status is not None:
                    tool_status.update(label=label, state="complete")
                else:
                    st.write(label)
                traces.append({"tool_name": ev["name"], "args": str(ev["args"]), "result": ev["result"]})
            elif et == "final":
                final_answer = ev["text"]
                stream_ph.empty()
            elif et == "error":
                error_msg = ev["message"]

        status_ph.empty()

        if error_msg:
            st.error(f"API 호출 실패: {error_msg}")
            if not final_answer:
                final_answer = "MiniMax API 호출에 실패했습니다. API 키 / Base URL / 모델명을 확인해 주세요."

        if final_answer:
            st.markdown("### 🤖 최종 에이전트 답변")
            st.markdown(final_answer)
            if traces:
                with st.expander("🛠️ 에이전트의 도구 실행 흔적 (Agent Action Traces)"):
                    render_traces(traces)
            st.session_state.chat_history.append({"role": "assistant", "content": final_answer, "traces": traces})
        else:
            st.warning("에이전트가 답변을 생성하지 못했습니다. 추론 루프 한도 또는 API 상태를 점검해 주세요.")

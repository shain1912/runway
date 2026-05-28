import streamlit as st
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from anthropic import Anthropic
import os

# Try to load environment variables from local .env file manually (zero-dependency)
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as env_file:
            for env_line in env_file:
                env_line = env_line.strip()
                if env_line and not env_line.startswith("#") and "=" in env_line:
                    env_key, env_val = env_line.split("=", 1)
                    env_key = env_key.strip()
                    env_val = env_val.strip().strip("'").strip('"')
                    os.environ[env_key] = env_val
    except Exception as env_err:
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
    .main {
        background-color: #0d0e15;
        color: #e2e8f0;
    }
    .stSidebar {
        background-color: #161821;
        border-right: 1px solid #232731;
    }
    .stTextInput>div>div>input {
        background-color: #1a1c29;
        color: #ffffff;
        border: 1px solid #333946;
    }
    .stButton>button {
        background-image: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
    }
    .tool-box {
        background-color: #161a22;
        border-left: 4px solid #7c3aed;
        border-radius: 4px;
        padding: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .tool-header {
        font-weight: bold;
        color: #a78bfa;
        font-size: 0.95rem;
        margin-bottom: 6px;
    }
    .tool-body {
        font-family: monospace;
        font-size: 0.85rem;
        color: #cbd5e1;
        background-color: #0f1117;
        padding: 8px;
        border-radius: 4px;
    }
    .chunk-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 8px;
        border-radius: 4px;
        margin-top: 5px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Core Helper Functions -----------------

@st.cache_resource
def load_embedding_model():
    """Cache the embedding model so it doesn't reload on every interaction"""
    model_name = "jhgan/ko-sbert-multitask"
    return SentenceTransformer(model_name)

def get_qdrant_client(host, port):
    try:
        return QdrantClient(host=host, port=port, timeout=5)
    except Exception:
        return None

# ----------------- Sidebar Configuration -----------------

st.sidebar.title("🤖 Agentic RAG")
st.sidebar.markdown("---")

# 1. API Configuration
st.sidebar.header("1. API Key Config")

# Read all minimax keys from .env
minimax_env_keys = sorted([k for k in os.environ.keys() if k.upper().startswith("MINIMAX")])

if minimax_env_keys:
    # Offer dropdown selector for loaded minimax keys from .env
    selected_key_name = st.sidebar.selectbox(
        "Select MiniMax Key from .env",
        minimax_env_keys + ["Enter manually"]
    )
    if selected_key_name != "Enter manually":
        minimax_api_key = os.environ[selected_key_name]
        st.sidebar.caption(f"Loaded key value from environment variable: `{selected_key_name}`")
    else:
        minimax_api_key = st.sidebar.text_input("Enter MiniMax API Key", type="password")
else:
    minimax_api_key = st.sidebar.text_input(
        "MiniMax API Key", 
        value=os.environ.get("MINIMAX_API_KEY", ""), 
        type="password"
    )

base_url = st.sidebar.text_input("Anthropic Base URL", value="https://api.minimax.io/anthropic")
model_name = st.sidebar.text_input("Claude Model", value="MiniMax-M2.7")

# 2. Vector Database Config
st.sidebar.markdown("---")
st.sidebar.header("2. Vector DB (Qdrant)")
qdrant_host = st.sidebar.text_input("Qdrant Host", value="localhost")
qdrant_port = st.sidebar.number_input("Qdrant Port", value=6333)
collection_name = st.sidebar.text_input("Collection Name", value="runway_docs")
top_k = st.sidebar.slider("Number of chunks to retrieve (K)", min_value=1, max_value=8, value=4)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Agentic RAG 연습용 앱**\n"
    "본 시스템은 단순 문서 주입 RAG가 아닙니다. "
    "에이전트(LLM)가 사용자 질문을 분석한 후, 벡터 DB 검색(`search_runway_docs`) "
    "또는 로컬 정리 파일 정독(`read_raw_document`) 도구를 직접 선택하고 "
    "결과를 종합하여 스스로 최종 답변을 도출합니다."
)

# ----------------- Tool Definitions for Agent -----------------

tools_definition = [
    {
        "name": "search_runway_docs",
        "description": (
            "Runway 2.0 플랫폼 가이드 문서(Qdrant 벡터 DB)를 검색하여 관련 문서 조각(Top-K)들을 가져옵니다. "
            "스토리지 볼륨 설정, GPU 할당 룰, Helm values.yaml 수정법, 추론 배포, Kubeconfig 세팅 등 "
            "플랫폼 제어와 관련된 포괄적이고 최신의 사용 정보를 조각 단위로 가져오기 위해 호출합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Qdrant 벡터 데이터베이스 검색에 적합한 한글/영어 키워드 검색 쿼리 (예: 'GPU 할당', 'ceph-block 볼륨 생성')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_raw_document",
        "description": (
            "특정 정리된 로컬 마크다운 가이드 파일(Skills)의 원본 전문을 통째로 읽어옵니다. "
            "특정 분야에 대해 더 완벽하고 일관된 설정 파일(yaml) 스키마 예제나 관리 방법을 정독하여 "
            "정확한 설명을 작성하고 싶을 때 유용합니다. 제공되는 5개의 스킬 파일명 중 하나를 입력하십시오."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "읽어올 파일명. 반드시 다음 리스트 중 정확히 하나를 골라 기입해야 합니다:\n"
                        "- 'runway_intro_and_setup.md'\n"
                        "- 'runway_development_and_app_creation.md'\n"
                        "- 'runway_gpu_and_storage_configuration.md'\n"
                        "- 'runway_model_serving_and_deployment.md'\n"
                        "- 'runway_kubeconfig_and_administration.md'"
                    )
                }
            },
            "required": ["file_path"]
        }
    }
]

# ----------------- App Main Layout -----------------

st.title("🤖 Agentic RAG - Runway AI Assistant")
st.markdown(
    "Runway 2.0 플랫폼 가이드봇 - **Minimax API & Anthropic SDK Tool Use 기반의 에이전틱 RAG 연습 환경**입니다.\n"
    "에이전트가 생각 흐름(Reasoning Loop)을 거쳐 필요한 도구를 직접 선택하고 문서를 읽는 전 과정을 실시간으로 모니터링할 수 있습니다."
)

# Initialize Session States
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Display friendly history

# Model and client checking
embedder = load_embedding_model()
qdrant_client = get_qdrant_client(qdrant_host, qdrant_port)

# Qdrant status check banner
if qdrant_client:
    try:
        collections = qdrant_client.get_collections().collections
        names = [c.name for c in collections]
        if collection_name in names:
            st.success(f"🟢 Qdrant 연결 성공! 인덱스 컬렉션: '{collection_name}' 정상 작동 중")
        else:
            st.warning(f"🟡 Qdrant 연결 성공하나 '{collection_name}' 컬렉션이 없습니다. ingest_qdrant.py를 먼저 가상환경에서 실행해 주세요.")
    except Exception:
        st.error("🔴 Qdrant 서버가 켜져 있지 않습니다. Docker를 켜거나 포트 6333 연결을 확인해 주세요.")
        qdrant_client = None
else:
    st.error("🔴 Qdrant 클라이언트 초기화 실패.")

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there are agent action traces, show them
        if "traces" in message and message["traces"]:
            with st.expander("🛠️ 에이전트의 도구 실행 흔적 (Agent Action Traces)"):
                for trace in message["traces"]:
                    st.markdown(f"""
                    <div class="tool-box">
                        <div class="tool-header">🛠️ Tool Called: {trace['tool_name']}</div>
                        <div class="tool-body">Arguments: {trace['args']}</div>
                        <div style="font-size:0.8rem; margin-top:5px; color:#94a3b8;">Execution Output:</div>
                        <div class="tool-body" style="background-color:#1e293b; max-height: 200px; overflow-y: auto;">
                            {trace['result'][:500]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# User Chat Input
if query := st.chat_input("Runway 2.0 플랫폼 가이드에 대해 질문해 보세요 (예: Triton 경로와 MLServer 경로가 어떻게 달라?)"):
    # Add User input to visual history
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 1. API key verification
    if not minimax_api_key:
        with st.chat_message("assistant"):
            st.error("🔴 에이전트를 구동하기 위해선 사이드바에 MiniMax API Key를 필수적으로 기입해 주셔야 합니다.")
        st.stop()

    # 2. Initialize Anthropic Client pointing to MiniMax
    try:
        client = Anthropic(
            api_key=minimax_api_key,
            base_url=base_url,
            default_headers={"Authorization": f"Bearer {minimax_api_key}"}
        )
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"Anthropic SDK 클라이언트 생성 중 오류 발생: {e}")
        st.stop()

    with st.chat_message("assistant"):
        st.markdown("🛠️ **에이전트가 생각 흐름을 시작합니다...**")
        agent_status_placeholder = st.empty()
        
        # Build prompt & SDK messages history
        messages_sdk = [
            {"role": "user", "content": query}
        ]
        
        system_prompt = (
            "You are an expert AI MLOps Operator specifically designed for the Runway 2.0 platform.\n"
            "Your task is to answer the user's questions utilizing the tools at your disposal.\n"
            "You have tools to search Qdrant vector database ('search_runway_docs') and read raw markdown guide documents ('read_raw_document').\n"
            "Use 'search_runway_docs' to search by semantic query if you need information.\n"
            "Use 'read_raw_document' if you need the full, exact layout/specification of a specific skills file for comprehensive context.\n"
            "If you cannot find the answer in the retrieved sources, kindly say you don't know rather than fabricating facts.\n"
            "Always reply in Korean. Maintain a precise, informative, and professional engineering tone."
        )
        
        traces = []
        loop_count = 0
        max_loops = 5
        final_answer = ""
        
        # 3. Agentic RAG Loop (Tool Calling Loop)
        while loop_count < max_loops:
            loop_count += 1
            agent_status_placeholder.info(f"🤔 에이전트 추론 루프 실행 중... (단계: {loop_count}/{max_loops})")
            
            try:
                # Call Anthropic Claude API
                response = client.messages.create(
                    model=model_name,
                    max_tokens=1500,
                    system=system_prompt,
                    messages=messages_sdk,
                    tools=tools_definition
                )
            except Exception as e:
                st.error(f"API 호출 실패: {e}")
                final_answer = "MiniMax API 호출에 실패하였습니다. 사이드바의 API 키나 베이스 URL 설정을 확인해 주십시오."
                break
                
            # Parse response
            stop_reason = response.stop_reason
            response_content = response.content
            
            # Find assistant text block and tool use block
            text_blocks = [block.text for block in response_content if block.type == "text"]
            assistant_text = "\n".join(text_blocks)
            
            tool_use_blocks = [block for block in response_content if block.type == "tool_use"]
            
            # If there's some reasoning or explanation, print it
            if assistant_text:
                st.markdown(f"> **에이전트의 중간 추론**: {assistant_text}")
                
            # If no tool is requested, the Agent completed its task!
            if stop_reason != "tool_use" or not tool_use_blocks:
                final_answer = assistant_text
                break
                
            # Prepare to execute tools
            tool_results = []
            
            # We must append the assistant's request (containing tool_use blocks) to SDK history
            # Converting to standard Anthropic messages block format
            assistant_msg_content = []
            for block in response_content:
                if block.type == "text":
                    assistant_msg_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_msg_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    
            messages_sdk.append({"role": "assistant", "content": assistant_msg_content})
            
            # Process each tool call
            tool_response_content = []
            for tool_use in tool_use_blocks:
                tool_name = tool_use.name
                tool_id = tool_use.id
                tool_input = tool_use.input
                
                trace_item = {
                    "tool_name": tool_name,
                    "args": str(tool_input),
                    "result": ""
                }
                
                with st.status(f"⚙️ 에이전트가 도구 실행 중: `{tool_name}`", expanded=True) as status:
                    # TOOL 1: Qdrant Search
                    if tool_name == "search_runway_docs":
                        search_query = tool_input.get("query", "")
                        st.write(f"🔍 벡터 DB 쿼리 검색: **'{search_query}'**")
                        
                        if not qdrant_client:
                            output_str = "Error: Qdrant Client is not initialized or running."
                        else:
                            try:
                                query_vector = embedder.encode(search_query).tolist()
                                search_results = qdrant_client.search(
                                    collection_name=collection_name,
                                    query_vector=query_vector,
                                    limit=top_k
                                )
                                chunks = []
                                for res in search_results:
                                    payload = res.payload
                                    text_content = payload.get("page_content", "")
                                    metadata = payload.get("metadata", {})
                                    chunks.append(f"Source: {metadata.get('source', 'Unknown')}\n{text_content}")
                                    
                                if chunks:
                                    output_str = "\n\n---\n\n".join(chunks)
                                    st.write(f"✅ 관련 기술 문서 {len(chunks)}개 조각 로드 완료.")
                                else:
                                    output_str = "Qdrant에서 일치하는 문서 조각을 찾을 수 없습니다."
                            except Exception as ex:
                                output_str = f"Qdrant 검색 에러: {ex}"
                                st.write("❌ Qdrant 검색 실패.")
                                
                    # TOOL 2: Read raw skill files
                    elif tool_name == "read_raw_document":
                        file_path = tool_input.get("file_path", "")
                        st.write(f"📖 가이드 전문 정독: **'skills/{file_path}'**")
                        
                        local_path = os.path.join("skills", file_path)
                        if not os.path.exists(local_path):
                            output_str = f"Error: File 'skills/{file_path}' does not exist."
                            st.write(f"❌ 파일을 찾을 수 없습니다: skills/{file_path}")
                        else:
                            try:
                                with open(local_path, "r", encoding="utf-8") as f:
                                    output_str = f.read()
                                st.write(f"✅ {len(output_str)}자 분량의 가이드 원본 파일 정독 완료.")
                            except Exception as ex:
                                output_str = f"Error reading file: {ex}"
                                st.write("❌ 파일 읽기 실패.")
                    else:
                        output_str = f"Error: Unknown tool '{tool_name}'."
                        st.write("❌ 알 수 없는 도구.")
                        
                    trace_item["result"] = output_str
                    traces.append(trace_item)
                    status.update(label=f"✅ 도구 완료: {tool_name}", state="complete")
                
                # Append tool result in Anthropic SDK format
                tool_response_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": output_str
                })
                
            # Append the tool execution results to messages history
            messages_sdk.append({"role": "user", "content": tool_response_content})
            
        # Clear status banner
        agent_status_placeholder.empty()
        
        # 4. Render Final Answer
        if final_answer:
            st.markdown("### 🤖 최종 에이전트 답변")
            st.markdown(final_answer)
            
            # Show Expandable traces
            if traces:
                with st.expander("🛠️ 에이전트의 도구 실행 흔적 (Agent Action Traces)"):
                    for trace in traces:
                        st.markdown(f"""
                        <div class="tool-box">
                            <div class="tool-header">🛠️ Tool Called: {trace['tool_name']}</div>
                            <div class="tool-body">Arguments: {trace['args']}</div>
                            <div style="font-size:0.8rem; margin-top:5px; color:#94a3b8;">Execution Output:</div>
                            <div class="tool-body" style="background-color:#1e293b; max-height: 200px; overflow-y: auto;">
                                {trace['result'][:500]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            # Save message to session history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": final_answer,
                "traces": traces
            })
        else:
            st.warning("에이전트가 답변을 생성하지 못했습니다. 추론 루프 한도에 걸렸거나 API 상태를 점검해 주십시오.")

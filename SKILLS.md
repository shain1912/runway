# SKILLS.md — Agentic RAG 레퍼런스 패턴 모음

이 문서는 본 레포(`E:\runway`)에서 구현한 **에이전틱 RAG 기법들을 다른 시스템 개발에 재사용**하기 위한 레퍼런스입니다.
"무엇을 복사할 것인가 / 무엇을 베끼면 안 되는가 / 프로덕션에서 무엇을 더할 것인가"를 기준으로 정리했습니다.

> 코드 위치 표기: `파일명#함수/심볼`. 핵심 로직은 거의 전부 `rag_core.py`에 모여 있습니다(UI/프로바이더 무관).

---

## 0. 아키텍처 한눈에 보기

```
docs(웹) ──scrape──> docs_markdown/ ──ingest──> Qdrant(하이브리드 색인)
                                                      │
                                  ┌───────────────────┴────────────────────┐
                                  │            rag_core.py (코어)            │
                                  │  retrieve(하이브리드+RRF+rerank)         │
                                  │  self-RAG 게이트 / 보안 파일읽기         │
                                  │  run_agent(툴유즈 루프 = 이벤트 제너레이터)│
                                  └───────────────────┬────────────────────┘
                       ┌───────────────────┬──────────┴──────────┐
                  rag_app.py(Streamlit)  evaluate_rag.py(평가)  answer()(헤드리스/CLI/API)
```

핵심 설계 원칙: **코어(로직)와 프론트엔드(렌더링)를 분리**한다. `rag_core`에는 Streamlit도, API 키 처리도 없다 → CLI·API·배치·테스트에서 그대로 재사용 가능.

---

## 1. 복사해서 쓸 패턴 (Reusable patterns)

### 1.1 툴유즈 에이전트 루프를 "이벤트 제너레이터"로
- **위치**: `rag_core.py#run_agent`
- **무엇**: `stream → stop_reason=="tool_use"면 tool_result 붙여 재호출 → 아니면 종료`. 이를 함수가 직접 렌더링하지 않고 `{"type": ...}` 이벤트를 **yield**한다.
- **왜 좋은가**: 같은 루프 하나를 (a) Streamlit이 스트리밍 렌더, (b) `answer()`가 헤드리스로 소비 → **로직 중복 0**. UI를 FastAPI/CLI로 바꿔도 코어 불변.
- **이식법**: 이벤트 프로토콜(`loop_start/text_delta/tool_start/tool_result/final/error/max_loops`)만 맞추면 어떤 프론트든 붙는다.
- **gotcha**: 스트리밍은 `client.messages.stream()`의 `text_stream` 소비 후 `get_final_message()`로 전체 메시지(툴콜 포함)를 받아야 한다.

### 1.2 프로바이더 추상화 (Anthropic SDK → 임의 호환 엔드포인트)
- **위치**: `rag_app.py`의 `Anthropic(base_url=..., default_headers={...})`, `rag_core.py#answer`
- **무엇**: Anthropic SDK를 MiniMax 호환 엔드포인트에 꽂아 사용. `base_url`/`model`/헤더만 교체.
- **이식법**: 멀티 LLM 백엔드를 둘 때, 메시지/툴 포맷이 Anthropic 호환이면 클라이언트 생성부만 분기.
- **gotcha**: 호환 엔드포인트가 **streaming**·**prompt caching**·일부 필드를 지원 안 할 수 있음 → 폴백 경로 필수(본 코어는 `stream=False` 경로를 별도 제공).

### 1.3 하이브리드 검색(dense + BM25 sparse) + RRF 융합
- **위치**: `rag_core.py#retrieve`, 색인은 `ingest_qdrant.py#build_points`
- **무엇**: Qdrant **named vectors**(`dense` + `bm25` sparse)로 색인하고, 질의 시 `query_points(prefetch=[dense, sparse], query=FusionQuery(RRF))`로 융합.
  - sparse는 FastEmbed `Qdrant/bm25`, 컬렉션 sparse 설정에 `Modifier.IDF`를 주면 BM25식 IDF 가중.
- **왜 좋은가**: dense는 의미, sparse(BM25)는 **정확매칭**(values.yaml 키, CLI 플래그, 에러코드)에 강함 → 둘을 RRF로 합쳐 recall↑.
- **이식법**: 컬렉션 생성 시 `vectors_config={"dense":...}`, `sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)}`. 포인트는 `vector={"dense":[...], "bm25": SparseVector(indices,values)}`.
- **gotcha**:
  - **Qdrant 서버 ≥ 1.10** (Query API). 구버전이면 본 코어는 dense-only로 graceful fallback.
  - **RRF 융합 점수는 코사인이 아니다** → 신뢰도 임계값 판단에 쓰면 안 됨(아래 1.5 참고).
  - fastembed 미설치 시 코어가 자동으로 dense-only로 동작(에러 안 남).

### 1.4 토큰-정합 청킹 (임베딩 truncation 방지) — ★중요
- **위치**: `rag_core.py#split_to_token_windows`, `#chunk_markdown`
- **무엇**: 헤딩(`#~####`)으로 1차 분할 후, **임베더의 실제 토큰 한계**에 맞춰 토큰 윈도우로 2차 분할(오버랩 포함). 청크 크기를 **글자 수가 아니라 토큰 수**로 잰다.
- **왜 중요**: 본 레포의 `jhgan/ko-sbert-multitask`는 **max_seq_length=128 토큰**(검증됨). 글자 기준(예: 1200자) 윈도우는 임베딩 시점에 **조용히 잘려** recall이 무너진다. 토큰 기준으로 자르면 잘림이 사라진다(검증: 21청크 중 over_limit=0).
- **이식법**: `max_tokens = embedder.max_seq_length - PREFIX_TOKEN_BUDGET`. 프리픽스(`Source/Context` breadcrumb)도 토큰을 먹으므로 예산에서 빼라.
- **gotcha**: 토큰ID 윈도우를 decode하면 subword 경계에서 약간의 텍스트 손실 가능(임베딩엔 영향 미미). 더 깔끔히 하려면 문장/문단 경계 우선 분할 후 초과분만 토큰 윈도우.

### 1.5 코드-레벨 Self-RAG 게이트 (프롬프트 권고가 아니라 신호 주입)
- **위치**: `rag_core.py#retrieve`(신뢰도 계산) + `#format_retrieval_for_model`(경고 주입)
- **무엇**: top-1 **dense 코사인**을 별도로 구해 `LOW_CONFIDENCE_THRESHOLD`와 비교 → 미달이면 검색 결과 머리말에 `[경고] ...재검색/abstain` 지시를 **코드가 주입**한다. 모델이 알아서 판단하길 기대하지 않는다.
- **왜 좋은가**: RRF 점수는 비교 불가하므로, 신뢰도는 **코사인으로 따로** 측정해야 의미가 있다. 임계값 미달 시 행동 지시를 강제 주입 → CRAG의 경량 버전.
- **이식법**: 신뢰도 척도(코사인/리랭커 점수)는 corpus별로 `evaluate_rag.py`로 보정. 더 강하게 가려면 "임계 미달 시 코드가 재질의/abstain을 강제"하는 제어 흐름으로 승격.
- **gotcha**: ko-sbert 코사인은 **미보정**이라 0.40은 출발값일 뿐. 반드시 골든셋으로 튜닝.

### 1.6 보안: 화이트리스트 + 경로탈출 차단 파일읽기
- **위치**: `rag_core.py#secure_skill_read`
- **무엇**: `os.path.basename()`로 경로 성분 제거 → 화이트리스트 집합 검사 → `realpath`로 루트 포함 여부 재확인.
- **왜 중요**: LLM이 만든 `file_path`를 그대로 `os.path.join`하면 `../`로 임의 파일 읽기가 된다(원래 코드의 취약점). LLM 입력은 **신뢰 경계 밖**으로 다뤄라.
- **이식법**: "모델이 만든 문자열로 파일/SQL/명령을 구성"하는 모든 곳에 동일 원칙. 검증됨: traversal/non-whitelist 차단, basename 정규화 통과.

### 1.7 렌더링 인젝션 차단
- **위치**: `rag_app.py#render_traces`
- **무엇**: `unsafe_allow_html=True`로 렌더할 때 동적 콘텐츠(도구 결과/문서 텍스트)를 `html.escape()`로 이스케이프.
- **gotcha**: 문서 본문에 HTML/스크립트가 섞여 있을 수 있으므로, 외부/검색 콘텐츠를 HTML에 직접 보간하지 말 것.

### 1.8 증분 인덱싱 (해시 매니페스트 + 결정적 ID + source 단위 삭제)
- **위치**: `ingest_qdrant.py`(`file_hash`/`load_manifest`/`chunk_point_id`/`delete_points_for_source`)
- **무엇**: 파일별 sha256를 `.ingest_manifest.json`에 저장 → 변경된 파일만 재색인. 포인트 ID는 `uuid5(namespace, "source::idx")`로 결정적 → 재색인이 멱등. source별 delete→upsert로 청크 수 변동·파일 삭제까지 정리.
- **이식법**: `--full`로 전체 재구축. 임베딩 모델/청킹 규칙을 바꾸면 `--full` 필수.

### 1.9 검색 평가 하니스 (프로덕션과 동일 경로)
- **위치**: `evaluate_rag.py`
- **무엇**: 골든 Q&A를 **`rag_core.retrieve`로 그대로** 통과시켜 Hit@K/MRR@K 측정 → 평가와 운영의 검색 경로가 일치.
- **이식법**: 청킹/모델/리랭커를 바꿀 때마다 돌려 회귀 확인. `--rerank`, `--k`로 비교.

---

## 2. 베끼면 안 되는 부분 / 남은 한계 (Anti-patterns & limits)

| 항목 | 현재 상태 | 다른 시스템에선 |
|---|---|---|
| 멀티턴 메모리 | 최근 N개 **텍스트만** 재생(중간 근거 미보존), 토큰 예산 없음 | 토큰 예산 기반 컨텍스트 관리 + 필요시 요약 |
| Self-RAG | 신호 주입까지(권고 강제). 행동은 모델 재량 | 임계 미달 시 **코드가** 재질의/abstain 강제 |
| 출처 | 모델이 작성(미검증) | 답변↔근거 정합성(NLI/인용) **사후 검증** |
| 평가 | 검색만, 경로-substring, 10문항 | 답변레벨(RAGAS: faithfulness/answer-relevance) + CI 회귀 게이트 |
| 견고성 | 헤드리스 경로만 재시도. 스트리밍은 1회 시도 | 스트리밍 포함 백오프/타임아웃/회로차단/루프·비용 예산 |
| 프롬프트 캐싱 | 미적용(MiniMax 호환성 불확실) | Anthropic 정식 사용 시 system+tools `cache_control`로 비용/지연 절감 |
| 관측성 | UI trace 표시뿐 | 구조화 트레이싱(tokens/latency/cost), 로그 집계 |
| 모델 | ko-sbert(128토큰, 768d) | 토큰 예산 큰 모델(bge-m3 등) 검토; chunk는 토크나이저 기준 |
| 배포 형태 | Streamlit 단일 프로세스·동기·단일 사용자 | 코어를 서비스(API)로, UI는 클라이언트로 분리 |

---

## 3. 프로덕션 로드맵 (우선순위)

1. **임계 미달 시 코드 강제 게이트** — 재질의/abstain을 제어 흐름으로 승격(현재는 신호 주입까지).
2. **답변 충실도 검증** — 생성 후 주장↔근거 검증(인용 검증/NLI), 실패 시 재생성 or abstain.
3. **컨텍스트/상태 관리** — 토큰 예산 + 요약, 긴 대화 안정화.
4. **견고성** — 스트리밍 포함 재시도/타임아웃, 턴당 루프·비용 상한, 동일쿼리 진동 감지.
5. **평가 성숙화** — 골든셋 확대 + 답변레벨 지표 + CI 게이트.
6. **관측성** — OpenTelemetry류 트레이싱(도구별 latency/tokens/cost).
7. **프롬프트 캐싱** — 정식 Anthropic 사용 시 system+tools 캐시.

---

## 4. 재현 메모 (이 레포에서 검증된 사실)

- `jhgan/ko-sbert-multitask` **max_seq_length = 128 토큰** (그래서 토큰-정합 청킹이 필수). 토큰 청킹 적용 후 over_limit=0 확인.
- 설치 환경: `qdrant-client 1.18`(Query API/Fusion/IDF 모두 지원), `sentence-transformers 5.5`, `anthropic 0.104`, `streamlit 1.57`. **`fastembed`는 별도 설치 필요**(미설치 시 dense-only로 자동 폴백).
- **하이브리드 사용 조건**: `pip install -r requirements.txt`(fastembed) + Qdrant 서버 ≥ 1.10 + `python ingest_qdrant.py --full`로 named-vector 컬렉션 재생성(기존 정수 ID/단일벡터 컬렉션과 호환 안 됨).
- 보안 가드 동작 확인: 경로탈출/비화이트리스트 차단, basename 정규화 통과.

---

## 5. 빠른 사용

```bat
pip install -r requirements.txt
qdrant\qdrant.exe                  :: Qdrant >= 1.10
python ingest_qdrant.py --full     :: 하이브리드(named vector) 색인 최초 1회
python evaluate_rag.py --rerank    :: 검색 품질 측정
streamlit run rag_app.py           :: UI
```

헤드리스(코어 단독) 사용 예:
```python
import rag_core as core
from qdrant_client import QdrantClient
ans = core.answer(
    "GPU 할당 방법 알려줘",
    api_key="<minimax_jwt>", base_url="https://api.minimax.io/anthropic",
    model="MiniMax-M2.7", qdrant_client=QdrantClient(host="localhost", port=6333),
    use_reranker=True,
)
print(ans)
```

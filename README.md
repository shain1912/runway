# 🤖 Runway Agentic RAG Chatbot

본 프로젝트는 Runway 2.0 플랫폼 가이드 문서를 바탕으로 구축된 **에이전틱 RAG (Agentic RAG) 연습 및 학습용 챗봇 시스템**입니다.  
사용자가 직접 로컬 환경이나 가상환경 환경에서 **Minimax API**와 **Anthropic Python SDK**의 Tool Use(도구 사용) 기능을 연계하여 고도화된 RAG 파이프라인의 실시간 추론 연쇄 과정을 직접 제어하고 눈으로 모니터링할 수 있도록 설계되었습니다.

---

## ✨ 주요 특징 (Key Features)

*   **에이전틱 추론 루프 (Agentic Reasoning Loop)**: 단순히 입력 질문에 맞춰 매번 전체 문서를 기입하여 넘기는 일반 RAG와 달리, LLM 에이전트(Claude)가 질문을 분석하여 필요할 때만 벡터 DB 검색(`search_runway_docs`) 및 가이드 전문 정독(`read_raw_document`) 도구를 스스로 선택해 조합하여 답변합니다.
*   **생각 흐름 시각화**: 에이전트가 질문을 어떻게 쪼개어 도구를 호출하고 어떤 아규먼트(인수)를 보냈는지, 그 실행 결과는 무엇인지를 Streamlit UI 상에서 **에이전트 도구 실행 흔적(Agent Action Traces)**으로 실시간 제공합니다.
*   **다중 .env API 키 지원**: 로컬에 배치된 `.env` 파일 내의 `MINIMAX1`, `MINIMAX2`, `MINIMAX3`, `MINIMAX4` 등의 여러 키값들을 웹 실행 시 자동으로 파싱하여, 사이드바에서 마우스 클릭 한 번으로 선택하여 토큰 검증 테스팅을 진행할 수 있습니다.
*   **100% 로컬 무료 임베딩 연동**: 인증 요구(401 Unauthorized)가 없는 고품질 퍼블릭 한국어 문장 임베딩 모델 `jhgan/ko-sbert-multitask`을 내장하여, 로그인이나 토큰 등록 없이 완전 격리된 오프라인 환경에서도 완벽한 벡터 주입이 수행됩니다.
*   **원클릭 Qdrant 무설치 구성**: 윈도우 환경에서 Docker 없이도 작동하도록, **공식 Qdrant Windows Standalone 바이너리**를 원클릭으로 자동 다운로드 및 백그라운드 구동해 주는 도우미 런처 기능을 탑재하였습니다.
*   **가상환경 자동 격리**: 개발자 PC에 지저분하게 글로벌 패키지를 설치하지 않고, 원클릭 시 독립 가상환경(`.venv`)을 구성하여 정해진 필수 패키지만 격리 설치하고 청정하게 구동합니다.

---

## 📂 프로젝트 구조 (Project Structure)

```text
e:\runway\
├── docs_markdown/       # 크롤링 완료된 53개의 원본 마크다운 문서 보관소
├── skills/              # 에이전트 정독용 5대 종합 한글 스킬 요약 파일
├── qdrant/              # (자동 생성) 다운로드 및 압축 해제된 Qdrant 실행기 영역
├── .venv/               # (자동 생성) 독립 가상환경 실행 라이브러리 폴더
├── ingest_qdrant.py     # 마크다운 문서 파싱, ko-SBERT 임베딩 및 Qdrant 주입 스크립트
├── rag_app.py           # Streamlit 기반 Agentic RAG 챗봇 메인 어플리케이션
├── run_chatbot.bat      # 가상환경 셋업, 의존성 설치, Qdrant/RAG 원클릭 런처 스크립트
├── requirements.txt     # 최소 코어 의존성 패키지 정의서
├── .env                 # (사용자 작성) Minimax 다중 API 키 보관 파일
└── README.md            # 본 소개 및 가이드 문서
```

---

## 🚀 빠른 시작 가이드 (Quick Start Guide)

### 1단계. API Key 구성 (`.env` 파일 생성)
프로젝트 최상위 디렉터리(`e:\runway\`)에 `.env` 파일을 생성하고 아래와 같이 소지하고 계신 Minimax 키 토큰값을 기입합니다:

```env
MINIMAX1=your_jwt_token_key_1
MINIMAX2=your_jwt_token_key_2
```

### 2단계. 원클릭 런처 실행
[run_chatbot.bat](file:///e:/runway/run_chatbot.bat) 파일을 더블 클릭하여 기동합니다. 최초 실행 시 isolated 파이썬 가상환경 구성 및 패키지 다운로드가 신속히 완료됩니다.

### 3단계. Qdrant 로컬 DB 켜기 (무설치 자동화)
런처 메뉴 화면에서 **`[4] Setup and Start Qdrant Server (Windows Standalone)`**를 선택합니다.  
자동으로 GitHub에서 공식 zip을 다운로드 및 압축 해제하여 백그라운드 명령 프롬프트 창으로 Qdrant 서비스를 구동(6333 포트)해 줍니다. (5초 후 자동으로 메뉴 복귀)

### 4단계. 가이드 문서 지식 데이터 적재 (Ingest)
메뉴 화면에서 **`[1] Ingest Documents (Run ingest_qdrant.py)`**를 선택합니다.  
53개 문서의 의미론적 청킹(Semantic Heading Chunking) 및 로컬 `ko-sbert` 임베딩 변환을 완료하여 Qdrant DB에 안전하게 인덱스 적재를 마칩니다.

### 5단계. 챗봇 가동 및 대화 시작!
메뉴 화면에서 **`[2] Start Streamlit Agentic Chatbot (Run rag_app.py)`**를 선택합니다.  
자동으로 로컬 호스트 웹앱이 켜집니다. 인터넷 브라우저로 **`http://localhost:8501`** 에 접속합니다.
1. 왼쪽 사이드바에서 `.env`에 정의된 **`MINIMAX1` ~ `MINIMAX4`** 중 테스트할 계정을 고릅니다.
2. 메인 채팅창에 가이드에 대해 질문을 던져 에이전트의 생각을 실시간 트래킹해 보십시오!

---

## 🛠️ 에이전트가 활용하는 도구 명세

*   **`search_runway_docs(query)`**: 사용자의 질문 핵심 키워드를 `ko-sbert` 벡터 변환하여 Qdrant에서 관련 마크다운 문서 조각들을 탐색하여 가져오는 도구.
*   **`read_raw_document(file_path)`**: 더 완벽하고 일관된 설정 파일(values.yaml) 전문 예시나 admin 세부 명령어를 학습해야 할 때, 에이전트가 5대 한글 스킬 파일의 전문을 끝까지 읽어내리는 정독용 로컬 도구.

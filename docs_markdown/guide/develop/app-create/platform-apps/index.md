# 플랫폼 앱

플랫폼 앱은 AI·ML 워크플로우 전반을 지원하기 위해 **Runway에 미리 설치된 서비스**입니다.
코드 관리, 실험 추적, 워크플로우 오케스트레이션, 배포, LLM 활용까지 — 별도의 설치나 설정 없이 바로 사용할 수 있습니다.

> 워크스페이스 > **플랫폼 앱** 메뉴

플랫폼 앱은 역할에 따라 다음 네 그룹으로 구성됩니다.

| 그룹 | 앱 | 역할 |
|------|-----|------|
|  **코드 관리 · ML 실험** | Gitea, MLflow | 코드 저장소 운영 및 실험 결과 추적 |
|  **워크플로우 · 배포 자동화** | Airflow, Argo CD | 파이프라인 스케줄링 및 선언적 배포 |
|  **AI · 협업** | LLM Playground, Chat, Langfuse | LLM API 관리, AI 채팅, LLM 모니터링 |
|  **보안 · 시크릿 관리** | OpenBao | 시크릿 저장 및 접근 제어 |

---

## 플랫폼 앱 접속

각 앱 카드의 **열기** 버튼을 클릭하면 해당 앱의 웹 인터페이스로 이동합니다.

### SSO 로그인 (Keycloak)

플랫폼 앱은 **Keycloak 기반 SSO(Single Sign-On)**로 통합 인증됩니다.

- Runway에 로그인한 상태에서 앱을 열면, 별도 로그인 없이 자동으로 인증됩니다.
- 세션이 만료된 경우 로그인 화면이 표시되며 **Keycloak 로그인**을 선택하여 접속할 수 있습니다.
- 모든 플랫폼 앱에서 동일한 계정과 인증 세션을 공유합니다.

---

## 코드 관리 · ML 실험 앱

### Gitea

Gitea는 경량 Git 서버로, Runway 내에서 소스 코드를 버전 관리하고 협업할 수 있는 환경을 제공합니다.

- 저장소(Repository) 생성 및 브랜치 관리
- Pull Request 기반 코드 리뷰
- 이슈 트래킹 및 프로젝트 보드
- Airflow DAG 파일, 모델 학습 스크립트 등 ML 프로젝트 코드를 중앙에서 관리

**Runway 연동**

Runway에서 프로젝트를 생성하거나 참여하면 Gitea organization이 자동으로 생성되고, 해당 프로젝트의 `airflow-dags` 저장소가 함께 추가됩니다.

[Gitea 공식 문서](https://docs.gitea.com/)

---

### MLflow

MLflow는 머신러닝 실험을 기록·비교하고, 학습된 모델을 체계적으로 관리하는 플랫폼입니다.

- 실험(Experiment) 단위 하이퍼파라미터, 메트릭, 아티팩트 기록
- 실험 간 성능 비교 및 시각화
- 모델 레지스트리를 통한 모델 버전 관리 및 스테이지(Staging → Production) 전환
- Airflow 파이프라인과 연동한 자동 실험 추적

[MLflow 공식 문서](https://mlflow.org/docs/latest/index.html)

---

## 워크플로우 · 배포 자동화 앱

### Airflow

Apache Airflow는 DAG(Directed Acyclic Graph) 기반으로 데이터 파이프라인과 ML 워크플로우를 스케줄링하고 모니터링합니다.

- DAG 단위의 워크플로우 정의 및 시각화
- 크론(Cron) 기반 스케줄링 및 수동 트리거
- 태스크 실행 상태 모니터링 및 로그 확인
- 데이터 전처리 → 모델 학습 → 평가 → 배포로 이어지는 ML 파이프라인 자동화

**Runway 연동**

멤버쉽이 있는 프로젝트의 DAG만 표시됩니다. Gitea의 `airflow-dags` 저장소와 gitsync로 주기적으로 동기화하여 DAG 파일을 자동 반영합니다.

[Apache Airflow 공식 문서](https://airflow.apache.org/docs/)

---

### Argo CD

Argo CD는 Git 저장소의 선언적 설정을 기준으로 애플리케이션 배포 상태를 자동으로 동기화합니다.

- Gitea 저장소와 연동하여 GitOps 워크플로우 구성
- 배포 상태 시각화 및 동기화(Sync) 관리
- 롤백 및 배포 이력 추적
- 모델 서빙 서비스, API 서버 등의 선언적 배포 관리

**Runway 연동**

멤버쉽이 있는 프로젝트의 애플리케이션과 저장소만 Argo CD 화면에 표시됩니다.

[Argo CD 공식 문서](https://argo-cd.readthedocs.io/)

---

## AI · 협업 앱

### LLM Playground

LLM Playground는 LiteLLM 기반의 **LLM API 게이트웨이**로, Runway에 등록된 다양한 언어 모델을 OpenAI 호환 API를 통해 통합 관리합니다. Chat을 비롯한 플랫폼 내 서비스가 LLM을 호출할 때 이 게이트웨이를 경유합니다.

- OpenAI 호환 API로 다양한 LLM 프로바이더 통합 (chat/completions, embeddings 등)
- 모델 등록·관리 및 API 키 발급
- 벡터 스토어 관리 및 프롬프트 테스트
- 사용량 추적 및 예산 관리

---

### Chat

Chat은 LibreChat 기반의 **대화형 AI 인터페이스**로, LLM Playground에 등록된 모델을 활용한 AI 채팅과 팀 협업을 함께 지원합니다.

- LLM Playground에 등록된 모델을 선택하여 AI 대화 수행
- 에이전트 제작기를 통한 커스텀 AI 어시스턴트 구성
- 벡터 DB 연동을 통한 RAG 기반 대화
- 팀 멤버 간 대화 이력 관리 및 협업

---

### Langfuse

Langfuse는 LLM 애플리케이션의 성능을 추적·평가·개선하기 위한 **LLM 모니터링 및 옵저버빌리티 플랫폼**입니다.

- LLM 호출 추적(Tracing) 및 로그 시각화
- 프롬프트 버전 관리 및 성능 비교
- Human-in-the-Loop 기반 응답 평가 — 잘못된 응답에 사용자 피드백 제출 가능
- 데이터셋 관리 및 LLM 평가 실험

**Runway 연동**

Langfuse Organization이 Runway 프로젝트와 자동으로 매핑됩니다. LLM Playground(LiteLLM) 및 Chat(LibreChat)과 연동하여 플랫폼 내 LLM 호출 전반을 모니터링할 수 있습니다.

[Langfuse 공식 문서](https://langfuse.com/docs)

---

## 보안 · 시크릿 관리 앱

### OpenBao

OpenBao는 API 키, 토큰, 인증서 등 민감한 정보를 안전하게 저장·관리하는 **오픈소스 시크릿 관리 플랫폼**입니다.

- Secrets Engine을 통한 시크릿 저장 및 동적 생성
- 정책(Policy) 기반 접근 제어
- 토큰·AppRole 등 다양한 인증 방식 지원
- ML 파이프라인에서 외부 서비스 인증 정보를 안전하게 참조

**Runway 연동**

Runway 프로젝트(= 네임스페이스) 단위로 시크릿을 분리하여 관리합니다.  
OpenBao는 아래 세 가지 역할로 접근 범위를 제어하며, Runway 프로젝트에서 부여된 **역할에 따라 자동으로 OpenBao 권한이 부여**됩니다.

OpenBao는 아래 세 가지 역할로 접근 범위를 제어합니다.

- **OpenBao Admin** — 모든 권한
- **OpenBao Member** — **삭제를 제외**한 모든 권한
- **OpenBao Viewer** — 조회만 가능

> **Note**: OpenBao 로그인 방법
>
> 1. 프로젝트의 **설정 > 일반** 메뉴에서 **프로젝트 ID**를 복사합니다.
>
>     {width="50%"}
>
> 2. **Namespace** 란에 확인한 프로젝트 ID를 입력합니다.
> 3. **Method** 항목에서 **OIDC**를 선택합니다.
> 4. **Sign in with OIDC Provider** 버튼을 클릭하여 로그인합니다.
>
> 

[OpenBao 공식 문서](https://openbao.org/docs/)
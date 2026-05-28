# 카탈로그에서 앱 배포

앱 카탈로그는 사용 빈도가 높은 애플리케이션의 **Helm 차트 구성(values.yaml)을 간편화하여 제공**하는 배포 방식입니다.
Helm 차트에 대한 상세 지식 없이도 필요한 설정만 조정하여 빠르게 애플리케이션을 배포할 수 있습니다.

## 제공 카탈로그 앱

앱 카탈로그는 다음과 같이 구성되어 있으며, 지속적으로 업데이트될 수 있습니다.

| 그룹 | 앱 | 설명 |
|------|-----|------|
| **IDE · 코딩 도구** | Code Server | 브라우저 기반 VS Code 개발 환경 |
| | JupyterLab | 대화형 Python 노트북 개발 환경 |
| **벡터 데이터베이스** | Chroma DB | AI 애플리케이션을 위한 오픈소스 임베딩 벡터 데이터베이스 |
| | Milvus | 대규모 유사도 검색을 위한 클라우드 네이티브 벡터 데이터베이스 |
| | Qdrant | 대규모 유사도 검색과 AI 애플리케이션을 위한 벡터 데이터베이스 |
| **AI 애플리케이션** | Langflow | 드래그 앤 드롭으로 멀티 에이전트·RAG 앱을 구성하는 비주얼 프레임워크 |

---

## 배포 절차

모든 카탈로그 앱의 배포 절차는 동일합니다. 각 앱별 values.yaml 설정 내용은  **[values.yaml 설정 가이드](#values-yaml-guide)**를 참고하세요.

> 프로젝트 > **카탈로그** 메뉴

1. 프로젝트 화면에서 **카탈로그** 메뉴로 이동합니다.

    

2. 애플리케이션 카드를 확인하여 원하는 애플리케이션을 선택합니다.

3. 화면 오른쪽 상단의 **애플리케이션 생성** 버튼을 클릭합니다.

    

4. **기본 정보**를 입력합니다.

    

    - **이름**: 목록에 표시될 이름 (예시)`code-server-003`
    - **ID**: 시스템 고유 식별자(3-53자, 영문 소문자, 숫자, 하이픈(-)만 사용 가능) (예시)`csef0227`
    - **설명**: 용도 메모 (선택)

    - **구성** 영역은 카탈로그가 자동으로 설정합니다. 헬름 리포지토리, 차트, 버전을 별도로 수정할 필요가 없습니다.

5. code-server 접속 링크를 생성하기 위해 **리소스 현황** 버튼을 클릭합니다.

    

6. 리소스 현황 최상단에 위치한 **베이스 도메인**을 확인하고, 복사하기 버튼을 클릭합니다.

7. **애플리케이션 열기 링크** 영역의 **링크 추가** 버튼을 클릭하고, 버튼명이 될 **이름**을 입력합니다.

8. 연결될 **URL**을 입력합니다.

    > **Info**: URL의 구성
    >
    > URL은 사용자 지정 이름(서브 도메인)과 Runway 베이스 도메인으로 구성됩니다.
    >
    > ```
        {user-defined_sub-domain}.{runway-base-domain}
        
        (예시 화면) csef0227.v2.mrxrunway.ai
        ```
    > 
    >  - **`서브 도메인`**(사용자 지정 이름): 임의 지정 가능하지만, 가급적 기본정보에 입력한 ID 값을 권장합니다.
    >  - **`베이스 도메인`**: 리소스 현황에 표시되는 베이스 도메인 주소(6번 단계에서 복사한 값)를 붙여넣기 합니다.

9. **헬름 차트** 영역에서 사전 구성된 설정을 확인하고, 필요에 따라 수정합니다.

    

    - **외부 접속을 위해서는 httpRoute 설정이 필수입니다.**  
    아래와 같이 `enabled`를 `true`로 변경하고 hostname을 지정하세요.

        ```yaml title="수정 전 (기본값)"
        httpRoute:
          enabled: false
          hostname: ""    
        ```

        ```yaml title="수정 후" hl_lines="2 3"
        httpRoute:
          enabled: true
          hostname: "{user-defined_sub-domain}.{runway-base-domain}" # 8번 항목 URL 값
        ```

    - 앱 카탈로그에서 제공하는 values.yaml은 자주 조정하는 항목 위주로 간편화되어 있습니다.  
    이외 자세한 설정 방법은 아래 카드를 참고하세요.

    

    -    **설정 항목 개요**

        ---

        values.yaml 각 영역의 역할과 수정해야 할 항목을 확인합니다.

         [영역별 설명 보기](#section-overview)

    -    **카탈로그별 values.yaml**

        ---

        카탈로그별 전체 values.yaml의 상세 내용을 확인합니다.

         [values.yaml 보기](#full-values)

    -    **필수 설정: 외부 접속 경로**

        ---

        외부에서 앱에 접속하기 위한 httpRoute 설정입니다.

         [httpRoute 설정하기](#httproute)

    -    **선택 설정**

        ---

        GPU, 볼륨, 레플리카, CPU·메모리 등 상황에 따른 추가 설정 방법입니다.

         [선택 설정 보기](#optional-settings)

    

10. 화면 하단의 **생성** 버튼을 클릭합니다.

> **Note**: 배포 후 운영
>
> 생성된 애플리케이션은 **애플리케이션** 메뉴에서 확인할 수 있습니다.  
> 실행, 중지, 수정, 삭제 등 배포 후 운영 방법은  **[애플리케이션 관리](../app-manage/)**를 참고하세요.

---

## values.yaml 설정 가이드

앱 카탈로그에서 애플리케이션을 선택하면 해당 앱에 맞는 values.yaml이 제공됩니다.
아래 탭에서 각 카탈로그 앱의 values.yaml 전문을 확인할 수 있습니다. 모든 앱이 유사한 구조를 따르므로, 하나의 설정 방법을 익히면 나머지 앱에도 동일하게 적용할 수 있습니다.

### values.yaml의 주요 설정 항목

| 설정 항목 | 역할 | 수정 여부 |
|------|------|----------|
| `replicaCount` | 애플리케이션 인스턴스(Pod) 수 | 기본값 유지 — 고가용성 필요 시 증가 |
| `podAnnotations` | GPU 스케줄링 설정 | GPU 사용 시에만 주석 해제 |
| `image` | 컨테이너 이미지 (리포지토리, 태그, 풀 정책) | **수정 불필요** — 카탈로그가 자동 설정 |
| `service` | 클러스터 내부 네트워크 (타입, 포트) | **수정 불필요** — 카탈로그가 자동 설정 |
| `podSecurityContext` | 파일 시스템 권한 (fsGroup 등) | 일반적으로 기본값 유지 |
| `securityContext` | 컨테이너 실행 사용자 권한 | 일반적으로 기본값 유지 (주석 처리됨) |
| `resources` | CPU, 메모리, GPU 리소스 할당 | 프로젝트 리소스 현황에 맞게 조정 |
| `persistence` | 데이터 저장소(볼륨) 연결 | 기존 볼륨 연결 시 수정 |
| `env` | 애플리케이션 환경 변수 (일부 앱만 해당) | 일반적으로 기본값 유지 |
| `auth` | 인증 설정 (JupyterLab 등 일부 앱만 해당) | 필요 시 토큰 설정 |
| **`httpRoute`** | **외부 접속 경로 설정** | **필수 설정** — 브라우저 접속에 필요 |

---

### 카탈로그별 values.yaml

> **Note**: 주석 번역 안내
>
> 아래 예시의 주석은 이해를 돕기 위해 한글로 번역한 것입니다. 실제 카탈로그에서는 영문 주석이 표시됩니다.

=== "Code Server"

    브라우저 기반 VS Code 개발 환경

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/codeserver
      tag: 4.96.2
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      port: 8443

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 1000  # 마운트된 볼륨의 파일 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000
    #   runAsGroup: 1000
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: 100m              # CPU 0.1코어
        memory: 512Mi          # 메모리 512MB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: 500m              # CPU 0.5코어
        memory: 1Gi            # 메모리 1GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /config       # 컨테이너 내부 마운트 경로
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
    ```

=== "JupyterLab"

    대화형 Python 노트북 개발 환경

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/jupyterlab
      tag: lab-4.0.5
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      port: 8888

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 100   # jovyan 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000        # jovyan 사용자
    #   runAsGroup: 100        # jovyan 그룹
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: "500m"            # CPU 0.5코어
        memory: "512Mi"        # 메모리 512MB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: "1"               # CPU 1코어
        memory: "1Gi"          # 메모리 1GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /home/jovyan  # 컨테이너 내부 마운트 경로 (Jupyter 작업 디렉터리)
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 인증 ──
    auth:
      token: ""  # 접속 토큰. 비워두면 토큰 없이 접속 가능합니다.

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
    ```

=== "Chroma DB"

    AI 애플리케이션을 위한 오픈소스 임베딩 벡터 데이터베이스

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/chroma
      tag: 1.4.1
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      port: 8000

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 1000  # 마운트된 볼륨의 파일 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000
    #   runAsGroup: 1000
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: 200m              # CPU 0.2코어
        memory: 512Mi          # 메모리 512MB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: 1                 # CPU 1코어
        memory: 2Gi            # 메모리 2GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /chroma       # 컨테이너 내부 마운트 경로 (Chroma 데이터 디렉터리)
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 환경 변수 ──
    env:
      CHROMA_SERVER_HTTP_PORT: "8000"      # HTTP 서버 포트
      CHROMA_PERSIST_DIRECTORY: "/chroma"  # 데이터 저장 경로

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
    ```

=== "Milvus"

    대규모 유사도 검색을 위한 클라우드 네이티브 벡터 데이터베이스

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/milvus
      tag: v2.4.0
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      ports:                   # Milvus는 두 개의 포트를 사용합니다.
        - name: grpc
          port: 19530          # gRPC 통신용 (SDK 연결)
        - name: http
          port: 9091           # HTTP API / 웹 UI용

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 1000  # 마운트된 볼륨의 파일 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000
    #   runAsGroup: 1000
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: 500m              # CPU 0.5코어
        memory: 1Gi            # 메모리 1GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: 1                 # CPU 1코어
        memory: 2Gi            # 메모리 2GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /var/lib/milvus    # 컨테이너 내부 마운트 경로 (Milvus 데이터 디렉터리)
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 환경 변수 ──
    env:
      - name: MILVUS_MODE
        value: "standalone"    # 실행 모드 (standalone: 단일 인스턴스)

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
      port: 9091               # HTTP 포트 (Milvus 웹 UI용)
    ```

=== "Qdrant"

    대규모 유사도 검색과 AI 애플리케이션을 위한 벡터 데이터베이스

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/qdrant
      tag: v1.8.4
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      port: 6333

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 1000  # 마운트된 볼륨의 파일 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000
    #   runAsGroup: 1000
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: 500m              # CPU 0.5코어
        memory: 1Gi            # 메모리 1GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: "1"               # CPU 1코어
        memory: 2Gi            # 메모리 2GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /qdrant/storage    # 컨테이너 내부 마운트 경로 (Qdrant 데이터 디렉터리)
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 환경 변수 ──
    env:
      QDRANT__SERVICE__HTTP_PORT: "6333"  # HTTP API 포트
      QDRANT__LOG_LEVEL: "INFO"           # 로그 레벨

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
    ```

=== "Langflow"

    드래그 앤 드롭으로 멀티 에이전트·RAG 앱을 구성하는 비주얼 프레임워크

    ```yaml
    # ── 인스턴스 설정 ──
    replicaCount: 1  # 고가용성이 필요하면 늘려주세요.

    # ── GPU 스케줄링 ──
    # podAnnotations:  # 사용하려면 이 블록의 주석을 해제하세요.
    #   # 아래 두 가지 방식 중 하나를 선택합니다.
    #   gpu_uuid: "GPU-xxxx.., GPU-yyyy..."          # 특정 GPU를 UUID로 지정
    #   gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti"  # GPU 모델명으로 지정

    # ── 컨테이너 이미지 ──
    image:
      repository: cr.makina.rocks/runway-applications/catalogs/langflow
      tag: 1.7.3
      pullPolicy: IfNotPresent  # 로컬에 이미지가 없을 때만 다운로드

    # ── 네트워크 ──
    service:
      type: ClusterIP  # 클러스터 내부 통신용 (수정 불필요)
      port: 7860

    # ── 보안 컨텍스트 ──
    podSecurityContext:
      fsGroup: 1000  # 마운트된 볼륨의 파일 그룹 ID
      # fsGroupChangePolicy: "OnRootMismatch"  # 권한 변경 최적화가 필요하면 해제

    # securityContext:         # 컨테이너 실행 사용자 설정 (필요 시 해제)
    #   runAsUser: 1000
    #   runAsGroup: 1000
    #   allowPrivilegeEscalation: false
    #   runAsNonRoot: true

    # ── 리소스 할당 ──
    resources:
      requests:                # 최소 보장 리소스
        cpu: 500m              # CPU 0.5코어
        memory: 2Gi            # 메모리 2GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1            # GPU 수량
        # nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
        # 아래 두 옵션 중 하나만 선택하세요.
        # nvidia.com/gpumem: 1024          # GPU 메모리 (MiB)
        # nvidia.com/gpumem-percentage: 50 # GPU 메모리 비율 (%)
      limits:                  # 최대 사용 가능 리소스
        cpu: 2                 # CPU 2코어
        memory: 3Gi            # 메모리 3GB
        # — GPU를 사용하려면 아래 주석을 해제하세요 —
        # nvidia.com/gpu: 1
        # nvidia.com/gpucores: 50
        # nvidia.com/gpumem: 1024
        # nvidia.com/gpumem-percentage: 50

    # ── 스토리지 ──
    persistence:
      enabled: true            # 스토리지 사용 여부
      mountPath: /var/lib/langflow  # 컨테이너 내부 마운트 경로 (Langflow 데이터 디렉터리)
      accessMode: ReadWriteOnce     # 접근 모드 (단일 Pod 읽기/쓰기)
      storageClassName: ""          # 스토리지 클래스 (비워두면 기본값 사용)
      size: 1Gi                     # 볼륨 크기
      # 기존에 만든 볼륨을 연결하려면 아래 주석을 해제하세요.
      # existingClaim: {volume-id}  # 스토리지 메뉴에서 생성한 볼륨 ID

    # ── 환경 변수 ──
    env:
      LANGFLOW_HOST: "0.0.0.0"     # 수신 대기 주소 (모든 인터페이스)
      LANGFLOW_PORT: "7860"         # 서비스 포트

    # ── 외부 접속 경로 (필수) ──
    httpRoute:
      enabled: false           # true로 변경하세요.
      hostname: ""             # 형식: {서브도메인}.{Runway 기본 도메인}
      hostnames: []            # 여러 도메인이 필요한 경우 목록으로 입력
    ```

> **Tip**: 폐쇄망 환경에서 Python 개발 환경 사용 시
>
> **Code Server**나 **JupyterLab**을 폐쇄망 환경에서 사용하는 경우, Python 패키지 설치를 위해 내부 PyPI 미러 서버 설정이 필요합니다.
> 자세한 내용은  **[폐쇄망 환경: PyPI 서버 설정](#pypi-config)**을 참고하세요.

---

### 필수 설정: 외부 접속 경로 (httpRoute)

외부에서 앱에 접속하려면 httpRoute를 활성화해야 합니다. 일반적으로 앱마다 아래와 같은 목적으로 외부 접속 경로를 생성합니다.

| 앱 | 접속 목적 |
|----|----------|
| Code Server | 브라우저에서 VS Code UI 직접 사용 |
| JupyterLab | 브라우저에서 노트북 UI 직접 사용 |
| Langflow | 브라우저에서 비주얼 에디터 UI 직접 사용 |
| Qdrant | 브라우저 대시보드 접속 또는 외부 클라이언트에서 API 호출 |
| Milvus | 외부 클라이언트(SDK/API)에서 접근 (웹 UI 없음, 별도 Attu 배포 필요) |
| Chroma DB | 외부 클라이언트(SDK/API)에서 접근 (웹 UI 없음) |

```yaml title="수정 전 (기본값)"
httpRoute:
  enabled: false
  hostname: ""
  hostnames: []
```

```yaml title="수정 후" hl_lines="2 3"
httpRoute:
  enabled: true
  hostname: "my-codeserver.v2.mrxrunway.ai"
```

| 항목 | 설명 |
|------|------|
| `enabled` | `true`로 변경하여 외부 접속 활성화 |
| `hostname` | `{원하는 서브도메인}.{Runway 기본 도메인}` 형식으로 입력 |
| `hostnames` | 여러 도메인이 필요한 경우 목록으로 입력 (일반적으로 비워둠) |

> **Note**: hostname 형식
>
> `hostname`은 `{서브도메인}.{Runway 기본 도메인}` 형식을 따릅니다.
> Runway 기본 도메인은 환경에 따라 다르므로, 관리자에게 확인하거나 기존 애플리케이션의 엔드포인트 주소를 참고하세요.

---

### 선택 설정

아래 항목은 필요한 경우에만 수정합니다.

#### GPU 사용

딥러닝 학습 등 GPU가 필요한 경우, 두 곳의 주석을 해제합니다.

**1) GPU 스케줄링** — `podAnnotations`에서 사용할 GPU를 지정합니다.

```yaml
podAnnotations:
  # 아래 중 하나를 선택하세요
  gpu_uuid: "GPU-xxxx.., GPU-yyyy..."         # 특정 GPU UUID 지정
  gpu_type: "1080,NVIDIA GeForce RTX 2080 Ti" # GPU 모델명으로 지정
```

| 방식 | 설명 | 사용 시점 |
|------|------|----------|
| `gpu_uuid` | GPU의 고유 UUID를 직접 지정 | 특정 GPU 장치를 사용해야 할 때 |
| `gpu_type` | GPU 모델명으로 지정 (쉼표로 여러 모델 가능) | 모델 종류만 지정하면 될 때 |

**2) GPU 리소스 요청** — `resources`의 requests와 limits에서 GPU 항목 주석을 해제합니다.

```yaml
resources:
  requests:
    cpu: 100m
    memory: 512Mi
    nvidia.com/gpu: 1            # GPU 수량
    nvidia.com/gpucores: 50      # GPU 코어 비율 (%)
    nvidia.com/gpumem: 1024      # GPU 메모리 (MiB)
  limits:
    cpu: 500m
    memory: 1Gi
    nvidia.com/gpu: 1
    nvidia.com/gpucores: 50
    nvidia.com/gpumem: 1024
```

| 항목 | 설명 |
|------|------|
| `nvidia.com/gpu` | 요청할 GPU 수량 |
| `nvidia.com/gpucores` | GPU 코어 사용 비율 (%) |
| `nvidia.com/gpumem` | GPU 메모리 (MiB 단위) |
| `nvidia.com/gpumem-percentage` | GPU 메모리 비율 (%) — `gpumem`과 택 1 |

> **Info**: GPU 자원 설정 상세 가이드
>
> GPU 리소스 요청 규칙, 카드 종류 지정 등 자세한 내용은  **[GPU 자원 설정 가이드](gpu-guide.md)**를 참고하세요.

> **Tip**: 리소스 현황 확인
>
> 애플리케이션 생성 화면 왼쪽의 **리소스 현황** 패널에서 프로젝트에 할당된 GPU 현황을 확인할 수 있습니다. 할당 가능한 범위 내에서 설정하세요.

---

#### 기존 볼륨 연결 (persistence)

미리 생성한 스토리지 볼륨을 애플리케이션에 연결하려면 `existingClaim`의 주석을 해제합니다.

```yaml title="수정 전 (기본값 — 차트가 새 볼륨 자동 생성)"
persistence:
  enabled: true
  mountPath: /config
  accessMode: ReadWriteOnce
  storageClassName: ""
  size: 1Gi
  # existingClaim: {volume-id}
```

```yaml title="수정 후 — 기존 볼륨 연결" hl_lines="4"
persistence:
  enabled: true
  mountPath: /config
  existingClaim: my-volume-id    # 스토리지 메뉴에서 생성한 볼륨 ID
```

| 항목 | 설명 |
|------|------|
| `mountPath` | 애플리케이션 내부에서 볼륨이 마운트되는 경로 |
| `existingClaim` | 스토리지 메뉴에서 생성한 볼륨 ID |

> **Note**: `existingClaim`을 설정하면 `storageClassName`, `size`, `accessMode`는 무시됩니다
>
> 이미 생성된 볼륨을 그대로 사용하므로, 나머지 스토리지 설정은 적용되지 않습니다. 삭제하거나 남겨두어도 무방합니다.

볼륨 생성 방법은  **[스토리지 가이드](../storage/volume-control.md#create-volume)**를 참고하세요.

---

#### 레플리카 확장 (replicaCount)

고가용성이 필요하거나 트래픽을 분산해야 할 때 인스턴스 수를 늘립니다.

```yaml
replicaCount: 2  # 기본값 1 → 필요한 수만큼 증가
```

> **Warning**: 레플리카를 늘리면 리소스도 비례하여 소비됩니다
>
> 예를 들어, CPU 500m / 메모리 1Gi 설정에서 replicaCount를 2로 늘리면, 프로젝트 전체에서 CPU 1000m / 메모리 2Gi를 사용하게 됩니다.

---

#### CPU · 메모리 조정 (resources)

애플리케이션이 사용할 CPU와 메모리를 프로젝트 리소스 현황에 맞게 조정합니다.

```yaml
resources:
  requests:          # 최소 보장 리소스
    cpu: 100m        # CPU 0.1코어
    memory: 512Mi    # 메모리 512MB
  limits:            # 최대 사용 가능 리소스
    cpu: 500m        # CPU 0.5코어
    memory: 1Gi      # 메모리 1GB
```

| 항목 | 기본값 | 조정 기준 |
|------|--------|----------|
| `requests.cpu` | `100m` | 가벼운 코딩이면 기본값 유지 |
| `requests.memory` | `512Mi` | 대규모 데이터 처리 시 `1Gi` 이상 |
| `limits.cpu` | `500m` | 빌드·컴파일이 잦으면 `1000m` 이상 |
| `limits.memory` | `1Gi` | 메모리 부족(OOMKilled) 발생 시 증가 |

---

#### 폐쇄망 환경: PyPI 서버 설정

폐쇄망 환경에서는 외부 PyPI 서버(`https://pypi.org`)에 접근할 수 없으므로, 내부 PyPI 미러 서버를 지정하여 Python 패키지를 설치해야 합니다. Python 패키지 설치 시 내부 PyPI 미러 서버를 사용하도록 설정하는 방법은 크게 세 가지입니다.  

> **Info**: 적용 대상 앱
> 이 설정은 **Code Server**, **JupyterLab** 등 Python 개발 환경에서 필요합니다.

> **Warning**: PyPI 미러 서버 주소 확인
> 실제 내부 PyPI 미러 서버 주소는 **플랫폼 관리자에게 문의**하세요.  
> 예시의 `https://pypi.runway.com`은 설명을 위한 가상의 주소입니다.

=== "방법 1: 환경변수 설정 (권장)"

    애플리케이션 생성 시 values.yaml에서 환경변수를 설정하여 모든 pip 명령어에 자동 적용합니다.

    - **장점**: 애플리케이션 생성 시 한 번만 설정하면 모든 pip 명령어에 자동 적용되며, 재배포 시에도 설정 유지
    - **단점**: 애플리케이션 생성 단계에서 미리 설정 필요

    ```yaml title="values.yaml에 환경변수 추가"
    # ── 환경 변수 ──
    env:
      PIP_INDEX_URL: "https://pypi.runway.com/simple"
      PIP_EXTRA_INDEX_URL: "https://pypi.org/simple"
      PIP_TRUSTED_HOST: "pypi.runway.com"  # HTTPS 미사용 또는 사설 인증서 환경
    ```

    > **Info**: trusted-host가 필요한 경우
    > 내부 PyPI 서버가 **HTTP를 사용하거나 사설 인증서를 사용**하는 경우, SSL 인증서 검증을 우회하기 위해 `PIP_TRUSTED_HOST`를 설정해야 합니다.
    > 값에는 PyPI 서버의 호스트명(도메인)만 입력합니다. (예: `pypi.runway.com`)

    > **Tip**: env 영역 추가 위치
    > 기본 values.yaml에 `env` 영역이 없다면 새로 추가하면 됩니다.
    > 스토리지(`persistence`) 설정과 외부 접속 경로(`httpRoute`) 사이에 배치하는 것을 권장합니다.

=== "방법 2: requirements.txt에 설정"

    requirements.txt 파일 상단에 index-url을 지정합니다.

    - **장점**: 프로젝트별로 일관된 패키지 관리 가능
    - **단점**: requirements.txt를 사용하는 경우에만 적용됨

    ```txt title="requirements.txt"
    --index-url https://pypi.runway.com/simple
    --extra-index-url https://pypi.org/simple
    --trusted-host pypi.runway.com

    pandas==2.0.0
    numpy==1.24.0
    scikit-learn==1.3.0
    ```

    ```bash title="설치 시"
    pip install -r requirements.txt
    ```

    > **Tip**: trusted-host 옵션
    > 내부 PyPI 서버가 HTTP를 사용하거나 사설 인증서를 사용하는 경우, `--trusted-host` 옵션을 추가하세요.

=== "방법 3: pip install 명령어에 옵션 지정"

    패키지 설치 시마다 `--index-url` 옵션을 직접 입력합니다.

    - **장점**: 특정 패키지만 내부 서버에서 설치할 때 유용
    - **단점**: 매번 옵션을 입력해야 하므로 번거로움

    ```bash
    pip install pandas --index-url https://pypi.runway.com/simple --trusted-host pypi.runway.com
    ```

    > **Tip**: trusted-host 옵션 추가
    > 내부 PyPI 서버가 HTTP를 사용하거나 사설 인증서를 사용하는 경우, `--trusted-host` 옵션을 함께 사용하세요.
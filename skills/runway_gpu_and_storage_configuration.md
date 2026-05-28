# [Skill] Runway GPU 및 고급 자원 설정 가이드

본 문서는 Runway 플랫폼에서 GPU 및 공유 메모리 등 고성능 머신러닝 개발 및 추론 워크로드에 필수적인 하드웨어 자원을 세부적으로 설정하고 제어하는 가이드입니다.

---

## 1. GPU 리소스 설정 개요

GPU 자원이 필요한 애플리케이션(Code Server, JupyterLab 등) 또는 모델 배포 배포 시 `values.yaml` 의 Pod 템플릿(pod spec) 리소스 정의 영역에 세부 자원을 기입합니다.

### 1) GPU 리소스 키 정의

| 리소스 식별 키 | 설명 | 입력 단위 |
|---|---|---|
| **`nvidia.com/gpu`** | 컨테이너에 할당할 **물리적 GPU 카드 개수** (필수 지정) | 정수 (Integer) |
| **`nvidia.com/gpumem`** | GPU 카드 1개당 요청할 **상세 그래픽 메모리 용량** | MiB 단위 정수 |
| **`nvidia.com/gpumem-percentage`** | GPU 카드 1개당 요청할 **상세 그래픽 메모리 비율** | % 단위 정수 (0~100) |
| **`nvidia.com/gpucores`** | GPU 카드 1개당 요청할 **GPU 코어 성능 비율** | % 단위 정수 (0~100) |

---

## 2. GPU 분할 및 요청 규칙 (GPU Sharing & Partitioning)

고가의 GPU 리소스를 여러 컨테이너가 효율적으로 나눠 쓰기 위한 **정밀 분할 규칙**을 반드시 준수해야 합니다.

### 핵심 제약 조건
- **물리 지정 필수**: `nvidia.com/gpu` 수량 지정은 필수이며, 분할 자원 필드는 선택 기입합니다.
- **기본 전 점유**: 분할 설정을 기입하지 않으면 GPU 자원 100%를 독점 사용하는 것으로 간주됩니다.
- **메모리 상호 배타성**: `nvidia.com/gpumem`과 `nvidia.com/gpumem-percentage` 중 **하나만 기입**해야 합니다. 동시에 기입 시 절대 메모리 용량 단위인 `gpumem` 값만 유효하게 동작합니다.
- **공유 필수 조건**: `nvidia.com/gpucores`(코어 비율)만 단독으로 기입하면 메모리는 독점 점유 상태가 되므로 타 컨테이너와 **자원 공유가 불가능**합니다. 다른 워크로드와 GPU를 안전하게 나누어 쓰려면 **반드시 코어 비율(`gpucores`)과 메모리(`gpumem` 또는 `gpumem-percentage`)를 동시에 정의**하여 기입해야 합니다.
- **카당 동일 복제**: 분할 자원 값은 할당한 모든 GPU 카드마다 개별적으로 동일 적용됩니다. (예: `nvidia.com/gpu: 2`, `gpucores: 50` 지정 시 총 2장의 카드에서 각각 50%씩 할당).
- **Requests & Limits 일치성**: Kubernetes 스케줄링 보장 정책에 의해 `resources.requests`와 `resources.limits` 영역의 GPU 키값들은 **항상 완벽히 일치**해야 합니다. (Limits 영역만 입력하면 Requests는 자동 복사되어 채워집니다.)

### 2) 설정 예시 (YAML)

**GPU 2장을 각각 코어 50%, 그래픽 메모리 2GiB(2048MiB)로 할당받는 설정:**
```yaml
spec:
  containers:
    - name: ml-container
      resources:
        limits:
          nvidia.com/gpu: 2
          nvidia.com/gpucores: 50
          nvidia.com/gpumem: 2048
```

---

## 3. 특정 GPU 노드 및 제품군 타겟팅 (GPU Node Selectors)

특정 아키텍처나 하이엔드 GPU(예: A100, H100, RTX 3090 등)를 명확히 지정하여 워크로드를 배치할 때, Pod metadata의 **Annotation**을 활용합니다.

| Annotation 키 | 설명 및 입력 방식 |
|---|---|
| **`nvidia.com/use-gputype`** | 허용할 GPU 제품 공식 명칭 목록. 쉼표(`,`)로 구분하며 부분 문자열 일치 필터링을 지원합니다.<br>- 예시: `"1080,2080 Ti,A100"` |
| **`nvidia.com/use-gpuuuid`** | 허용할 GPU 물리 하드웨어의 UUID 목록. 쉼표(`,`)로 구분합니다. |

- 두 가지 어노테이션을 혼용할 시 AND 연산으로 작동합니다.
- 별도 미기입 시 클러스터 내 사용 가능한 모든 유휴 GPU 노드 중 스케줄링됩니다.

### 설정 예시 (YAML)
```yaml
metadata:
  annotations:
    nvidia.com/use-gputype: "3090,A100"
```

---

## 4. 고급 자원: 공유 메모리 (Shared Memory) 설정

PyTorch 기반 딥러닝 트레이닝 시 멀티 프로세스로 데이터를 전처리하는 **DataLoader** 연산(`num_workers > 0` 사용 시)이나 **NVIDIA Triton Inference Server** 운영 시 복사 오버헤드를 낮추기 위해 **공유 메모리 설정**은 필수적입니다.

### 공유 메모리 명세
- **마운트 경로 (Mount Path)**: 기본값으로 `/dev/shm` 경로를 지정하며, 반드시 슬래시(`/`)로 시작하는 절대 경로 형식을 준수해야 합니다.
- **용량 제약 (Size Limit)**: Pod에 할당된 전체 CPU 시스템 메모리(Memory) 총량을 초과할 수 없습니다.

### values.yaml 설정 예시
```yaml
sharedMemory:
  enabled: true
  mountPath: /dev/shm
  size: 2048Mi                      # 2GiB 할당
```

---

## 5. 에이전트 가이드라인 (Agent Best Practices)

- **공유 필수 조건 리마인드**: 사용자가 GPU 자원 공유(Sharing)를 희망하며 코어 혹은 메모리 비율만 단독으로 기입한 설정을 작성하려 할 때, 에이전트는 **"코어 성능(`gpucores`)과 그래픽 메모리(`gpumem`)가 동시에 기입되어야 실질적 공유가 적용된다"**는 정책을 친절하게 상기시켜 설정 보정을 도와야 합니다.
- **용량 단위 검증**: `nvidia.com/gpumem`은 단위 접미사 없이 **숫자만(MiB 단위)** 기입하며, 공유 메모리 `size`는 Kubernetes 표준 표기(예: `2048Mi` 또는 `2Gi`)를 사용하는 특이점이 있으므로 이를 면밀히 비교 검토하십시오.
- **노드 자원 모니터링 사전 확인**: 사용자가 `use-gputype`을 임의 입력하기 전에, 프로젝트 정보에 등록된 사용 가능한 실제 노드 GPU 종류(`docs_markdown\guide\develop\app-create\gpu-guide\index.md` 참고)와 명칭이 정확히 일치하는지 비교하여 오타로 인한 스케줄링 실패(Pending)를 사전에 차단하십시오.

# 모델 서빙 이해하기

모델 서빙(Model Serving)은 학습된 머신러닝 모델을 프로덕션 환경에 배포하고 외부 시스템에서 추론 요청을 받을 수 있도록 서비스화하는 과정입니다.

> 프로젝트 > **추론 엔드포인트** 메뉴

---

## 주요 내용

-    **빠른 시작 가이드**

    ---

    엔드포인트 생성부터 모델 배포, 추론 요청까지 전체 과정을 단계별로 따라해봅니다.

     [모델 서빙 시작하기](../../getting-started/getting-ready/model-serving-quickstart.md)

-    **엔드포인트 생성 및 관리**

    ---

    외부에서 모델에 접근할 수 있는 REST API 엔드포인트를 생성하고 관리합니다. 서빙 런타임을 선택하여 다양한 모델 유형을 지원합니다.

     [엔드포인트 관리하기](endpoint.md)

-    **모델 배포 및 배포 전략**

    ---

    프로젝트 볼륨에 저장된 모델을 배포하고, 여러 모델 버전을 동시에 운영하며, 트래픽 가중치를 조정하여 A/B 테스트나 카나리 배포를 수행합니다.

     [모델 배포하기](model-deployment.md)

-    **배포된 모델 관리**

    ---

    배포된 모델의 상태와 설정을 확인하고, 운영 중 필요에 따라 CPU, 메모리, GPU 등의 컴퓨팅 리소스를 조정하거나 모델을 삭제합니다.

     [배포 관리하기](deployment-manage.md)

-    **추론 요청**

    ---

    배포된 모델에 REST API로 추론 요청을 보내고 응답을 확인합니다. curl, Python, API 클라이언트 등 다양한 방법을 지원합니다.

     [추론 요청하기](inference.md)

---

## 모델 준비 워크플로우

모델 서빙을 시작하기 전, 전체 프로세스를 단계별로 확인하세요.

1. **모델 학습 및 저장**: Code Server, JupyterLab 등에서 모델 학습 후 프로젝트 볼륨에 저장
2. **서빙 런타임 확인**: 학습한 모델 유형에 맞는 서빙 런타임(Triton/MLServer)을 확인합니다. ( **[런타임 선택 가이드](#runtime-guide)** 참고)
3. **디렉토리 구조 구성**: 확인한 런타임에 맞는 폴더 구조 생성 ( **[런타임별 모델 디렉토리 구성](#model-directory-structure)** 참고)
4. **설정 파일 작성**: `config.pbtxt` 또는 `model-settings.json` 작성
5. **엔드포인트 생성**: 확인한 서빙 런타임을 선택하여 엔드포인트 생성
6. **모델 배포**: 볼륨과 모델 경로를 지정하여 모델 배포

> **Example**: 실제 배포 예시
>
> **시나리오**: JupyterLab에서 학습한 ONNX 모델을 Triton으로 배포
>
> 1. JupyterLab에서 모델 학습 후 볼륨 `/mnt/models/my-model/1/model.onnx`에 저장
> 2. 동일 위치에 `config.pbtxt` 파일 생성
> 3. 엔드포인트 생성 시 **Triton Inference Server** 선택
> 4. 모델 배포 시 **볼륨** 선택 및 **모델 경로**에 `my-model` 입력
> 5. 엔드포인트에서 `/v2/models/my-model/infer`로 추론 요청

---

## 모델 서빙 구조

Runway의 모델 서빙은 **엔드포인트**와 **모델 배포** 두 가지 핵심 구성 요소로 이루어집니다.

| 구성 요소 | 설명 |
|-----------|------|
| **엔드포인트** | 외부 시스템이 모델을 호출할 수 있는 접근 지점입니다. REST API 방식으로 요청을 수신하고 응답을 반환합니다. |
| **모델 배포** | 엔드포인트에서 제공할 모델 아티팩트를 지정하고 실행하는 단위입니다. 하나의 엔드포인트에 여러 모델을 등록할 수 있습니다. |

> **Info**: 엔드포인트와 서빙 런타임
> 엔드포인트 생성 시 **서빙 런타임**(Triton Inference Server 또는 MLServer)을 선택해야 합니다.  
> 선택한 런타임에 따라 지원되는 모델 포맷과 디렉토리 구조가 결정되며, 생성 후에는 변경할 수 없습니다.

## 서비스 생성 흐름

```mermaid
flowchart LR
    A["<b>1. 엔드포인트 생성</b><br/>외부에서 접근할 수 있는<br/>API 엔드포인트 생성"]
    B["<b>2. 모델 배포 추가</b><br/>엔드포인트에 서빙할 모델 등록<br/>배포 전략 설정"]
    C["<b>3. 서비스 실행</b><br/>배포된 모델 활성화<br/>추론 요청 준비 완료"]

    A --> B
    B --> C
```

1. **엔드포인트 생성 (런타임 선택)**: 외부에서 접근할 수 있는 API 엔드포인트를 생성하고 서빙 런타임을 선택합니다.
2. **모델 배포 추가**: 엔드포인트에 서빙할 모델을 등록하고 배포 전략을 설정합니다.
3. **서비스 실행**: 배포된 모델을 활성화하여 추론 요청을 받을 준비를 완료합니다.

---

## 서빙 런타임 선택 가이드

엔드포인트 생성 시 배포할 모델 유형에 맞는 서빙 런타임을 선택해야 합니다.

> **Warning**: 런타임 선택 주의사항
> **서빙 런타임은 엔드포인트 생성 후 변경할 수 없습니다.** 모델 유형과 성능 요구사항을 고려하여 신중하게 선택하세요.

### 모델 유형별 런타임 추천

| 모델 유형 | 추천 런타임 | 이유 |
|----------|------------|------|
| **딥러닝 모델** (TensorFlow, PyTorch, ONNX) | Triton | GPU 최적화, 고성능 추론 |
| **전통적 ML 모델** (scikit-learn, XGBoost) | MLServer | 다양한 ML 프레임워크 지원 |
| **MLflow 관리 모델** | MLServer | MLflow 네이티브 지원 |
| **GPU 가속 필요** | Triton | GPU 최적화된 추론 엔진 |
| **경량 추론** | MLServer | Kubernetes 네이티브, 경량 설계 |

---

### 제공 런타임 비교

| 항목 | Triton (v25.12-py3) | MLServer (v1.7.1) |
|------|---------------------|-------------------|
| **지원 모델** | TensorRT, PyTorch, TensorFlow, ONNX, OpenVINO, Python | scikit-learn, XGBoost, LightGBM, MLflow, Custom Python |
| **특화 분야** | 엔터프라이즈급 딥러닝, GPU 가속 추론 | 전통적 ML 모델, 경량 추론 |
| **GPU 지원** | ✅ 최적화 | 선택적 |
| **동적 배칭** | ✅ | ❌ |
| **추론 엔드포인트** | `/v2/models/{model}/infer` | `/v2/models/{model}/infer` |

> **Info**: 서빙 런타임별 특징
>
> === "Triton Inference Server"
>
>     NVIDIA에서 개발한 엔터프라이즈급 딥러닝 모델 서빙 서버입니다.
>
>     **주요 특징**
>
>     - GPU 최적화된 고성능 추론
>     - 동적 배칭 (Dynamic Batching)으로 처리량 극대화
>     - 다양한 딥러닝 프레임워크 통합 지원
>     - 동시 모델 실행 지원
>
>     **지원 모델 포맷**
>
>     TensorRT, PyTorch, TensorFlow, ONNX, OpenVINO, Python backends
>
>     **적합한 사용 사례**
>
>     - GPU 가속이 필요한 대규모 딥러닝 모델
>     - 고성능 추론이 필요한 프로덕션 환경
>     - ONNX, TensorRT 포맷 모델
>
> === "MLServer"
>
>     Kubernetes 네이티브 환경에 최적화된 경량 추론 서버입니다.
>
>     **주요 특징**
>
>     - Kubernetes 네이티브 설계로 클라우드 환경에 최적화
>     - 여러 ML 프레임워크 지원
>     - V2 Inference Protocol 지원
>     - 경량 추론 서버
>
>     **지원 모델 포맷**
>
>     scikit-learn, XGBoost, LightGBM, MLflow, Custom Python models
>
>     **적합한 사용 사례**
>
>     - 전통적인 머신러닝 모델 (scikit-learn, XGBoost, LightGBM 등)
>     - MLflow로 관리되는 모델
>     - 다양한 ML 프레임워크를 혼합하여 사용하는 경우

---

> **Info**: 런타임별 배포 가능한 모델 포맷 설명
>
> === "Triton Inference Server"
>
>     **TensorRT**
>
>     - NVIDIA의 고성능 딥러닝 추론 최적화 엔진
>     - GPU 환경에서 최고의 추론 성능 제공
>     - ONNX, TensorFlow, PyTorch 모델을 TensorRT로 변환하여 배포
>
>     **PyTorch**
>
>     - PyTorch 프레임워크로 학습한 모델
>     - `.pt` 또는 `.pth` 파일 형식
>     - GPU 및 CPU 환경 모두 지원
>
>     **TensorFlow**
>
>     - TensorFlow 프레임워크로 학습한 모델
>     - SavedModel 형식
>     - GPU 및 CPU 환경 모두 지원
>
>     **ONNX**
>
>     - Open Neural Network Exchange 표준 포맷
>     - 다양한 프레임워크 간 모델 교환 가능
>     - 예시:
>         - Hugging Face에서 export된 `model.onnx`
>         - PyTorch에서 `torch.onnx.export()`로 저장한 모델
>
>     **OpenVINO**
>
>     - Intel의 딥러닝 추론 최적화 툴킷
>     - CPU 및 Intel GPU에 최적화
>
>     **Python Backends**
>
>     - 커스텀 Python 코드로 작성된 모델
>     - 전처리/후처리 로직 포함 가능
>
> === "MLServer"
>
>     **scikit-learn**
>
>     - scikit-learn 라이브러리로 학습한 모델
>     - `.pkl` 또는 `.joblib` 파일 형식
>     - 전통적인 머신러닝 모델 (분류, 회귀, 클러스터링 등)
>
>     **XGBoost**
>
>     - XGBoost 라이브러리로 학습한 모델
>     - Gradient Boosting 기반 고성능 모델
>
>     **LightGBM**
>
>     - Microsoft의 Gradient Boosting 프레임워크
>     - 빠른 학습 속도와 효율적인 메모리 사용
>
>     **MLflow**
>
>     - MLflow로 관리되는 모델
>     - 다양한 Flavor 지원 (pyfunc, sklearn, pytorch 등)
>     - 예시:
>         - `mlflow.sklearn.log_model()`
>         - `mlflow.xgboost.log_model()`
>         - `mlflow.pyfunc.log_model()`
>
>     **Custom Python Models**
>
>     - 커스텀 Python 코드로 작성된 모델
>     - MLServer의 Python runtime 사용

---

### 런타임별 모델 디렉토리 구성

각 서빙 런타임은 특정 디렉토리 구조와 설정 파일을 요구합니다. 모델을 배포하기 전에 볼륨에 모델 파일을 올바른 구조로 준비해야 합니다.

> **Info**: 모델 디렉토리 기본 경로
>
> Runway에서 모델은 프로젝트 볼륨에 저장되며, 엔드포인트에 마운트될 때 `/mnt/models/` 경로를 기본 루트로 사용합니다.
>
> - 볼륨 생성 방법:  **[볼륨 생성 및 조회](../../develop/storage/volume-control.md)**
> - 모델 배포 시 경로 지정:  **[모델 배포 방법](model-deployment.md#create)**

Triton Inference Server와 MLServer는 각각 고유한 디렉토리 구조와 설정 파일 형식을 사용합니다. 엔드포인트 생성 시 선택한 런타임에 맞춰 모델 파일을 올바르게 구성해야 합니다.

> **Warning**: 트래픽 분배 사용 시 모델 이름 제약
>
> 하나의 엔드포인트에 여러 모델을 배포하고 **트래픽 분배**를 사용하려면, 모든 모델의 이름을 **`default`로 통일**해야 합니다.
>
> **제약 사항:**
>
> - 추론 요청은 `/v2/models/{model_name}/infer` 형식으로 모델 이름을 포함합니다.
> - 모델 이름{model_name}이 **'default'**가 아니면 트래픽 분배 시 일부 요청이 실패합니다.
>
> **실패 케이스 예시:**
>
> ❌ **케이스 1**: 서로 다른 모델 이름 (모두 실패)
> ```
    엔드포인트: my-endpoint
    - 모델 A: 이름 "mymodel" (50%)
    - 모델 B: 이름 "yourmodel" (50%)

    요청: POST /v2/models/default/infer
    결과: 두 모델 모두 "default"가 아니므로 모든 요청 실패
    ```
>
> ❌ **케이스 2**: 일부만 default (확률적 실패)
> ```
    엔드포인트: my-endpoint
    - 모델 A: 이름 "default" (50%)
    - 모델 B: 이름 "mymodel" (50%)

    요청: POST /v2/models/default/infer
    결과: 모델 A로 라우팅되면 성공, 모델 B로 라우팅되면 실패
    ```
>
> ✅ **올바른 구성**: 모든 모델 이름 통일
> ```
    엔드포인트: my-endpoint
    - 모델 A: 이름 "default" (50%)
    - 모델 B: 이름 "default" (50%)

    요청: POST /v2/models/default/infer
    결과: 모든 요청 정상 처리
    ```

=== "Triton Inference Server" 

    **기본 구조**

    ``` hl_lines="2"
    /mnt/models/
    └── default/
        ├── config.pbtxt              # 모델 설정 파일 (필수)
        └── <version>/                # 모델 버전 디렉토리 (예: 1, 2, ...)
            └── model.<format>        # 모델 파일
    ```

    **필수 구성 요소**

    - **config.pbtxt**: 모델 메타데이터, 입출력 텐서 정의, 배칭 설정 등을 포함하는 설정 파일
    - **버전 디렉토리**: 숫자로 된 버전 폴더 (1, 2, 3, ...) 내에 실제 모델 파일 저장
    - **모델 파일**: 프레임워크별 포맷 (`.onnx`, `.pt`, `.plan` 등)

    

    **예시: ONNX 모델**

    ``` title="폴더 구조" hl_lines="2"
    /mnt/models/
    └── default/
        ├── config.pbtxt
        └── 1/
            └── model.onnx
    ```

    ```protobuf title="config.pbtxt 예시" hl_lines="1"
    name: "default"
    platform: "onnxruntime_onnx"
    max_batch_size: 8
    input [
      {
        name: "input"
        data_type: TYPE_FP32
        dims: [ 3, 224, 224 ]
      }
    ]
    output [
      {
        name: "output"
        data_type: TYPE_FP32
        dims: [ 1000 ]
      }
    ]
    ```

    > **Tip**: Triton 공식 문서
    > 상세한 설정 옵션은 [Triton Model Configuration](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_configuration.html)을 참고하세요.

=== "MLServer"

    **기본 구조**

    ``` hl_lines="2"
    /mnt/models/
    └── default/
        ├── model-settings.json       # 모델 설정 파일 (필수)
        └── <model_files>             # 프레임워크별 모델 파일
    ```

    **필수 구성 요소**

    - **model-settings.json**: 모델 런타임, 입출력 정의 등을 포함하는 설정 파일
    - **모델 파일**: 프레임워크별 파일 (`.pkl`, `.joblib`, `.h5` 등)

    

    **예시: scikit-learn 모델**

    ``` title="폴더 구조" hl_lines="2"
    /mnt/models/
    └── default/
        ├── model-settings.json
        └── model.pkl
    ```

    ```json title="model-settings.json 예시" hl_lines="2"
    {
      "name": "default",
      "implementation": "mlserver_sklearn.SKLearnModel",
      "parameters": {
        "uri": "./model.pkl",
        "version": "v1.0.0"
      }
    }
    ```

    

    **예시: XGBoost 모델**

    ``` title="폴더 구조" hl_lines="2"
    /mnt/models/
    └── default/
        ├── model-settings.json
        └── model.json
    ```

    ```json title="model-settings.json 예시 (XGBoost)" hl_lines="2"
    {
      "name": "default",
      "implementation": "mlserver_xgboost.XGBoostModel",
      "parameters": {
        "uri": "./model.json",
        "version": "v1.0.0"
      }
    }
    ```

    > **Tip**: MLServer 공식 문서
    > 상세한 설정 옵션 및 지원 프레임워크별 가이드는 [MLServer Documentation](https://mlserver.readthedocs.io/)을 참고하세요.

---
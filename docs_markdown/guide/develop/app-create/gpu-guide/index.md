# GPU 상세 설정 가이드

GPU 자원이 필요한 앱을 배포할 때 values.yaml의 Pod spec에 아래 리소스를 지정합니다.

## GPU 리소스 이름과 의미

| 리소스 이름 | 설명 | 단위 |
|------------|------|------|
| `nvidia.com/gpu` | 물리적 GPU 카드 개수 | 정수 |
| `nvidia.com/gpumem` | GPU 카드 1개당 요청 메모리 | MiB (정수) |
| `nvidia.com/gpucores` | GPU 카드 1개당 요청 코어 퍼센트 | percent (정수) |
| `nvidia.com/gpumem-percentage` | GPU 카드 1개당 요청 메모리 퍼센트 | percent (정수) |

## GPU 리소스 요청 규칙

- `nvidia.com/gpu`는 반드시 지정해야 합니다.
- `nvidia.com/gpumem`, `nvidia.com/gpucores`, `nvidia.com/gpumem-percentage`는 분할 사용 요청 시 입력하는 옵션입니다.
    - 분할 자원을 지정하지 않으면 GPU 100%를 사용하는 것으로 처리됩니다.
    - `nvidia.com/gpumem`과 `nvidia.com/gpumem-percentage`는 둘 중 하나만 입력합니다. 둘 다 입력하면 `nvidia.com/gpumem` 값만 사용됩니다.
    - `nvidia.com/gpucores`만 입력하면 메모리 자원은 한 컨테이너가 100% 사용하게 되어 다른 컨테이너와 같은 GPU 카드를 공유할 수 없습니다.
    - `nvidia.com/gpucores`와 `nvidia.com/gpumem`(또는 `nvidia.com/gpumem-percentage`)은 함께 지정할 수 있습니다.
    - 분할 자원은 지정한 GPU 카드 수(`nvidia.com/gpu`)마다 동일하게 적용됩니다.
- `limits`만 입력하면 `requests`에 자동으로 같은 값이 지정됩니다. `requests`와 `limits`는 항상 같은 값이어야 합니다.

아래 예시는 GPU 카드 2개를 각각 코어 50%, 메모리 2GiB로 요청하는 설정입니다.

```yaml title="GPU 할당 요청 예시"
spec:
  containers:
    - resources:
        limits:
          nvidia.com/gpu: 2
          nvidia.com/gpucores: 50
          nvidia.com/gpumem: 2048
```

## GPU 카드 종류 지정

특정 GPU 모델 또는 UUID로 할당을 제한할 수 있습니다. Pod metadata의 annotation으로 지정합니다.

> **Note**: GPU 모델 또는 UUID 확인 방법
>
> 지정할 수 있는 GPU 모델이나 UUID는 리소스 설정 화면에 표시되는 **설정 관련 정보** 버튼을 클릭하여 **노드 리소스** 영역에서 확인할 수 있습니다.
>
> 

| annotation | 설명 |
|------------|------|
| `nvidia.com/use-gputype` | 허용할 GPU 공식 제품명 목록 (콤마 구분, 부분 문자열 허용) |
| `nvidia.com/use-gpuuuid` | 허용할 GPU UUID 목록 (콤마 구분) |

- 미지정 시 사용 가능한 모든 GPU를 할당받을 수 있습니다.
- 두 항목을 모두 지정하면 AND 조건으로 적용됩니다.

```yaml title="GPU 카드 종류 제한 예시"
metadata:
  annotations:
    nvidia.com/use-gputype: "1080,2080 Ti"
```

```yaml title="GPU UUID 지정 예시"
metadata:
  annotations:
    nvidia.com/use-gpuuuid: "GPU-aaaa1111-bb22-cc33-dd44-fffff555555,GPU-gggg6666-hh77-ii88-jj99-kkkkk555555"
```
# 추론 요청

배포된 모델에 추론 요청을 보내고 응답을 확인하는 방법을 안내합니다.

> 프로젝트 > **추론 엔드포인트** 메뉴 > (특정 엔드포인트) 선택 > (특정 모델 배포) 선택

> **Note**: 사전 준비사항
> 엔드포인트가 생성되고 모델이 배포되어 있어야 합니다.
>
>  [추론 엔드포인트 생성](endpoint.md)  
>  [모델 배포](model-deployment.md)

---

## 엔드포인트 URL 확인

추론 요청을 보낼 엔드포인트 URL을 확인합니다.

1. 프로젝트 화면에서 **추론 엔드포인트** 메뉴로 이동합니다.

2. 엔드포인트 목록에서 원하는 엔드포인트를 선택합니다.

3. 엔드포인트 상세 화면에서 **추론 URL**을 확인합니다.

    > **Info**: 추론 URL 확인
    >
    > 추론 URL은 배포 환경에 따라 다를 수 있습니다. 엔드포인트 상세 화면에서 표시되는 **추론 URL**을 사용하세요.
    >
    > 

---

## 직접 테스트하기

모델 배포 상세 화면의 **직접 API 접근** 영역에서 별도 도구 없이 바로 추론 요청을 보내고 응답을 확인할 수 있습니다.

> 추론 엔드포인트 > (엔드포인트 선택) > (배포 선택) > **직접 API 접근**

> **Info**: API 키 불필요
> 직접 API 접근을 사용할 때는 API 키 없이도 추론 요청이 가능합니다.

1. 프로젝트 화면에서 **추론 엔드포인트** 메뉴로 이동합니다.

2. 엔드포인트 목록에서 테스트할 엔드포인트를 선택합니다.

    

3. 엔드포인트 상세 화면의 **모델 배포** 목록에서 테스트할 배포를 선택합니다.

    

4. 배포 상세 화면 하단의 **직접 API 접근** 영역을 확인합니다.

    

    > **Note**: 배포되지 않은 모델
    > 모델이 배포(Deployed) 상태가 아닌 경우 영역이 비활성화되며 요청을 보낼 수 없습니다.

5. **요청 URL**과 **요청 본문**을 확인합니다.

    - **요청 URL**: 복사 아이콘을 클릭하면 URL 전체가 클립보드에 복사됩니다.

    > **Info**: 직접 API 접근 URL과 엔드포인트 추론 URL의 차이
    > 직접 API 접근의 URL은 트래픽 가중치(Traffic Weight)와 관계없이 **해당 배포로 직접** 요청을 보냅니다.  
    > 엔드포인트 추론 URL로 요청 시에는 설정된 트래픽 가중치에 따라 라우팅됩니다.

    - **요청 본문**: 배포 정보를 기반으로 JSON 요청값이 자동으로 구성됩니다. 모델 입력 스펙에 맞게 `data` 값 등을 수정하세요.
    - 초기화 아이콘을 클릭하면 자동 구성된 기본값으로 복원됩니다.

6. **요청 전송** 버튼을 클릭합니다.

7. **응답** 영역에서 응답 코드와 결과를 확인합니다.

    - 복사 아이콘을 클릭하면 응답 내용 전체가 클립보드에 복사됩니다.

    

---

## 외부 도구로 추론 요청 보내기

REST API를 통해 외부 도구로 배포된 모델에 추론 요청을 보냅니다.

> **Note**: API 키 필요
> 외부에서 추론 요청을 하려면 API 키가 필요합니다. API 키 발급 방법은  **[API 키 관리](../../manage/account/access-keys.md)**를 참고하세요.

> **Important**: 요청 데이터 구성
> 아래 예시는 V2 Inference Protocol 형식의 샘플입니다. **실제로는 배포한 모델의 입력 스펙에 맞게 `name`, `shape`, `datatype`, `data` 등의 필드를 수정**해야 합니다.
>
> - 모델의 입력 요구사항을 확인하고 그에 맞는 데이터 형식으로 요청하세요.
> - 데이터 타입, 형태(shape), 필드명 등은 모델마다 다를 수 있습니다.

### 필수 요청 정보

추론 요청 시 다음 정보가 필요합니다:

| 항목 | 값 |
|------|------|
| **HTTP Method** | POST |
| **Content-Type** | application/json |
| **Authorization** | Bearer `<API-KEY-TOKEN>` |
| **URL** | 엔드포인트 추론 URL |
| **Body** | 모델 입력 데이터 (JSON 형식) |

> **Warning**: API 키 보안
> - `<API-KEY-TOKEN>` 부분을 발급받은 실제 API 비밀 키로 교체하세요.
> - API 키는 민감한 정보이므로 안전하게 관리하고, 코드에 직접 포함하지 마세요.

### curl을 사용한 요청 예시

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API-KEY-TOKEN>" \
  -d '{
    "inputs": [
      {
        "name": "input_data",
        "shape": [1, 4],
        "datatype": "FP32",
        "data": [[1.0, 2.0, 3.0, 4.0]]
      }
    ]
  }' \
  <추론 URL>/v2/models/default/infer
```

> **Note**: V2 Inference Protocol 형식
> 위 예시는 V2 Inference Protocol 형식을 따르는 샘플입니다.
>
> - `inputs`: 모델 입력 데이터 배열
> - `name`: 입력 텐서 이름 (모델 정의에 따라 다름)
> - `shape`: 입력 데이터의 차원 (예: `[1, 4]`는 1개 샘플, 4개 특성)
> - `datatype`: 데이터 타입 (FP32, FP64, INT32, INT64 등)
> - `data`: 실제 입력 데이터 값
>
> **배포한 모델의 입력 스펙에 맞게 이 필드들을 수정**해야 합니다.

### Python을 사용한 요청 예시

```python
import requests

# 엔드포인트 URL과 API 키 설정
url = "<추론 URL>/v2/models/default/infer"
api_key = "<API-KEY-TOKEN>"

# 요청 헤더
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 요청 데이터
data = {
    "inputs": [
        {
            "name": "input_data",
            "shape": [1, 4],
            "datatype": "FP32",
            "data": [[1.0, 2.0, 3.0, 4.0]]
        }
    ]
}

# 추론 요청 전송
response = requests.post(url, json=data, headers=headers)

# 응답 확인
if response.status_code == 200:
    result = response.json()
    print("추론 결과:", result)
else:
    print(f"오류 발생: {response.status_code}")
    print(response.text)
```

### 기타 API 클라이언트 사용

Postman, Insomnia, HTTPie 등 다양한 API 클라이언트 도구를 사용할 수 있습니다.

1. API 클라이언트를 실행합니다.

2. 다음 정보를 입력합니다:
    - **Method**: POST
    - **URL**: 엔드포인트 추론 URL
    - **Headers**:
        - `Content-Type: application/json`
        - `Authorization: Bearer <API-KEY-TOKEN>`
    - **Body**: 모델 입력 데이터 (JSON 형식)

3. 요청을 전송하고 응답을 확인합니다.

---
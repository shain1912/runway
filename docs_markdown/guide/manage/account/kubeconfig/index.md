# Kubeconfig 활용

Kubeconfig는 Kubernetes 클러스터에 접근하기 위한 인증 설정 파일입니다.  
Runway에서 다운로드한 Kubeconfig 파일을 사용하면 `kubectl` CLI를 통해 Runway 플랫폼의 Kubernetes 클러스터에 접근할 수 있습니다.

> 오른쪽 상단 프로필 아이콘 > **계정 설정** > **다운로드 Kubeconfig** 메뉴

---

## Kubeconfig 다운로드하기

1.  계정 설정 페이지에서 **다운로드 Kubeconfig** 메뉴를 선택합니다.

    

2.  **다운로드 Kubeconfig** 버튼을 클릭합니다.

3.  `config.yml` 파일이 다운로드됩니다.

    

> **Note**: 다운로드되는 Kubeconfig 특징
>
> - 포함 정보: API 서버 주소, CA 인증서, OIDC(issuer, client-id 등), exec 플러그인(kubelogin) 설정
> - 개인 토큰은 파일에 포함되지 않으며, 로그인은 실행 시 Keycloak에서 진행됩니다.

---

## Kubeconfig 파일 구조

다운로드된 Kubeconfig 파일에는 다음 정보가 포함되어 있습니다.

| 항목 | 설명 |
|---|---|
| **clusters** | Runway Kubernetes 클러스터의 API 서버 주소 |
| **contexts** | 클러스터와 사용자 인증 정보의 연결 설정 |
| **users** | Keycloak OIDC 기반 사용자 인증 설정 |

Runway는 **Keycloak OIDC** 인증 방식을 사용합니다. `kubectl` 명령 실행 시,
`kubelogin` 플러그인이 Keycloak을 통해 자동으로 인증을 수행합니다.

```bash title="Kubeconfig 예시"

apiVersion: v1
kind: Config
clusters:
- name: <CLUSTER_NAME>
  cluster:
    server: https://k8s.<DOMAIN_HOST>:6443
    certificate-authority-data: <BASE64_CA_CERT>
contexts:
- name: <CONTEXT_NAME>
  context:
    cluster: <CLUSTER_NAME>
    user: keycloak-user
current-context: <CONTEXT_NAME>
users:
- name: keycloak-user
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: kubectl
      args:
        - oidc-login
        - get-token
        - --oidc-issuer-url=https://keycloak.<DOMAIN_HOST>/realms/<REALM_NAME>
        - --oidc-client-id=<CLIENT_ID>
        - --oidc-extra-scope=openid,profile,email,offline_access,groups
      interactiveMode: IfAvailable
      provideClusterInfo: true

```

---

## Kubeconfig 파일 사용 방법

Keycloak OIDC로 Kubernetes 접속 방법을 안내합니다.

---

### 사전 요구 사항

Kubeconfig를 사용하려면 다음 도구가 설치되어 있어야 합니다.

-    **kubectl**

    ---

    kubectl는 클러스터와 ±1 minor 범위 버전 설치 권장

    - [macOS 설치 가이드](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/)
    - [Linux 설치 가이드](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)

-    **kubelogin**

    ---

    kubectl oidc-login 플러그인 (int128/kubelogin)

    - [GitHub Setup Guide](https://github.com/int128/kubelogin)
    - [Releases (바이너리 다운로드)](https://github.com/int128/kubelogin/releases)

---

### Kubeconfig 적용 위치

> **Warning**: 기존 Kubeconfig 덮어쓰기 주의
>
> `~/.kube/config` 경로에 이미 다른 클러스터의 설정 파일이 있는 경우, 파일을 덮어쓰면 기존 설정이 유실됩니다. 여러 클러스터를 사용하는 경우 `KUBECONFIG` 환경 변수를 사용하거나, 기존 파일과 병합하여 사용하세요.

다운로드한 `config.yml` 파일을 다음 방법 중 하나로 적용합니다.

```bash title="방법 1: 기본 경로에 배치"

cp config.yml ~/.kube/config

```

```bash title="방법 2: 환경 변수로 지정"

export KUBECONFIG=~/kubeconfigs/config.yaml

```

> **Info**: 여러 kubeconfig 파일 동시 사용
> 
> 여러 kubeconfig 파일을 동시에 쓰려면 콜론(:)으로 구분(macOS/Linux)하여 결합할 수 있습니다.  
> 예: export KUBECONFIG=~/.kube/config:~/work/kubeconfig-dev.yaml

---

### 클러스터 접근 확인

```bash
kubectl get namespaces
```

최초 실행 시 브라우저가 열리며 Keycloak 로그인 페이지로 이동합니다. Runway 계정으로 로그인하면 인증이 완료되고 이후 명령이 정상적으로 실행됩니다.

---

### 프로젝트 네임스페이스 확인

사용 중인 프로젝트의 네임스페이스는 프로젝트 ID와 같습니다. 

> 프로젝트 > **설정** > **일반** 메뉴 > **일반** 영역 > **ID**

---

### 네임스페이스 고정(선택)

필요한 경우, 프로젝트 네임스페이스를 kubeconfig에 고정할 수 있습니다.(선택사항)

kubeconfig의 context.namespace를 채우면, 매번 -n 옵션을 넣지 않아도 기본 네임스페이스로 동작합니다.

```bash title="kubeconfig 예시 (발췌)"

apiVersion: v1
kind: Config
contexts:
- name: <CONTEXT_NAME>
  context:
    cluster: <CLUSTER_NAME>
    user: keycloak-user
    namespace: my-project   # ← 여기 값을 프로젝트 네임스페이스로 설정

```

```bash

# 고정 적용 후, -n 옵션 없이도 동작
kubectl get pods

```
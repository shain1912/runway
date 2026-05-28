# Helm 차트 이해하기

Runway에서 사용자가 앱을 배포하는 방식은 **앱 카탈로그**든 **직접 배포**든, 모두 Helm Chart를 기반으로 합니다.
앱 카탈로그는 자주 사용하는 Helm Chart의 values.yaml을 간소화하여 템플릿으로 제공하는 방식이고, 직접 배포는 Helm Chart의 모든 설정을 사용자가 직접 지정하는 방식입니다.

이 페이지에서는 Runway에서 앱을 이해하고 배포하기 위해 알아야 할 Helm의 핵심 개념과 외부에서 제공하는 주요 Helm Chart를 검색하는 방법을 설명합니다.

---

## Helm이란?

Helm은 Kubernetes 애플리케이션을 패키지 형태로 묶어 배포할 수 있도록 하는 **Kubernetes 패키지 관리자**입니다.

- **Docker 이미지** — 컨테이너 단위
- **Helm** — 여러 Kubernetes 리소스(Deployment, Service 등)를 패키징한 단위

단순히 컨테이너 하나를 띄우는 것이 아니라, 앱을 실행하기 위해 필요한 구성 전체를 한 번에 배포할 수 있습니다.

---

## Helm Chart

**Helm Chart**는 애플리케이션을 배포하기 위한 **설정 파일들의 묶음**입니다.

하나의 웹 애플리케이션을 배포할 때 필요한 구성 요소 — Deployment, Service, ConfigMap, PersistentVolume, Ingress — 를 **하나의 패키지(폴더)**로 담아둔 것입니다.

```
my-app/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
```

---

## Helm Release

Helm에서 **Chart를 설치하면 Release가 생성**됩니다.

- **Chart** — 배포 템플릿
- **Release** — 실제 클러스터에 설치된 애플리케이션 인스턴스

같은 Chart라도 서로 다른 설정(values.yaml)으로 여러 Release를 만들 수 있습니다.

예:

- `codeserver-dev`
- `codeserver-prod`

Runway에서 애플리케이션 하나는 내부적으로 **하나의 Helm Release**에 해당합니다.  
즉, 앱을 생성한다는 것은 Helm Release를 하나 생성하는 것과 같습니다.

---

## Namespace와 프로젝트 격리

Kubernetes는 리소스를 **Namespace 단위로 격리**합니다.

Runway에서는 **프로젝트가 하나의 Namespace와 매핑**됩니다.

구조를 단순화하면 다음과 같습니다:

- 하나의 프로젝트
- 하나의 Kubernetes Namespace
- 그 안에 여러 Helm Release(애플리케이션)

이 구조 덕분에:
- 서로 다른 프로젝트 간 리소스가 격리되며
- 동일한 이름의 애플리케이션도 다른 프로젝트에서 독립적으로 배포할 수 있습니다.

---

## values.yaml

**values.yaml**은 Helm Chart의 설정 값을 담고 있는 파일로, "이 앱을 어떻게 배포할지"를 사용자가 정의하는 공간입니다.

앱 카탈로그의 값은 각 앱에 맞게 간소화된 형태로 제공되며, Helm 직접 배포 시에는 사용자가 직접 작성합니다.
아래는 values.yaml의 일부 예시입니다.

```yaml title="values.yaml 예시"
replicaCount: 1  # 실행할 인스턴스 수

# 컨테이너 이미지 설정
image:
  repository: cr.makina.rocks/runway/applications/codeserver  # 이미지 경로
  tag: 4.96.2                                                 # 이미지 버전

# 네트워크 설정
service:
  type: ClusterIP  # 클러스터 내부 통신용
  port: 8443       # 앱이 사용하는 포트

# 리소스 할당
resources:
  requests:        # 최소 보장 리소스
    cpu: 100m      # CPU 0.1코어
    memory: 512Mi  # 메모리 512MB
  limits:          # 최대 사용 가능 리소스
    cpu: 500m      # CPU 0.5코어
    memory: 1Gi    # 메모리 1GB

# 스토리지 설정
persistence:
  enabled: true  # 스토리지 사용 여부
  size: 1Gi      # 볼륨 크기

# 외부 접속 경로 설정
httpRoute:
  enabled: false  # true로 변경하면 외부에서 접속 가능
  hostname: ""    # 형식: {서브도메인}.{Runway 기본 도메인}
```

앱 카탈로그에서는 이 중 자주 조정하는 항목(리소스, 스토리지, 접속 경로 등)만 노출해 입력 부담을 줄입니다.

---

## Helm Repository

**Helm Repository**는 Helm Chart 파일들을 저장해 둔 **원격 저장소**입니다. apt나 Homebrew의 repository와 동일한 개념입니다.

Runway에서는 외부 Helm Repository에 있는 오픈소스 애플리케이션뿐만 아니라, 사용자가 직접 개발한 애플리케이션도 Helm Chart로 패키징하여 배포할 수 있습니다.

앱 배포 흐름:

1. Helm Repository 주소를 등록합니다.
2. 등록된 Repository에서 Chart 목록을 조회합니다.
3. 원하는 Chart를 선택하고, 설정을 구성하여 앱을 배포합니다.

자세한 배포 방법은  **[사용자 정의 앱 배포](../app-create/custom-app.md)**를 참고하세요.

---

## 주요 Helm Repository

많이 사용되는 외부 Helm Repository 목록입니다. [Artifact Hub](https://artifacthub.io/)에서 더 다양한 Chart 정보를 확인할 수 있습니다.

| 이름 | 주요 패키지 | 헬름 리포지토리 URL |
|------|------------|-----|
| **Bitnami** | Redis, PostgreSQL, MySQL, MongoDB, Kafka, Nginx 등 | https://charts.bitnami.com/bitnami |
| **Grafana** | Grafana, Loki, Tempo, Mimir | https://grafana.github.io/helm-charts |
| **Prometheus Community** | kube-prometheus-stack | https://prometheus-community.github.io/helm-charts |
| **MinIO** | S3 호환 오브젝트 스토리지 | https://charts.min.io/ |
| **Seldon Core** | 모델 서빙·추론 | https://seldonio.github.io/helm-charts |
| **NATS** | 분산 메시징 | https://nats-io.github.io/k8s/helm/charts/ |
| **Elastic** | Elasticsearch, Kibana, Logstash | https://helm.elastic.co |
| **BentoML (Yatai)** | 모델 패키징·서빙 | https://bentoml.github.io/helm-charts |
| **Spark-on-K8s** | Spark 클러스터 | https://googlecloudplatform.github.io/spark-on-k8s-operator |
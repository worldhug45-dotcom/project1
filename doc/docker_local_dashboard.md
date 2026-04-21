# Docker Compose 로컬 실행 가이드

이 문서는 웹 운영자 대시보드를 로컬에서 표준 방식으로 실행하기 위한 Docker Compose 가이드다.
기본 `compose.yaml`은 fixture 중심 로컬 스타터이고, `compose.api.yaml`은 실제 API 모드 전환용 2단계 override다.

## 목적

- 단일 컨테이너로 웹 대시보드를 실행한다.
- 기존 `app.presentation.web.server`를 그대로 사용한다.
- `config`, `data`, `output`, `doc` 디렉터리는 로컬 볼륨으로 유지한다.
- `/health`를 Docker healthcheck에 연결한다.
- fixture 모드와 api 모드를 설정만 바꿔 전환할 수 있게 한다.

## 포함 파일

- `Dockerfile`
- `compose.yaml`
- `compose.api.yaml`
- `.env.example`
- `config/settings.docker.toml`
- `config/keywords.docker.override.toml`

## 기본 동작

- 컨테이너 기본 실행 명령은 아래와 같다.

```bash
python -m app.presentation.web.server \
  --host 0.0.0.0 \
  --port 8787 \
  --config config/settings.docker.toml \
  --history-path data/observations/bizinfo/collect_observations.json \
  --raw-output-dir data/observations/bizinfo/raw \
  --log-path doc/bizinfo_collect_observation_log.md \
  --state-path data/operations/manual_run_state.json
```

- 기본 compose는 `fixture` 기반 `config/settings.docker.toml`을 그대로 사용한다.
- `compose.api.yaml`은 별도 이미지나 별도 웹 엔진을 추가하지 않고, 환경 변수 override만으로 `api` 모드 전환을 수행한다.

## 볼륨 마운트

아래 디렉터리는 컨테이너 안 `/workspace` 기준으로 bind mount 된다.

- `./config -> /workspace/config`
- `./data -> /workspace/data`
- `./output -> /workspace/output`
- `./doc -> /workspace/doc`

이 구조 덕분에 설정, SQLite DB, observation 기록, Excel 결과물, 운영 문서가 로컬 파일 시스템에 그대로 남는다.

## 환경 변수 구조

두 Compose 파일에서 공통으로 자연스럽게 연결되는 핵심 환경 변수는 아래와 같다.

- `PROJECT1_BIZINFO_CERT_KEY`
- `PROJECT1_G2B_API_KEY`
- `PROJECT1_KEYWORDS_OVERRIDE_PATH`
- `PROJECT1_STORAGE_DATABASE_PATH`
- `PROJECT1_EXPORT_OUTPUT_DIR`

api override에서 source 선택까지 바꾸고 싶으면 아래도 함께 사용할 수 있다.

- `PROJECT1_SOURCES_BIZINFO_ENABLED`
- `PROJECT1_SOURCES_G2B_ENABLED`

현재 collect는 한 번에 하나의 enabled source만 지원하므로, Docker api 모드에서도 둘 중 하나만 활성화해야 한다.

## 실행 방법

### 1. fixture 모드 실행

```bash
docker compose up --build
```

또는 백그라운드:

```bash
docker compose up --build -d
```

이 모드는 기본적으로 fixture 중심 로컬 스타터다.

### 2. api 모드 실행

api 모드는 기본 compose 위에 override만 덧붙인다.

기업마당 API 모드 기본 예시:

```bash
export PROJECT1_BIZINFO_CERT_KEY="your-bizinfo-key"
docker compose -f compose.yaml -f compose.api.yaml up --build
```

PowerShell 예시:

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "your-bizinfo-key"
docker compose -f compose.yaml -f compose.api.yaml up --build
```

api override 기본값은 `bizinfo=true`, `g2b=false`다.

나라장터 API 모드로 전환하려면 source 선택 환경 변수를 함께 바꾼다.

```bash
export PROJECT1_G2B_API_KEY="your-g2b-key"
export PROJECT1_SOURCES_BIZINFO_ENABLED=false
export PROJECT1_SOURCES_G2B_ENABLED=true
docker compose -f compose.yaml -f compose.api.yaml up --build
```

PowerShell 예시:

```powershell
$env:PROJECT1_G2B_API_KEY = "your-g2b-key"
$env:PROJECT1_SOURCES_BIZINFO_ENABLED = "false"
$env:PROJECT1_SOURCES_G2B_ENABLED = "true"
docker compose -f compose.yaml -f compose.api.yaml up --build
```

api override가 하는 일:

- `PROJECT1_RUNTIME_SOURCE_MODE=api` 적용
- 기본 source 선택은 `bizinfo=true`, `g2b=false`
- API 키, keywords override, DB 경로, export 경로는 기존 환경 변수 구조를 그대로 재사용

### 3. 접속 확인

- 대시보드: `http://127.0.0.1:8787`
- health: `http://127.0.0.1:8787/health`

### 4. 상태 확인

```bash
docker compose ps
```

healthcheck는 `/health`를 호출해 컨테이너 상태를 판별한다.

- `ok`: 설정과 최소 운영 파일 접근이 준비됨
- `degraded`: 서버는 살아 있지만 운영 보조 파일 일부가 아직 없음
- `error`: 설정 로드 실패 등으로 건강 상태가 나쁨

`degraded`는 로컬 초기 부팅에서 허용 가능한 상태이며, `data`와 `doc`가 아직 비어 있을 때 나타날 수 있다.

### 5. 종료

```bash
docker compose down
```

## 현재 범위

이번 단계는 로컬 표준 실행용 단일 컨테이너 구조와 api override까지만 포함한다.

- Nginx 없음
- worker/scheduler 분리 없음
- collect/export/observe/status/health 핵심 로직 수정 없음
- 웹 프레임워크 교체 없음

다음 단계에서는 운영 배포용 보강, reverse proxy, 다중 서비스 분리, 이미지 경량화 등을 이어서 검토할 수 있다.

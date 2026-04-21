# 웹 운영자 대시보드 MVP 설계

이 문서는 현재 내부 운영형 CLI 솔루션 위에 웹 형태의 운영자 대시보드 MVP를 추가하기 위한 구조안이다.
목표는 기존 `collect`, `export`, `observe`, `status` 기능을 그대로 재사용하면서, 내부 사용자가 브라우저 한 화면에서 현재 상태와 주요 실행 버튼, 결과물 경로를 바로 확인할 수 있게 만드는 것이다.

## 1. 설계 목표

- 기존 Python 엔진과 Domain 규칙은 그대로 유지한다.
- 웹 레이어는 orchestration과 상태 표시만 담당한다.
- 첫 화면은 단일 운영 화면(single operator cockpit)으로 시작한다.
- 운영자는 코드나 CLI 명령을 몰라도 `collect`, `export`, `observe`, `status`를 실행할 수 있어야 한다.
- Docker Compose로 배포할 수 있도록 경로, 볼륨, 환경 변수 구조를 초기에 정리한다.

## 2. MVP 범위

### 포함 범위

- 현재 상태(`status`) 표시
- `collect` 실행 버튼
- `export` 실행 버튼
- `observe` 실행 버튼
- 최근 결과물 경로 표시
- 현재 `config` 경로 표시
- 현재 `keywords override` 경로 표시
- 최근 collect/export/observe 실행 요약 표시

### 제외 범위

- 나라장터 연동
- 키워드 규칙 자체 수정 화면
- 사용자 인증/권한 관리
- 다중 사용자 세션 관리
- WebSocket 기반 실시간 스트리밍
- 별도 작업 큐/분산 워커

## 3. Visual Thesis

- **Visual thesis**: 어두운 슬레이트-네이비 그라데이션 위에 반투명 유리 패널이 떠 있는 내부 운영 Cockpit
- **Content plan**: masthead, current status plane, action rail, recent artifact strip
- **Interaction thesis**:
  1. 화면 진입 시 배경 광원과 패널 blur가 천천히 떠오르는 entrance motion
  2. 액션 버튼 실행 시 버튼 내부 progress 상태와 패널 테두리 glow 변화
  3. 최근 결과물 경로가 갱신되면 짧은 highlight flash로 업데이트 지점을 인지시킴

## 4. 아키텍처 원칙

### 4-1. 계층 구조

- `Presentation`
  - 웹 라우트
  - 서버사이드 템플릿
  - 정적 CSS/JS
- `Application`
  - 운영자 대시보드용 상태 조회 서비스
  - 수동 실행 orchestration 서비스
  - 웹 액션 요청/응답 DTO
- `Domain`
  - 기존 `Notice`, 키워드 판정, 실행 결과 모델 유지
- `Infrastructure`
  - 기존 SQLite 저장소
  - 기존 기업마당 API adapter
  - 파일 시스템 기반 상태/결과물 조회
  - `manual_run.py` subprocess 실행 gateway

### 4-2. 재사용 원칙

- `collect`, `export`, `observe`, `status`의 핵심 엔진은 계속 CLI/설정 기반으로 유지한다.
- 웹은 직접 Domain 로직을 실행하지 않고, 기존 manual runner 흐름을 감싸는 얇은 orchestration 레이어로 시작한다.
- 현재 `scripts/manual_run.py`가 이미 결과 요약, 경로 출력, 상태 파일 갱신 역할을 수행하므로, 웹 MVP는 이 흐름을 최대한 재사용한다.

### 4-3. 권장 책임 분리

웹 구현 단계에서는 아래처럼 책임을 나누는 것이 가장 안전하다.

```text
app/
  presentation/
    web/
      routes.py
      templates/
        dashboard.html
      static/
        dashboard.css
        dashboard.js
      viewmodels.py
  application/
    operator_dashboard/
      models.py
      status_service.py
      action_service.py
      ports.py
  infrastructure/
    operator_runtime/
      manual_run_gateway.py
      status_snapshot_loader.py
      artifact_locator.py
```

### 4-4. 왜 이 구조가 적합한가

- 현재 CLI가 이미 안정화되어 있으므로, 웹에서 직접 collect/export/observe 로직을 다시 구현하면 중복과 회귀 위험이 커진다.
- subprocess gateway 방식은 기존 수동 운영 흐름과 1:1로 대응하므로 디버깅이 쉽다.
- 이후 필요하면 `manual_run.py` 내부 로직을 `Application` 모듈로 추출해 CLI와 Web이 공용 서비스로 합칠 수 있다.

## 5. 웹 MVP 화면 구성안

### 5-1. 단일 화면 레이아웃

첫 화면은 마케팅형 랜딩 페이지가 아니라, 내부 운영자를 위한 작업 화면으로 구성한다.

```text
┌────────────────────────────────────────────────────────────┐
│ Masthead                                                   │
│ - Dashboard title                                          │
│ - current config path                                      │
│ - keyword override path                                    │
├───────────────────────────────┬────────────────────────────┤
│ Current Status Plane          │ Action Rail                │
│ - latest collect summary      │ - collect button           │
│ - latest export summary       │ - export button            │
│ - latest observe summary      │ - observe button           │
│ - db path                     │ - running / idle indicator │
│ - export output dir           │ - last action timestamp    │
├────────────────────────────────────────────────────────────┤
│ Recent Artifact Strip                                         │
│ - latest xlsx path                                            │
│ - observation history path                                    │
│ - observation report path                                     │
│ - raw jsonl dir                                               │
└────────────────────────────────────────────────────────────┘
```

### 5-2. 영역별 책임

#### A. Masthead

- 화면 이름: `Project1 Operator Dashboard`
- 현재 config 경로
- 현재 keywords override 경로
- 현재 시각 또는 마지막 갱신 시각

#### B. Current Status Plane

- 최근 collect 상태 요약
  - `fetched_count`
  - `saved_count`
  - `skipped_count`
  - `error_count`
- 최근 export 상태 요약
  - 최근 `.xlsx` 파일 경로
  - export output 디렉터리
- 최근 observe 상태 요약
  - observation history 경로
  - observation report 경로
  - raw jsonl 디렉터리

#### C. Action Rail

- `collect` 버튼
- `export` 버튼
- `observe` 버튼
- 현재 실행 중 여부
- 직전 실행 시각
- 실패 시 짧은 안내 문구

#### D. Recent Artifact Strip

- 가장 최근 `.xlsx`
- SQLite DB 경로
- observation history
- observation report
- raw jsonl 디렉터리

### 5-3. 모바일/좁은 화면

- `Action Rail`은 상태 패널 아래로 내려간다.
- 경로 정보는 줄바꿈 가능한 mono block으로 렌더링한다.
- 버튼은 전체 폭으로 확장한다.

## 6. Glassmorphism 디자인 가이드

### 6-1. 전체 톤

- 배경: 심도 있는 blue/teal gradient
- 주요 패널: 반투명 유리 표면
- 강조색: cyan 계열 한 가지
- 텍스트: 차가운 white + muted slate 조합

### 6-2. 추천 스타일 토큰

```css
:root {
  --bg-1: #08111f;
  --bg-2: #0d1f33;
  --bg-3: #123a52;
  --glass-fill: rgba(255, 255, 255, 0.12);
  --glass-stroke: rgba(255, 255, 255, 0.22);
  --glass-shadow: 0 24px 60px rgba(3, 10, 18, 0.38);
  --text-strong: #f4f8fb;
  --text-soft: #b7c8d8;
  --accent: #7fe3ff;
  --accent-strong: #4bc7f1;
}
```

### 6-3. 패널 원칙

- 카드 남발 대신 큰 패널 3개만 사용한다.
- 각 패널은 `backdrop-filter: blur(18px)` 수준의 blur를 가진다.
- 테두리는 진한 선 대신 얇은 translucent stroke로 처리한다.
- 그림자는 무겁게 퍼지지 않고, 깊이를 암시하는 soft shadow로 제한한다.

### 6-4. 타이포그래피

- 본문/제목: `SUIT Variable` 또는 유사한 한국어 가독성 폰트
- 경로/ID/숫자: `JetBrains Mono`
- 헤더는 짧고 단정하게, 설명은 1문장만 사용한다.

### 6-5. 모션 원칙

- 최초 진입: 패널 opacity + translateY 12px 정도의 짧은 reveal
- 버튼 hover: 배경 광택과 border glow만 사용
- 결과 경로 갱신: 600ms 이하의 subtle highlight

### 6-6. 피해야 할 것

- KPI 카드 8~12개를 격자처럼 늘어놓는 구성
- 과도한 neon 효과
- 배경 위에 작은 badge를 과도하게 나열하는 구성
- 내부 운영 도구인데 marketing copy처럼 과장된 헤드라인

## 7. 웹 라우트와 상호작용 구조

### 7-1. 최소 라우트

- `GET /`
  - 운영자 대시보드 렌더링
- `GET /api/status`
  - 현재 상태와 경로, 최근 요약 JSON 반환
- `POST /actions/collect`
  - collect 실행 시작
- `POST /actions/export`
  - export 실행 시작
- `POST /actions/observe`
  - observe 실행 시작
- `GET /health`
  - Docker health check 용도

### 7-2. 액션 실행 방식

웹 MVP에서는 별도 작업 큐 대신 subprocess 기반으로 시작한다.

```text
Web POST /actions/collect
-> Application ActionService
-> ManualRunGateway
-> subprocess: python scripts/manual_run.py collect ...
-> manual_run_state.json 갱신
-> Web status polling
-> Dashboard 화면 반영
```

### 7-3. 상태 조회 방식

상태 조회는 아래 정보를 합쳐서 만든다.

- `data/operations/manual_run_state.json`
- 최신 `.xlsx` 파일 위치
- observation history 최신 레코드
- observation raw jsonl 최신 파일
- 현재 `config` / `keywords override` 경로

### 7-4. 웹 전용 상태 파일

기존 `manual_run_state.json`은 최신 액션 결과 요약에는 충분하지만, 웹에서 “실행 중” 상태를 표시하려면 최소한의 job registry가 있으면 좋다.

권장 추가 파일:

```text
data/operations/web_jobs.json
```

권장 필드:

- `job_id`
- `action`
- `status` (`queued`, `running`, `success`, `failed`)
- `started_at`
- `finished_at`
- `summary_path` 또는 `run_id`
- `error_message`

이 파일은 Presentation 전용 상태이므로 Domain 모델과 분리한다.

## 8. Docker Compose 배포 구조 초안

### 8-1. 서비스 구조

MVP는 단일 웹 컨테이너로 시작한다.

- `operator-web`
  - 웹 화면 제공
  - `manual_run.py` subprocess 실행
  - SQLite 파일 직접 사용
  - export 파일 생성
  - observation 파일 생성

별도 worker, Redis, message broker는 현재 단계에서 도입하지 않는다.

### 8-2. 권장 compose 구조

```yaml
services:
  operator-web:
    build:
      context: .
      dockerfile: docker/web/Dockerfile
    container_name: project1-operator-web
    ports:
      - "8080:8080"
    environment:
      PROJECT1_BIZINFO_CERT_KEY: ${PROJECT1_BIZINFO_CERT_KEY}
      PROJECT1_KEYWORDS_OVERRIDE_PATH: /app/config/keywords.override.toml
      PROJECT1_STORAGE_DATABASE_PATH: /app/data/observations/bizinfo/notices.sqlite3
      PROJECT1_EXPORT_OUTPUT_DIR: /app/output/observations/bizinfo
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./output:/app/output
      - ./doc:/app/doc
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-m", "app.presentation.web.healthcheck"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### 8-3. 볼륨 설계 이유

- `config`
  - `settings.local.toml`
  - `keywords.override.toml`
- `data`
  - SQLite DB
  - `manual_run_state.json`
  - observation history
  - 향후 `web_jobs.json`
- `output`
  - 실제 `.xlsx` 산출물
- `doc`
  - 현재 observation Markdown report가 여기에 저장되므로 호환성을 위해 유지

### 8-4. Docker 관점에서의 주의점

- 현재 observation report가 `doc/`에 생성되므로, generated artifact와 문서 경로가 섞인다.
- Docker MVP에서는 호환성을 위해 `doc` 볼륨을 유지하되, 차기 단계에서 observation report를 `output/observations/` 계열로 이동하는 것을 검토한다.
- 내부 운영 환경이므로 우선 single-container로 시작하고, 장시간 collect와 동시 접속이 늘면 worker 분리를 검토한다.

## 9. 환경 변수 구조

웹/CLI/Docker가 함께 사용할 최소 환경 변수는 아래와 같다.

- `PROJECT1_BIZINFO_CERT_KEY`
- `PROJECT1_KEYWORDS_OVERRIDE_PATH`
- `PROJECT1_STORAGE_DATABASE_PATH`
- `PROJECT1_EXPORT_OUTPUT_DIR`

향후 웹 서버 포트를 분리할 때 추가 후보:

- `PROJECT1_WEB_HOST`
- `PROJECT1_WEB_PORT`
- `PROJECT1_WEB_STATE_PATH`

## 10. 구현용 TODO

### 1차: 공용 orchestration seam 추출

- `manual_run.py` 내부 상태 조회 로직을 재사용 가능한 Application 서비스로 추출
- subprocess 실행을 감싸는 `ManualRunGateway` 추가
- 웹/CLI 공용 `DashboardStatus` DTO 정의

### 2차: 웹 Presentation shell 구현

- `app/presentation/web/` 폴더 생성
- 단일 dashboard route 구현
- glassmorphism CSS와 최소 JS 작성
- 현재 상태 표시 UI 구현

### 3차: 액션 실행 연결

- `collect` 버튼 연결
- `export` 버튼 연결
- `observe` 버튼 연결
- 실행 중 indicator와 최근 상태 refresh 연결

### 4차: Docker 배포

- `docker/web/Dockerfile` 작성
- `docker-compose.yml` 초안 작성
- `/health` endpoint와 healthcheck 연결

### 5차: 운영 안정화

- 중복 클릭 방지
- 액션 실행 중 버튼 disable
- 최근 에러 메시지 표시
- observation report 경로 재배치 검토

## 11. 권장 구현 순서

가장 안전한 순서는 아래와 같다.

1. 상태 조회를 웹/CLI 공용 서비스로 추출
2. 웹 단일 화면과 `GET /api/status` 구현
3. `collect` 액션 연결
4. `export`, `observe` 액션 연결
5. Docker Compose 초안 추가

## 12. 한 줄 결론

웹 운영자 대시보드 MVP는 **기존 CLI 엔진을 재사용하는 얇은 Presentation 레이어**로 시작하는 것이 가장 안전하다.  
즉, 지금 단계에서 가장 좋은 구조는 “새 엔진”이 아니라 **`manual_run/status`를 감싸는 단일 화면형 Glassmorphism 운영 Cockpit + 단일 컨테이너 Docker 배포**다.

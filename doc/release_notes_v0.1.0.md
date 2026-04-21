# Release Notes v0.1.0

## 릴리즈 개요

- 버전: `v0.1.0`
- 성격: 초기 내부 운영형 MVP 릴리즈
- 기준 태그: `v0.1.0`
- 기준 브랜치: `main`

이번 릴리즈는 문서 기반 설계를 실제 실행 가능한 MVP로 연결한 첫 기준점이다.  
현재는 **기업마당 실제 API collect + SQLite 저장 + Excel export + observation + 운영자 편의 도구**까지 포함한다.

## 포함 범위

### 1. collect

- 기업마당 fixture collect
- 기업마당 실제 API collect
- `source_mode=fixture` / `source_mode=api`
- 키워드 기반 적격 판정
- `Notice` 공통 모델 정규화
- skip reason diagnostics

### 2. persistence

- SQLite 저장소 구현
- `DeduplicationKey` 기반 중복 저장 방지
- In-memory repository 테스트 대안 유지

### 3. export

- `NoticeRepositoryPort.list_all()` 기반 export
- 실제 `.xlsx` 생성
- `support_notices` / `bid_notices` 시트 생성
- 엑셀 포맷 규칙 고정

### 4. ops / observation

- 실행 로그와 `RunSummary`
- observation history 누적
- observation Markdown report 생성
- 최근 수집 결과 비교 구조

### 5. operator tooling

- `scripts/manual_run.py`
- `status` 액션
- PowerShell launcher
  - `scripts/run_status.ps1`
  - `scripts/run_collect.ps1`
  - `scripts/run_export.ps1`
  - `scripts/run_observe.ps1`
- 키워드 override 파일

## 이번 릴리즈에서 아직 제외한 항목

- 나라장터 collect 구현
- `all` 액션 완성
- NTIS 연동
- K-Startup 연동
- 검색 UI
- Word 출력
- 알림 연동
- 자동 우선순위 점수화

## 운영자가 바로 쓰는 명령

PowerShell 기준:

### 현재 상태 확인

```powershell
.\scripts\run_status.ps1
```

### 실제 API collect

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

### 실제 API collect + diagnostics

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1 -CollectDiagnostics
```

### export

```powershell
.\scripts\run_export.ps1
```

### observe

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_observe.ps1
```

## 기본 결과물 경로

- SQLite DB: `data/observations/bizinfo/notices.sqlite3`
- export output: `output/observations/bizinfo/`
- observation history: `data/observations/bizinfo/collect_observations.json`
- observation report: `doc/bizinfo_collect_observation_log.md`
- manual runner state: `data/operations/manual_run_state.json`

## 검증 결과

이번 릴리즈 기준 검증 결과는 아래와 같다.

- `python -m unittest discover -v` 통과
- `python -m compileall app tests scripts` 통과
- 전체 테스트 `67`개 통과
- fixture collect / export / observe 수동 경로 검증
- 실제 기업마당 API collect → SQLite 저장 → export 경로 검증

## 알려진 제한사항

### 1. 나라장터 미구현

README 목표에는 포함되어 있지만, 현재 코드 기준으로는 아직 연결하지 않았다.

### 2. `all` 액션 미완성

현재 `all`은 collect → export를 자동 orchestration 하지 않는다.

### 3. observation은 기업마당 중심

현재 observation 누적/분석 구조는 기업마당 collect를 기준으로 설계되어 있다.

### 4. 운영 환경은 Windows PowerShell 기준

launcher는 `.ps1` 스크립트 기준이며, 다른 셸에서는 `manual_run.py` 직접 실행이 더 자연스럽다.

## 다음 단계

다음 릴리즈 후보는 아래 순서가 자연스럽다.

1. 나라장터 collect adapter 구현
2. `all` 액션 완성
3. 운영 상태/observation 시각화 개선

## GitHub Release 본문용 초안

아래 블록은 GitHub Release 본문에 바로 붙여 넣을 수 있다.

```markdown
## v0.1.0

초기 내부 운영형 MVP 릴리즈입니다.

### 포함 범위
- 기업마당 fixture collect
- 기업마당 실제 API collect
- SQLite 저장 및 중복 방지
- 실제 `.xlsx` export
- observation history / report
- operator tooling (`manual_run.py`, launcher, `status`)

### 제외 범위
- 나라장터
- `all` 액션 완성
- NTIS / K-Startup
- 검색 UI / 알림 / Word 출력

### 운영자 명령
```powershell
.\scripts\run_status.ps1
```

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

```powershell
.\scripts\run_export.ps1
```

### 검증
- `python -m unittest discover -v`
- `python -m compileall app tests scripts`
- 전체 테스트 67개 통과
```

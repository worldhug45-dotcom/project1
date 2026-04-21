# AI·인프라·SI 사업기회 탐지용 공고 수집 시스템

기업마당과 향후 나라장터 공고를 수집해, AI·인프라·SI 관점에서 적격 여부를 판정하고 SQLite와 Excel 산출물로 정리하는 내부 운영형 솔루션이다.

## 현재 상태

2026-04-21 기준 현재 구현 상태는 아래와 같다.

| 항목 | 상태 | 설명 |
| --- | --- | --- |
| 기업마당 fixture collect | 완료 | 샘플 응답 기반 collect 흐름이 end-to-end로 동작한다. |
| 기업마당 실제 API collect | 완료 | `source_mode=api`에서 실제 API를 호출해 SQLite 저장까지 이어진다. |
| 키워드 판정/정규화 | 완료 | `Notice` 공통 모델, 도메인 분류, skip reason 진단이 동작한다. |
| SQLite 저장/중복 방지 | 완료 | `DeduplicationKey` 기준으로 중복 저장을 막는다. |
| Excel export | 완료 | 실제 `.xlsx` 파일 생성과 `support_notices` / `bid_notices` 시트 생성이 동작한다. |
| observation 누적 | 완료 | collect diagnostics를 바탕으로 관찰 로그와 history를 누적한다. |
| 운영자 수동 실행 도구 | 완료 | `manual_run.py`, PowerShell launcher, `status` 액션이 준비되어 있다. |
| 나라장터 수집 | 미구현 | README 범위에는 포함되어 있지만 현재 코드는 아직 연결하지 않았다. |
| `all` 액션 완성 | 미구현 | 현재 CLI `all`은 skeleton 상태이며 collect+export orchestration은 아직 연결하지 않았다. |

## 내부 운영자가 바로 쓰는 명령

PowerShell 기준:

```powershell
.\scripts\run_status.ps1
```

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1 -CollectDiagnostics
```

```powershell
.\scripts\run_export.ps1
```

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_observe.ps1
```

운영 가이드는 [manual_operations_guide.md](/C:/code/project1/doc/manual_operations_guide.md)를 기준 문서로 사용한다.

## 핵심 기능

- 기업마당 지원사업 API collect
- fixture 기반 collect 테스트 경로
- 키워드 기반 적격 판정과 skip reason 진단
- `Notice` 공통 모델 정규화
- SQLite 저장 및 중복 방지
- 실제 `.xlsx` export
- observation history / Markdown report 누적
- 운영자용 launcher / `status` / 결과물 경로 요약

## 현재 범위와 제외 범위

### 현재 구현 범위

- 기업마당 공고 조회
- 키워드 기반 적격 여부 판정
- 공통 필드 정규화
- SQLite 저장
- Excel 산출물 생성
- 로그 및 실행 요약
- 운영자 수동 실행 편의 기능

### 아직 구현하지 않은 항목

- 나라장터 공고 조회
- NTIS 연동
- K-Startup 연동
- 검색 UI
- Word 출력
- 알림 연동
- `all` 액션 완성

## 프로젝트 구조

```text
project-root/
├─ app/
│  ├─ application/
│  ├─ domain/
│  ├─ exporters/
│  ├─ filters/
│  ├─ infrastructure/
│  ├─ normalizers/
│  ├─ ops/
│  ├─ persistence/
│  ├─ sources/
│  └─ main.py
├─ config/
├─ data/
├─ doc/
├─ output/
├─ scripts/
├─ tests/
├─ CHECKLIST.md
├─ DECISIONS.md
├─ TASKS.md
└─ README.md
```

## 주요 경로

- 기본 설정: `config/settings.example.toml`
- 운영 설정: `config/settings.local.toml`
- 키워드 override: `config/keywords.override.toml`
- SQLite DB 기본 경로: `data/observations/bizinfo/notices.sqlite3`
- observation history: `data/observations/bizinfo/collect_observations.json`
- observation report: `doc/bizinfo_collect_observation_log.md`
- export output: `output/observations/bizinfo/`
- manual runner state: `data/operations/manual_run_state.json`

## 실행 방식

### 1. 상태 확인

```powershell
.\scripts\run_status.ps1
```

현재 설정 경로, 키워드 override 경로, SQLite DB, output 디렉터리, 최근 `.xlsx`, 최근 collect/export/observe 상태를 한 번에 볼 수 있다.

### 2. collect

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

fixture 모드:

```powershell
.\scripts\run_collect.ps1 -SourceMode fixture
```

### 3. export

```powershell
.\scripts\run_export.ps1
```

### 4. observe

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_observe.ps1
```

## 설정 원칙

- 설정은 `TOML` 기반으로 관리한다.
- 비밀값은 환경 변수로만 주입한다.
- 키워드 추가/제거는 `config/keywords.override.toml`에서 처리한다.
- override 우선순위는 `CLI > 환경 변수 > override 파일 > 설정 파일 > 기본값`이다.

세부 기준은 [settings_schema.md](/C:/code/project1/doc/settings_schema.md)를 따른다.

## 문서 맵

- 공통 데이터 모델: [common_data_model.md](/C:/code/project1/doc/common_data_model.md)
- 설정 구조: [settings_schema.md](/C:/code/project1/doc/settings_schema.md)
- 키워드 판정 규칙: [keyword_matching_rules.md](/C:/code/project1/doc/keyword_matching_rules.md)
- 로그 정책: [logging_policy.md](/C:/code/project1/doc/logging_policy.md)
- 예외 처리 정책: [error_handling_policy.md](/C:/code/project1/doc/error_handling_policy.md)
- 엑셀 포맷 기준: [excel_export_format.md](/C:/code/project1/doc/excel_export_format.md)
- fixture 기준: [fixtures.md](/C:/code/project1/doc/fixtures.md)
- 운영 가이드: [manual_operations_guide.md](/C:/code/project1/doc/manual_operations_guide.md)
- 실제 API 수동 검증: [bizinfo_api_manual_verification.md](/C:/code/project1/doc/bizinfo_api_manual_verification.md)
- 관찰 로그: [bizinfo_collect_observation_log.md](/C:/code/project1/doc/bizinfo_collect_observation_log.md)
- 키워드 보정 분석: [keyword_adjustment_analysis.md](/C:/code/project1/doc/keyword_adjustment_analysis.md)
- 릴리즈 노트 초안: [release_notes_v0.1.0.md](/C:/code/project1/doc/release_notes_v0.1.0.md)
- 릴리즈 체크리스트: [release_checklist.md](/C:/code/project1/doc/release_checklist.md)

## 테스트

기본 검증 명령:

```powershell
python -m unittest discover -v
```

```powershell
python -m compileall app tests scripts
```

2026-04-21 기준 전체 테스트는 `67`개 통과 상태다.

## 다음 작업 후보

현재 가장 자연스러운 다음 단계는 아래 순서다.

1. 나라장터 collect adapter 구현
2. `all` 액션을 collect → export orchestration으로 완성
3. 운영 상태 파일과 observation report를 더 시각적으로 정리

## 요약

이 저장소는 “기획 단계 문서”를 넘어, 현재는 **기업마당 실제 API collect + SQLite 저장 + Excel export + observation + 운영자 실행 도구**까지 갖춘 내부 운영형 MVP 상태다.  
다만 나라장터와 `all` 액션은 아직 미완성이므로, README 기준 목표와 현재 구현 상태를 구분해서 운영하는 것이 중요하다.

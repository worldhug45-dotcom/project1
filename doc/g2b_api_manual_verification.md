# 나라장터 실제 API 수동 검증 절차

## 목적

이 문서는 나라장터 실제 API 응답이 현재 1차 MVP 흐름에 자연스럽게 연결되는지 수동으로 검증하는 절차를 정리한다.

검증 범위:

- `source_mode=api` collect 실행
- 실제 API 응답 파싱
- `G2BNoticeNormalizer`와 키워드 판정 연결
- `SQLiteNoticeRepository` 저장
- `CLI export`를 통한 실제 `.xlsx` 생성

## 사전 준비

PowerShell 기준으로 아래 환경 변수를 설정한다.

```powershell
$env:PROJECT1_G2B_API_KEY = "발급받은_서비스키"
```

실제 검증 데이터를 기존 로컬 데이터와 분리하려면 아래 환경 변수도 함께 설정한다.

```powershell
$env:PROJECT1_SOURCES_BIZINFO_ENABLED = "false"
$env:PROJECT1_SOURCES_G2B_ENABLED = "true"
$env:PROJECT1_STORAGE_DATABASE_PATH = "C:\code\project1\.test_tmp\g2b_api_manual\notices.sqlite3"
$env:PROJECT1_EXPORT_OUTPUT_DIR = "C:\code\project1\.test_tmp\g2b_api_manual\output"
```

## 1. 실제 API collect 실행

기본 collect 실행:

```powershell
python -m app.main --config config/settings.example.toml --action collect --source-mode api
```

원인 확인이 필요할 때만 진단 출력 포함:

```powershell
python -m app.main --config config/settings.example.toml --action collect --source-mode api --collect-diagnostics
```

실행 전 확인 포인트:

- `sources.g2b.enabled = true`
- `sources.bizinfo.enabled = false`
- `PROJECT1_G2B_API_KEY`가 현재 세션에 주입되어 있음
- `sources.g2b.inquiry_division = "1"` 또는 `"3"`
- `sources.g2b.inquiry_window_days`가 적절한 최근 조회 범위를 가지는지 확인

정상 기대 결과:

- `run_started` 로그 출력
- `source_finished` 로그 출력
- `run_summary` 출력
- `run_finished` 로그 출력
- `status = success`

실제 저장 성공 사례가 있는 경우 확인 포인트:

- `fetched_count > 0`
- `saved_count > 0`
- `skipped_count >= 0`
- 인증키가 로그에 출력되지 않음

## 2. SQLite 저장 확인

collect 성공 후 같은 DB 경로를 기준으로 export를 실행한다.

```powershell
python -m app.main --config config/settings.example.toml --action export
```

정상 기대 결과:

- `export_finished` 로그 출력
- `run_summary.exported_files`에 `.xlsx` 경로 포함
- `run_finished` 로그 출력

## 3. 산출물 확인

생성된 `.xlsx` 파일에서 아래를 확인한다.

- `support_notices` 시트 존재
- `bid_notices` 시트 존재
- `bid_notices`에 저장된 공고 행이 존재
- `support_notices`는 비어 있어도 헤더 행은 존재
- 컬럼 순서와 날짜/URL/match_keywords 포맷이 `doc/excel_export_format.md`와 일치

## 4. 실패 시 확인 순서

### 4-1. 설정/인증 실패

아래와 같은 경우는 설정 또는 인증 문제로 본다.

- `PROJECT1_G2B_API_KEY` 미설정
- HTTP `401` 또는 `403`
- 나라장터 응답 header에서 서비스키 오류 반환

우선 확인할 것:

- 현재 PowerShell 세션에 `PROJECT1_G2B_API_KEY`가 설정되어 있는지
- `sources.g2b.endpoint`가 올바른지
- `sources.bizinfo.enabled`가 `false`인지

### 4-2. 필수 조회조건 누락

나라장터 `getBidPblancListInfoServc`는 `inqryDiv`만 보내면 안 되고, 공식 참고문서 기준으로 아래 조건이 함께 필요하다.

- `inqryDiv = "1"` 또는 `"3"`일 때
  - `inqryBgnDt`
  - `inqryEndDt`
- `inqryDiv = "2"`일 때
  - `bidNtceNo`

현재 1차 MVP는 최근 공고 수집을 위해 `inqryDiv = "1"` 기준만 지원하며, `inqryBgnDt` / `inqryEndDt`는 현재 시각 기준 최근 `inquiry_window_days` 범위로 자동 계산한다.

### 4-3. 저장 성공이 0건일 때

아래 명령으로 진단 출력을 켠다.

```powershell
python -m app.main --config config/settings.example.toml --action collect --source-mode api --collect-diagnostics
```

확인 항목:

- `skip_reason`
  - `no_keyword_match`
  - `excluded_keyword`
  - `duplicate_notice`
  - `normalization_value_error`
  - `normalization_type_error`
- `matched_core_keywords`
- `matched_supporting_keywords`
- `matched_excluded_keywords`
- `business_domains`
- `primary_domain`
- `detail_message`

## 5. 현재 상태

2026-04-21 현재 이 저장소에서는 아래 상태까지 확인되었다.

- 나라장터 fixture 기반 collect 경로 구현 완료
- 나라장터 API mode CLI 연결 완료
- 나라장터 API mode collect -> SQLite -> export 경로를 mocking 테스트로 검증 완료
- 실제 서비스키가 user 환경 변수에 저장되면 process env로 승격해 live 검증 가능

## 6. 2026-04-21 live 검증 결과

다음 조건으로 실제 나라장터 API 검증을 수행했다.

- collect: `source_mode=api`
- 활성 소스: `g2b = true`, `bizinfo = false`
- 저장 경로: `C:\code\project1\.test_tmp\g2b_api_live\notices.sqlite3`
- 출력 경로: `C:\code\project1\.test_tmp\g2b_api_live\output`
- 조회 기준:
  - `inquiry_division = "1"`
  - `inquiry_window_days = 7`

확인 결과:

- 실제 API collect 성공
- `fetched_count = 20`
- `saved_count = 2`
- `skipped_count = 18`
- `error_count = 0`
- SQLite 저장 성공
- CLI export 성공
- 실제 `.xlsx` 파일 생성 성공
- `support_notices` 시트는 헤더만 생성
- `bid_notices` 시트는 헤더 + 데이터 2행 생성

저장된 대표 사례:

- `농촌공간 참여형 데이터 구축 모델 개발 및 실증 연구 용역`
  - `primary_domain = data`
- `2026년도 동해청 VTS 주요정보통신기반시설 보안 취약점 분석평가 용역`
  - `primary_domain = security`

추가 확인 사항:

- 나라장터 `getBidPblancListInfoServc`는 `inqryDiv = "1"`만 보내면 실패하고, 공식 참고문서 기준으로 `inqryBgnDt`, `inqryEndDt`가 함께 필요했다.
- 실제 오류 payload는 `response.header`뿐 아니라 top-level `nkoneps.com.response.ResponseError.header` 형식으로도 내려올 수 있었다.

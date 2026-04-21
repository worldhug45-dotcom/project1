# 기업마당 실제 API 수동 검증 절차

## 목적

이 문서는 기업마당 실제 API 응답이 현재 1차 MVP 흐름에 자연스럽게 연결되는지 수동으로 검증하는 절차를 정리한다.

검증 범위:

- `source_mode=api` collect 실행
- 실제 API 응답 파싱
- `BizinfoNoticeNormalizer`와 키워드 판정 연결
- `SQLiteNoticeRepository` 저장
- `CLI export`를 통한 실제 `.xlsx` 생성

## 사전 준비

PowerShell 기준으로 아래 환경 변수를 설정한다.

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
```

실제 검증 데이터를 기존 로컬 데이터와 분리하려면 아래 환경 변수도 함께 설정한다.

```powershell
$env:PROJECT1_STORAGE_DATABASE_PATH = "C:\code\project1\.test_tmp\bizinfo_api_manual\notices.sqlite3"
$env:PROJECT1_EXPORT_OUTPUT_DIR = "C:\code\project1\.test_tmp\bizinfo_api_manual\output"
$env:PROJECT1_SOURCES_G2B_ENABLED = "false"
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
- `support_notices`에 저장된 공고 행이 존재
- `bid_notices`는 비어 있어도 헤더 행은 존재
- 컬럼 순서와 날짜/URL/match_keywords 포맷이 `doc/excel_export_format.md`와 일치

## 4. 진단 출력 해석

`--collect-diagnostics`를 사용할 때는 notice 단위로 아래 정보를 확인할 수 있다.

- `outcome`
  - `saved`
  - `skipped`
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

이 출력은 실제 API 응답 기준으로 왜 저장되지 않았는지 빠르게 판단하기 위한 진단용 구조이며, 기본 실행에서는 옵션을 켠 경우에만 출력한다.

## 5. 2026-04-20 수동 검증 결과

다음 조건으로 수동 검증을 수행했다.

- collect: `source_mode=api`
- storage: `C:\code\project1\.test_tmp\bizinfo_api_manual_seq\notices.sqlite3`
- export output: `C:\code\project1\.test_tmp\bizinfo_api_manual_seq\output`
- g2b: 비활성화

확인 결과:

- 실제 API collect 성공
- `fetched_count = 20`
- `saved_count = 1`
- `skipped_count = 19`
- 저장된 SQLite 데이터를 기준으로 CLI export 성공
- `.xlsx` 파일 생성 성공
- SQLite 저장 건수 `1` 확인
- workbook 시트 확인
  - `support_notices`: 헤더 + 데이터 1행
  - `bid_notices`: 헤더만 존재

추가 관찰:

- 저장 성공 사례 1건은 키워드 기준으로 `infra`로 분류되었고, 종료일이 `사업별 상이` 형태여서 선택 날짜 필드를 `None`으로 처리한 뒤 저장되었다.
- 다수 공고는 `no_keyword_match` 또는 `excluded_keyword`로 skipped 되었다.

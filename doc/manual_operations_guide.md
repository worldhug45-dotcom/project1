# 수동 운영 가이드

이 문서는 내부 사용자가 코드 수정 없이 키워드를 조정하고, launcher 또는 `manual_run.py`로 `collect`, `export`, `observe`, `status`를 실행하며, 결과물 위치와 최근 상태를 바로 확인하기 위한 운영 가이드이다.

## 빠른 실행 명령 5개

1. 현재 상태 확인

```powershell
.\scripts\run_status.ps1
```

2. 실제 API collect

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

3. 실제 API collect + diagnostics

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1 -CollectDiagnostics
```

4. export

```powershell
.\scripts\run_export.ps1
```

5. observe

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_observe.ps1
```

## 1. launcher 스크립트

운영자가 직접 긴 명령을 외우지 않도록 PowerShell launcher를 제공한다.

- 상태 확인: `scripts/run_status.ps1`
- collect 실행: `scripts/run_collect.ps1`
- export 실행: `scripts/run_export.ps1`
- observe 실행: `scripts/run_observe.ps1`

기본 설정 파일은 모두 `config/settings.local.toml`을 사용한다.

다른 설정 파일을 쓰고 싶으면 `-Config` 인자를 붙인다.

```powershell
.\scripts\run_collect.ps1 -Config config/settings.local.toml -SourceMode fixture
```

PowerShell 실행 정책 때문에 막히면 아래처럼 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_status.ps1
```

## 2. status 확인

`status`는 운영자가 가장 먼저 보는 화면이다.

```powershell
.\scripts\run_status.ps1
```

최소 아래 정보를 한 번에 보여준다.

- 현재 `config_path`
- 현재 `keyword_override_path`
- 현재 `sqlite_db_path`
- 현재 `export_output_dir`
- 가장 최근 `latest_exported_file_path`
- 현재 `observation_history_path`
- 현재 `observation_report_path`
- 현재 `observation_raw_jsonl_dir`
- 최근 `collect` 결과 요약
- 최근 `export` 결과 요약
- 최근 `observe` 결과 요약

## 3. 키워드 조정 파일

기본 키워드 세트는 `config/settings.local.toml`에 있고, 사용자 추가/제거는 `config/keywords.override.toml`에서 처리한다.

- 실제 편집 파일: `config/keywords.override.toml`
- 예시 파일: `config/keywords.override.example.toml`
- 대체 경로 환경 변수: `PROJECT1_KEYWORDS_OVERRIDE_PATH`

구조:

```toml
[keywords_override]
add_core = []
add_supporting = []
add_exclude = []
remove_core = []
remove_supporting = []
remove_exclude = []
```

규칙:

- `add_*`: 기존 키워드 세트에 중복 없이 추가한다.
- `remove_*`: 기존 키워드 세트에서 제거한다.
- 대소문자 차이는 구분하지 않는다.

예시:

```toml
[keywords_override]
add_supporting = ["국방기술", "전자전"]
remove_exclude = ["문화"]
```

## 4. collect 실행

실제 API collect:

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

fixture collect:

```powershell
.\scripts\run_collect.ps1 -SourceMode fixture
```

diagnostics 포함:

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1 -CollectDiagnostics
```

collect 완료 후 바로 확인 가능한 정보:

- `fetched_count`
- `saved_count`
- `skipped_count`
- `error_count`
- `db_path`
- `export_output_dir`

## 5. export 실행

```powershell
.\scripts\run_export.ps1
```

export 완료 후 바로 확인 가능한 정보:

- `db_path`
- `export_output_dir`
- `exported_file_path`

## 6. observe 실행

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_observe.ps1
```

observe 완료 후 바로 확인 가능한 정보:

- `observation_history_path`
- `observation_report_path`
- `observation_raw_jsonl_dir`
- `observation_snapshot_db_dir`

기본 생성 위치:

- history: `data/observations/bizinfo/collect_observations.json`
- report: `doc/bizinfo_collect_observation_log.md`
- raw: `data/observations/bizinfo/raw/`
- snapshot DB: `data/observations/bizinfo/snapshots/`

## 7. manual_run.py 직접 사용

launcher 대신 직접 실행하고 싶으면 아래 형식을 사용한다.

```powershell
python scripts/manual_run.py <action> --config config/settings.local.toml
```

지원 action:

- `status`
- `collect`
- `export`
- `observe`

예시:

```powershell
python scripts/manual_run.py status --config config/settings.local.toml
python scripts/manual_run.py collect --config config/settings.local.toml --source-mode api
python scripts/manual_run.py export --config config/settings.local.toml
python scripts/manual_run.py observe --config config/settings.local.toml --source-mode api
```

## 8. 결과물 위치 요약

`settings.local.toml` 기준 기본 경로:

- collect DB: `data/observations/bizinfo/notices.sqlite3`
- export output dir: `output/observations/bizinfo/`
- observation report: `doc/bizinfo_collect_observation_log.md`
- state file: `data/operations/manual_run_state.json`

## 9. 실패 시 확인 순서

실패하면 `manual_run.py`가 터미널에 `next_checks:` 섹션을 함께 출력한다. 우선 아래 순서로 본다.

1. `config_path`와 TOML 문법
2. `PROJECT1_BIZINFO_CERT_KEY` 환경 변수 여부(api 모드인 경우)
3. `keyword_override_path`와 override 파일 문법
4. `db_path`, `export_output_dir`, observation 경로의 쓰기 권한
5. 직전 `error` 로그와 `run_summary` 상태

## 10. 운영 원칙

- 키워드 실험은 먼저 `config/keywords.override.toml`로만 진행한다.
- 기본 키워드 세트를 직접 수정하기 전에 2~3일 observation 근거를 먼저 쌓는다.
- `excluded_keyword` 완화는 저장 성공률보다 오탐 리스크 근거가 충분할 때만 검토한다.
- 실제 인증키는 환경 변수로만 주입하고 파일에 기록하지 않는다.

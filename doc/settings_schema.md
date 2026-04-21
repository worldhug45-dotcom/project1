# 설정 파일 구조 정의

## 1. 목적

이 문서는 1차 MVP 실행에 필요한 설정 구조를 정의한다.  
설정 구조를 먼저 고정해 외부 소스 어댑터, 키워드 판정, 저장, 엑셀 출력, 로그 구현이 하드코딩 없이 확장될 수 있게 한다.

## 2. 적용 범위

- 포함: 설정 섹션, 필드, 타입, 필수 여부, 기본값, override 우선순위, 검증 규칙
- 제외: 설정 로더 구현, 외부 API 호출 구현, DB 저장 구현, 엑셀 출력 구현

## 3. 설정 원칙

- 설정 파일 포맷은 `TOML`을 사용한다.
- 기본 설정 파일 경로는 `config/settings.toml`로 한다.
- 환경별 설정은 `config/settings.local.toml`, `config/settings.dev.toml`, `config/settings.prod.toml`처럼 분리할 수 있다.
- 비밀값은 설정 파일에 저장하지 않는다.
- API 키, 인증 토큰, 비밀번호는 환경 변수 또는 CI/CD secret으로만 주입한다.
- 필수 설정값은 실행 시작 시 검증한다.
- 잘못된 필수 설정은 경고 후 진행하지 않고 즉시 실패한다.

## 4. Override 우선순위

설정값은 아래 순서로 override한다.

1. CLI 인자
2. 환경 변수
3. 선택된 설정 파일
4. 애플리케이션 기본값

CLI 인자는 실행 액션, 환경명, 설정 파일 경로처럼 실행 시점에 바뀌는 값을 다룬다.  
환경 변수는 비밀값 또는 배포 환경에서 주입해야 하는 값을 다룬다.

## 5. 환경 변수 규칙

환경 변수 prefix는 `PROJECT1_`을 사용한다.

| 설정 경로 | 환경 변수 예시 |
| --- | --- |
| `app.env` | `PROJECT1_APP_ENV` |
| `sources.bizinfo.enabled` | `PROJECT1_SOURCES_BIZINFO_ENABLED` |
| `sources.bizinfo.endpoint` | `PROJECT1_SOURCES_BIZINFO_ENDPOINT` |
| `sources.bizinfo.fixture_path` | `PROJECT1_SOURCES_BIZINFO_FIXTURE_PATH` |
| `sources.g2b.fixture_path` | `PROJECT1_SOURCES_G2B_FIXTURE_PATH` |
| `sources.g2b.endpoint` | `PROJECT1_SOURCES_G2B_ENDPOINT` |
| `sources.g2b.inquiry_division` | `PROJECT1_SOURCES_G2B_INQUIRY_DIVISION` |
| `sources.g2b.inquiry_window_days` | `PROJECT1_SOURCES_G2B_INQUIRY_WINDOW_DAYS` |
| `storage.database_path` | `PROJECT1_STORAGE_DATABASE_PATH` |
| `export.output_dir` | `PROJECT1_EXPORT_OUTPUT_DIR` |
| `logging.level` | `PROJECT1_LOGGING_LEVEL` |
| `runtime.action` | `PROJECT1_RUNTIME_ACTION` |
| `runtime.source_mode` | `PROJECT1_RUNTIME_SOURCE_MODE` |

비밀값은 아래처럼 별도 환경 변수로만 관리한다.

| 비밀값 | 환경 변수 예시 |
| --- | --- |
| 기업마당 API 인증키 (`crtfcKey`) | `PROJECT1_BIZINFO_CERT_KEY` |
| 나라장터 API 키 | `PROJECT1_G2B_API_KEY` |

## 6. 설정 섹션

1차 MVP 설정은 아래 섹션으로 구성한다.

- `app`: 앱 이름, 환경, 타임존
- `sources`: 기업마당/나라장터 활성화 여부, 엔드포인트, 타임아웃, 재시도
- `keywords`: 핵심/보조/강제 제외 키워드
- `storage`: DB 종류, 경로
- `export`: 출력 폴더, 파일명 규칙, 시트명
- `logging`: 로그 레벨, 로그 경로, 포맷
- `runtime`: 실행 액션, 실행 모드, 실행 ID 생성 방식
- `validation`: 설정 검증 정책

## 7. app 섹션

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `name` | 선택 | `str` | `project1` | 애플리케이션 이름 |
| `env` | 선택 | `str` | `local` | 실행 환경. `local`, `dev`, `prod` 중 하나 |
| `timezone` | 선택 | `str` | `Asia/Seoul` | `collected_at`과 로그 기준 시간대 |

## 8. sources 섹션

### 8-1. 공통 필드

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `enabled` | 선택 | `bool` | 소스별 기본값 사용 | 해당 소스 활성화 여부 |
| `endpoint` | 필수 | `str` | 없음 | API 엔드포인트 |
| `fixture_path` | 조건부 필수 | `str` | 없음 | fixture 모드에서 사용할 샘플 응답 파일 경로 |
| `timeout_seconds` | 선택 | `int` | `10` | 단일 요청 타임아웃 |
| `retry_count` | 선택 | `int` | `3` | 재시도 횟수 |
| `retry_backoff_seconds` | 선택 | `int` | `2` | 재시도 간 기본 대기 시간 |
| `page_size` | 선택 | `int` | `20` | 1차 MVP 조회 기준 건수 |

### 8-2. 기업마당

| 설정 경로 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `sources.bizinfo.enabled` | 선택 | `bool` | `true` | 기업마당 수집 활성화 |
| `sources.bizinfo.endpoint` | 필수 | `str` | 없음 | 지원사업정보 API 엔드포인트 |
| `sources.bizinfo.fixture_path` | 조건부 필수 | `str` | 없음 | `runtime.source_mode = "fixture"`에서 사용할 기업마당 fixture 경로 |
| `sources.bizinfo.cert_key` | 환경 변수 전용 | `str` | 없음 | `runtime.source_mode = "api"`에서 `PROJECT1_BIZINFO_CERT_KEY`로만 주입하는 기업마당 인증키 |
| `sources.bizinfo.timeout_seconds` | 선택 | `int` | `10` | 요청 타임아웃 |
| `sources.bizinfo.retry_count` | 선택 | `int` | `3` | 재시도 횟수 |
| `sources.bizinfo.retry_backoff_seconds` | 선택 | `int` | `2` | 재시도 대기 시간 |
| `sources.bizinfo.page_size` | 선택 | `int` | `20` | 조회 건수 |

### 8-3. 나라장터

| 설정 경로 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `sources.g2b.enabled` | 선택 | `bool` | `true` | 나라장터 수집 활성화 |
| `sources.g2b.endpoint` | 필수 | `str` | 없음 | 입찰공고정보서비스 엔드포인트 |
| `sources.g2b.fixture_path` | 조건부 필수 | `str` | 없음 | `runtime.source_mode = "fixture"`에서 사용할 나라장터 fixture 경로 |
| `sources.g2b.cert_key` | 환경 변수 전용 | `str` | 없음 | `runtime.source_mode = "api"`에서 `PROJECT1_G2B_API_KEY`로만 주입하는 나라장터 서비스키 |
| `sources.g2b.timeout_seconds` | 선택 | `int` | `10` | 요청 타임아웃 |
| `sources.g2b.retry_count` | 선택 | `int` | `3` | 재시도 횟수 |
| `sources.g2b.retry_backoff_seconds` | 선택 | `int` | `2` | 재시도 대기 시간 |
| `sources.g2b.page_size` | 선택 | `int` | `20` | 조회 건수 |
| `sources.g2b.inquiry_division` | 선택 | `str` | `"1"` | 조회구분. 1차 MVP는 등록일시(`1`) 또는 변경일시(`3`)만 지원 |
| `sources.g2b.inquiry_window_days` | 선택 | `int` | `7` | `inqryDiv = "1"` 또는 `"3"`일 때 최근 조회 기간(일) |

`runtime.source_mode = "api"`일 때 활성화된 소스의 `endpoint`는 필수이다.  
기업마당 실제 API 모드에서는 `PROJECT1_BIZINFO_CERT_KEY`가 필수이며, 이 값은 설정 파일이 아니라 환경 변수에서만 읽는다.  
`runtime.source_mode = "fixture"`일 때 활성화된 소스는 각자의 `fixture_path`를 사용하며, 실제 외부 API endpoint 검증은 수행하지 않는다.  
비활성화된 소스의 `endpoint`는 검증 대상에서 제외할 수 있다.
나라장터 실제 API 모드에서는 `sources.g2b.inquiry_division = "1"`을 기본값으로 사용하며, 이 경우 `inqryBgnDt`와 `inqryEndDt`는 현재 시각 기준 최근 `inquiry_window_days` 범위로 자동 계산한다.

## 9. keywords 섹션

키워드는 설정 파일에서 관리하고 코드에 하드코딩하지 않는다.

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `core` | 필수 | `list[str]` | 없음 | 핵심 키워드 |
| `supporting` | 필수 | `list[str]` | 없음 | 보조 키워드 |
| `exclude` | 필수 | `list[str]` | 없음 | 강제 제외 키워드 |

초기 키워드 예시는 `config/settings.example.toml`에 제공하며, 기준은 `README.md`의 키워드 운영 기준을 따른다.
키워드 판정 규칙 자체는 별도 문서에서 확정한다.

## 10. storage 섹션

1차 MVP 기본 저장소는 `sqlite`로 한다.

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `type` | 선택 | `str` | `sqlite` | 저장소 종류 |
| `database_path` | 선택 | `str` | `data/notices.sqlite3` | SQLite DB 파일 경로 |

`storage.type`이 `sqlite`이면 `database_path`는 필수 검증 대상이다.  
디렉터리가 없으면 실행 시작 시 생성 가능하지만, 파일 생성 권한이 없으면 즉시 실패한다.

## 11. export 섹션

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `output_dir` | 선택 | `str` | `output` | 엑셀 산출물 출력 폴더 |
| `filename_pattern` | 선택 | `str` | `notices_{run_date}_{run_id}.xlsx` | 산출물 파일명 규칙 |
| `support_sheet_name` | 선택 | `str` | `support_notices` | 기업마당 지원사업 공고 시트명 |
| `bid_sheet_name` | 선택 | `str` | `bid_notices` | 나라장터 입찰공고 시트명 |
| `date_format` | 선택 | `str` | `%Y-%m-%d` | 엑셀 날짜 출력 형식 |

`filename_pattern`은 최소 `{run_date}`와 `{run_id}` 중 하나를 포함해야 한다.  
재실행 산출물이 서로 덮어쓰이지 않도록 `{run_id}` 포함을 권장한다.

## 12. logging 섹션

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `level` | 선택 | `str` | `INFO` | 로그 레벨 |
| `log_dir` | 선택 | `str` | `logs` | 로그 출력 폴더 |
| `format` | 선택 | `str` | `jsonl` | 로그 포맷. `jsonl`, `text` 중 하나 |
| `filename_pattern` | 선택 | `str` | `run_{run_date}.jsonl` | 로그 파일명 규칙 |

운영 로그 필수 항목은 별도 로그 구조 정의 단계에서 확정한다.  
이 문서에서는 로그 출력 위치와 기본 포맷만 정한다.

## 13. runtime 섹션

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `action` | 선택 | `str` | `all` | 실행 액션. `collect`, `export`, `all` 중 하나 |
| `mode` | 선택 | `str` | `normal` | 실행 모드. `normal`, `dry_run` 중 하나 |
| `source_mode` | 선택 | `str` | `api` | 소스 입력 모드. `api`, `fixture` 중 하나 |
| `run_id_strategy` | 선택 | `str` | `timestamp_uuid` | 실행 ID 생성 방식 |

`dry_run`은 저장이나 엑셀 파일 생성을 수행하지 않는 검증 모드로 예약한다.  
1차 구현에서 `dry_run`을 구현하지 않으면 CLI에서 선택할 수 없게 막는다.
`fixture` source mode는 외부 API 없이 샘플 응답으로 collect 흐름을 end-to-end 검증하기 위한 로컬 실행 모드이다.

## 14. validation 섹션

| 필드 | 필수 여부 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `fail_fast` | 선택 | `bool` | `true` | 필수 설정 누락 시 즉시 실패 여부 |
| `allow_unknown_keys` | 선택 | `bool` | `false` | 알 수 없는 설정 키 허용 여부 |
| `require_at_least_one_source` | 선택 | `bool` | `true` | 최소 1개 소스 활성화 필요 여부 |

## 15. 필수 설정값 목록

아래 값은 실행 시작 시 검증한다.

- `api` source mode에서 활성화된 소스의 `endpoint`
- `api` source mode에서 `sources.bizinfo.enabled = true`이면 `PROJECT1_BIZINFO_CERT_KEY`
- `api` source mode에서 `sources.g2b.enabled = true`이면 `PROJECT1_G2B_API_KEY`
- `fixture` source mode에서 활성화된 각 소스의 `fixture_path`
- `storage.type`
- `storage.database_path`
- `export.output_dir`
- `export.support_sheet_name`
- `export.bid_sheet_name`
- `logging.log_dir`
- `runtime.action`
- `app.timezone`

## 16. 검증 실패 기준

아래 조건은 치명적 설정 오류로 보고 실행 시작 전에 즉시 실패한다.

- `app.env`가 `local`, `dev`, `prod`가 아니다.
- `app.timezone`이 유효한 timezone 이름이 아니다.
- 활성화된 소스의 `endpoint`가 비어 있다.
- `runtime.source_mode`가 `api`인데 `PROJECT1_BIZINFO_CERT_KEY`가 비어 있다.
- `runtime.source_mode`가 `api`인데 `PROJECT1_G2B_API_KEY`가 비어 있다.
- `runtime.source_mode`가 `fixture`인데 활성화된 소스의 `fixture_path`가 비어 있거나 존재하지 않는다.
- `timeout_seconds`가 1보다 작다.
- `retry_count`가 0보다 작다.
- `page_size`가 1보다 작다.
- `sources.g2b.inquiry_window_days`가 0보다 작다.
- `sources.g2b.inquiry_division`이 1차 MVP에서 지원하지 않는 값이다.
- `keywords.core`, `keywords.supporting`, `keywords.exclude` 중 하나라도 비어 있다.
- `storage.type`이 지원하지 않는 값이다.
- `storage.database_path`가 비어 있다.
- `export.output_dir`이 비어 있다.
- `runtime.action`이 `collect`, `export`, `all`이 아니다.
- `runtime.source_mode`가 `api`, `fixture`가 아니다.
- `validation.require_at_least_one_source`가 `true`인데 활성화된 소스가 없다.

아래 조건은 경고로 기록하고 기본값을 사용할 수 있다.

- 선택 설정값이 누락되어 기본값으로 대체된다.
- 비활성화된 소스의 `endpoint`가 비어 있다.
- `logging.level`이 누락되어 `INFO`로 대체된다.

## 17. 설정 예시

```toml
[app]
name = "project1"
env = "local"
timezone = "Asia/Seoul"

[sources.bizinfo]
enabled = true
endpoint = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
fixture_path = "tests/fixtures/bizinfo/support_notices.json"
timeout_seconds = 10
retry_count = 3
retry_backoff_seconds = 2
page_size = 20

[sources.g2b]
enabled = false
endpoint = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc"
fixture_path = "tests/fixtures/g2b/bid_notices.json"
timeout_seconds = 10
retry_count = 3
retry_backoff_seconds = 2
page_size = 20

[keywords]
core = ["AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"]
supporting = ["데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "사물인터넷", "IoT", "보안", "ICT", "SW", "소프트웨어", "IT서비스", "유지보수"]
exclude = ["채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"]

[storage]
type = "sqlite"
database_path = "data/notices.sqlite3"

[export]
output_dir = "output"
filename_pattern = "notices_{run_date}_{run_id}.xlsx"
support_sheet_name = "support_notices"
bid_sheet_name = "bid_notices"
date_format = "%Y-%m-%d"

[logging]
level = "INFO"
log_dir = "logs"
format = "jsonl"
filename_pattern = "run_{run_date}.jsonl"

[runtime]
action = "all"
mode = "normal"
source_mode = "api"
run_id_strategy = "timestamp_uuid"

[validation]
fail_fast = true
allow_unknown_keys = false
require_at_least_one_source = true
```

## 18. 1차 확정 사항

- 설정 파일 포맷은 `TOML`로 한다.
- 기본 설정 파일 경로는 `config/settings.toml`로 한다.
- override 우선순위는 `CLI 인자 > 환경 변수 > 설정 파일 > 기본값`으로 한다.
- 비밀값은 설정 파일에 저장하지 않고 환경 변수 또는 CI/CD secret으로 주입한다.
- 기업마당 인증키는 `PROJECT1_BIZINFO_CERT_KEY` 환경 변수로만 주입한다.
- 필수 설정 오류는 실행 시작 시 즉시 실패한다.
- 1차 MVP 기본 저장소는 `sqlite`로 한다.
- 기본 엑셀 출력 폴더는 `output`으로 한다.
- 기본 로그 출력 폴더는 `logs`로 한다.
- 기본 소스 입력 모드는 `api`로 하며, CLI/테스트 검증용으로 `fixture` 모드를 지원한다.

## 19. 남은 결정 사항

- 기업마당 API 추가 검색 필터 (`searchLclasId`, `hashtags`) 사용 여부
- 실제 나라장터 API endpoint 값
- `dry_run` 구현 여부
- 설정 로더 구현 방식

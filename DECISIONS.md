# DECISIONS

이 문서는 구현 중 확정한 규칙을 기록하는 Decision Log이다.  
코드 변경 전에 기준이 바뀌면 이 문서를 먼저 갱신한다.

## 기록 형식

```text
## YYYY-MM-DD - 결정 제목

- Status: Proposed | Accepted | Superseded
- Context:
- Decision:
- Consequences:
```

## 2026-04-16 - 1차 MVP 범위 고정

- Status: Accepted
- Context: `README.md`와 승인 요청안 기준으로 1차 MVP 범위를 명확히 제한해야 한다.
- Decision: 1차 MVP는 기업마당 공고 조회, 나라장터 공고 조회, 키워드 기반 적격 판정, 공통 필드 정규화, DB 저장, 엑셀 산출물 생성, 로그 생성으로 한정한다.
- Consequences: NTIS, K-Startup, AI 요약, Word 출력, 알림 연동, 검색 UI, 우선순위 자동 점수화는 별도 변경요청으로 분리한다.

## 2026-04-16 - 구현 순서 원칙

- Status: Accepted
- Context: 외부 연동부터 구현하면 데이터 모델, 중복 기준, 로그 기준이 뒤늦게 흔들릴 수 있다.
- Decision: 외부 API 연동보다 프로젝트 구조, 공통 데이터 모델, 설정 구조, 중복 판단 키, 키워드 판정 규칙, 로그 필수 항목을 먼저 고정한다.
- Consequences: 첫 구현 작업은 내부 구조와 인터페이스 정의에 집중한다.

## 2026-04-16 - 계층 방향

- Status: Accepted
- Context: README는 책임 분리와 Ports and Adapters 방식을 권장한다.
- Decision: 계층은 `Presentation`, `Application`, `Domain`, `Infrastructure`로 구분하고, 외부 소스 연동은 어댑터로 분리한다.
- Consequences: 새 소스 추가는 기존 핵심 로직 수정이 아니라 새 어댑터 추가 방식으로 처리한다.

## 2026-04-16 - 아키텍처 기준 정렬

- Status: Accepted
- Context: `README.md`는 `source`, `filter`, `normalize`, `persistence`, `export`, `ops` 역할 기반 구조를 제시하고, 구현 결정 문서는 계층 기반 구조를 사용하고 있어 구현 시 혼선 가능성이 있다.
- Decision: 상위 아키텍처는 `Presentation`, `Application`, `Domain`, `Infrastructure` 계층을 따르며, 하위 구현 모듈은 `sources`, `filters`, `normalizers`, `persistence`, `exporters`, `ops` 역할 기준으로 구성할 수 있다.
- Consequences: 계층 책임과 물리적 폴더 구조를 동시에 관리할 수 있으며, 바이브코딩 중 구조 흔들림을 줄인다.

## 2026-04-16 - 판정과 정규화 책임 위치

- Status: Accepted
- Context: 키워드 판정과 도메인 분류는 비즈니스 규칙이고, 원천 응답을 공통 모델로 변환하는 작업은 외부 데이터 형식에 영향을 받는다.
- Decision: 키워드 판정 규칙과 `business_domains`, `primary_domain` 분류 규칙은 `Domain` 계층에 둔다. 원천 응답 DTO를 공통 `Notice` 모델로 변환하는 정규화는 `Infrastructure` 또는 `Application` 경계에서 수행하고, 전체 흐름 orchestration은 `Application` 계층이 담당한다.
- Consequences: 비즈니스 규칙은 Domain에 고정하고, 외부 API 응답 형식 변화는 바깥 계층에서 흡수한다.

## 2026-04-16 - fixture 우선 검증

- Status: Accepted
- Context: 기업마당과 나라장터의 응답 형식이 다르므로 실제 API부터 연결하면 내부 구조가 API 상태에 끌려갈 수 있다.
- Decision: 외부 API 연동 전에 각 소스의 샘플 응답 fixture를 확보하고, DTO 파싱과 정규화 테스트를 fixture 기반으로 먼저 작성한다.
- Consequences: 외부 API 장애나 응답 변동과 내부 구조 설계를 분리할 수 있으며, API 없이도 핵심 정규화 로직을 검증할 수 있다.

## 2026-04-16 - 공통 데이터 모델 정의

- Status: Accepted
- Context: 기업마당과 나라장터 공고를 같은 흐름에서 판정, 저장, 산출하려면 내부 공통 모델이 필요하다.
- Decision: 내부 공통 모델은 `Notice`로 정의하고, 중복 판단은 `DeduplicationKey`로 수행한다. `Notice`는 `source`, `notice_type`, `business_domains`, `primary_domain`, `title`, `organization`, `status`, `url`, `match_keywords`, `collected_at`을 필수 값으로 가진다. `posted_at`, `end_at`, `source_notice_id`, `raw_source_name`, `summary`는 선택 값으로 둔다.
- Consequences: 기업마당과 나라장터 원천 응답은 모두 `Notice`로 정규화해야 하며, 엑셀 필수 컬럼은 `Notice`에서 산출한다.

## 2026-04-16 - 설정 파일 구조 정의

- Status: Accepted
- Context: 소스 어댑터, 키워드 판정, 저장, 엑셀 출력, 로그 구현이 하드코딩에 의존하지 않으려면 설정 구조와 override 규칙을 먼저 고정해야 한다.
- Decision: 설정 파일 포맷은 `TOML`로 하고 기본 경로는 `config/settings.toml`로 한다. 설정 섹션은 `app`, `sources`, `keywords`, `storage`, `export`, `logging`, `runtime`, `validation`으로 구성한다. Override 우선순위는 `CLI 인자 > 환경 변수 > 설정 파일 > 기본값`으로 한다. 비밀값은 설정 파일에 저장하지 않고 환경 변수 또는 CI/CD secret으로만 주입한다.
- Consequences: 키워드, 활성 소스, 타임아웃, 재시도, 출력 경로, 시트명, 로그 경로는 코드에 하드코딩하지 않고 설정에서 읽어야 한다.

## 2026-04-16 - 키워드 판정 규칙 정의

- Status: Accepted
- Context: `Notice.business_domains`, `Notice.primary_domain`, `Notice.match_keywords`를 일관되게 생성하려면 매칭 대상, 전처리, 우선순위, 도메인 매핑, 적격 판정 기준을 먼저 고정해야 한다.
- Decision: 키워드 매칭 대상은 `title`, `organization`, `summary`, `raw_source_name`으로 한정하고 URL과 날짜 값은 제외한다. 전처리는 `NFKC`, 공백 정규화, 영문 casefold를 적용한다. 강제 제외 키워드는 핵심/보조 키워드보다 우선하며, 핵심 또는 보조 키워드가 1개 이상 매칭되고 제외 키워드가 없으면 적격으로 판정할 수 있다. `primary_domain`은 핵심 여부, 도메인 우선순위, 필드 우선순위, 최초 출현 순서로 선정한다.
- Consequences: 키워드 판정은 Domain 계층의 비즈니스 규칙으로 유지되며, 정규화 결과는 이 규칙에 따라 `business_domains`, `primary_domain`, `match_keywords`를 생성해야 한다.

## 2026-04-16 - 코드 구현 착수 승인

- Status: Accepted
- Context: 공통 데이터 모델, 설정 스키마, 키워드 판정 규칙 등 0단계 핵심 기준이 문서로 확정되었다.
- Decision: 지금부터 1차 MVP 코드 구현을 시작한다. 구현 범위는 `README.md`에 정의된 1차 범위로 한정한다.
- Consequences: 첫 구현 우선순위는 프로젝트 골격, 공통 데이터 모델 코드 반영, 설정 로더/검증 구조, CLI 진입점 정의 순으로 진행한다.

## 2026-04-16 - 로그와 예외 처리 기준 정의

- Status: Accepted
- Context: collect, 저장, export 흐름이 추가되기 전에 실행 단위와 오류 단위를 공통으로 기록하고 분류할 기준이 필요하다.
- Decision: 로그 이벤트는 `run_id`, `event_type`, `action`, `status`를 공통 필수 값으로 가진다. 오류 유형은 `retryable`, `non_fatal`, `fatal`, `configuration`으로 구분한다. CLI 흐름은 실행 시작, 실행 종료, 오류 이벤트를 공통 구조로 기록할 수 있어야 한다.
- Consequences: 이후 소스 수집, 저장, 엑셀 산출 흐름은 같은 로그 이벤트 모델과 예외 분류 구조를 사용해야 한다.

## 2026-04-17 - Application 계층 계약 정의

- Status: Accepted
- Context: 기업마당/나라장터 어댑터, 저장소, 엑셀 익스포터를 구현하기 전에 Application 계층이 사용할 공통 Port와 실행 결과 모델을 고정해야 한다.
- Decision: Application 계층에는 `CollectNoticesUseCase`, `ExportNoticesUseCase`, `NoticeSourcePort`, `NoticeNormalizerPort`, `NoticeRepositoryPort`, `ExcelExporterPort`, `LogSinkPort`, `RunSummary`, `SourceRunSummary` 계약을 둔다. Use Case와 Port는 구현이 아니라 계약으로 정의하며, Application 계층은 orchestration 책임만 가진다.
- Consequences: 이후 Infrastructure 어댑터는 이 Port를 구현하고, collect/export/all 액션은 같은 `RunSummary` 모델을 공유한다. Domain 비즈니스 규칙과 외부 연동 세부 구현은 Application 계층으로 들어오지 않는다.

## 2026-04-17 - 기업마당 fixture 기반 소스 초안

- Status: Accepted
- Context: 첫 실제 수집 소스로 기업마당을 연결하되, 외부 API 상태에 의존하지 않고 파싱과 정규화 흐름을 먼저 검증해야 한다.
- Decision: 기업마당 원천 응답 DTO는 `BizinfoNoticeRaw`로 정의하고, fixture 위치는 `tests/fixtures/bizinfo/support_notices.json`으로 한다. `BizinfoFixtureSourceAdapter`는 `NoticeSourcePort` 계약에 맞춰 fixture를 반환하고, `BizinfoNoticeNormalizer`는 `BizinfoNoticeRaw`를 내부 `Notice`로 변환한다.
- Consequences: 기업마당 파싱과 정규화는 외부 API 없이 테스트 가능하며, 이후 HTTP client 기반 실제 adapter를 같은 Port 위에 붙일 수 있다.

## 2026-04-17 - 기업마당 fixture 기반 collect Use Case 초안

- Status: Accepted
- Context: 기업마당 fixture adapter와 normalizer가 준비되었으므로, 실제 DB 없이도 collect orchestration과 `RunSummary` 집계를 검증할 수 있어야 한다.
- Decision: `DefaultCollectNoticesUseCase`는 `NoticeSourcePort`, `NoticeNormalizerPort`, `NoticeRepositoryPort`를 주입받아 `source adapter -> raw DTO -> normalizer -> repository 저장 -> RunSummary 생성` 순서로 실행한다. 저장소는 초기 검증용 `InMemoryNoticeRepository`를 사용한다.
- Consequences: 적격 공고는 저장되고 부적격 공고는 `skipped_count`로 집계된다. 이후 실제 저장소와 나라장터 소스는 같은 Port 계약 위에 추가할 수 있다.

## 2026-04-17 - CLI collect fixture 모드 연결

- Status: Accepted
- Context: 현재 단계에서는 실제 외부 API 호출과 실제 DB 저장 없이 기업마당 1개 소스의 collect 흐름을 CLI에서 end-to-end로 검증해야 한다.
- Decision: CLI는 `runtime.source_mode = "fixture"` 또는 `--source-mode fixture`일 때만 기업마당 fixture collect를 실행한다. 실행 시 `BizinfoFixtureSourceAdapter`, `BizinfoNoticeNormalizer`, 설정의 저장소 구현, `DefaultCollectNoticesUseCase`를 조립하고, 결과는 `source_finished` 로그와 `run_summary` JSON 출력으로 확인한다.
- Consequences: CLI collect는 외부 API 없이 적격 저장, 부적격 skip, `RunSummary` 집계를 검증할 수 있다. 실제 API 모드와 나라장터 확장은 이후 같은 Port 구조 위에서 별도 작업으로 추가한다.

## 2026-04-17 - SQLite 저장소 초안

- Status: Accepted
- Context: fixture 기반 collect 흐름이 준비되었으므로, 운영 저장소 확장 전 최소 SQLite 저장소로 중복 저장 방지와 이후 export 조회 가능성을 검증해야 한다.
- Decision: `SQLiteNoticeRepository`는 Infrastructure 계층의 `NoticeRepositoryPort` 구현체로 둔다. 저장 스키마는 `Notice` 필드와 `DeduplicationKey`를 기준으로 구성하고, 중복 방지는 `source`, `dedup_key_type`, `dedup_key_value`의 `UNIQUE` 제약으로 보장한다. 테이블 생성은 복잡한 마이그레이션 없이 repository 초기화 시 `CREATE TABLE IF NOT EXISTS`로 수행한다.
- Consequences: 기업마당 fixture collect 결과를 SQLite에 저장할 수 있고, 동일 fixture 재실행 시 중복 저장되지 않는다. `InMemoryNoticeRepository`는 빠른 단위 테스트용 대안으로 유지한다.

## 2026-04-17 - 저장 실패 치명적 오류 처리

- Status: Accepted
- Context: 저장 실패는 데이터 유실과 재실행 안전성 훼손으로 이어질 수 있으므로 부적격 공고 제외나 일부 정규화 실패처럼 계속 진행하면 안 된다.
- Decision: 저장소 write 실패는 `StorageWriteError` 또는 `fatal` 오류로 분류한다. Collect Use Case는 저장 실패가 발생하면 즉시 실행을 중단하고 `RunSummary.status=failed`, `SourceRunSummary.error_count=1`, `ErrorInfo.error_type=fatal`을 반환한다. CLI는 실패 요약을 기준으로 `source_finished`, `error`, `run_summary`, `run_finished`를 모두 `failed` 상태로 남긴다.
- Consequences: 저장 실패는 `partial_success`가 아니라 `failed`로 고정된다. 이후 export 실패와 source 전체 실패 처리도 같은 패턴으로 `RunSummary`와 로그를 일관되게 연결한다.

## 2026-04-17 - 저장소 조회 계약 확정

- Status: Accepted
- Context: 엑셀 export Use Case가 SQLite에 저장된 `Notice`를 읽으려면 저장소 구현체별 보조 메서드가 아니라 Application Port의 정식 조회 계약이 필요하다.
- Decision: `NoticeRepositoryPort`에 `list_all() -> tuple[Notice, ...]` 조회 계약을 추가한다. 조회 결과는 export 준비를 위해 결정적인 순서를 가져야 하며, `InMemoryNoticeRepository`는 삽입 순서, `SQLiteNoticeRepository`는 `id ASC` 순서로 반환한다.
- Consequences: export Use Case는 저장소 구현체를 알지 않고 `NoticeRepositoryPort.list_all()`만 사용해 엑셀 산출 대상 공고를 읽을 수 있다. 기존 `all()` 보조 메서드는 호환용 alias로 유지한다.

## 2026-04-17 - Export Use Case 초안

- Status: Accepted
- Context: 실제 엑셀 파일 생성 전에 저장소 조회 결과를 시트 입력 구조로 분리하고, exporter Port로 전달하는 Application orchestration을 검증해야 한다.
- Decision: `DefaultExportNoticesUseCase`는 `NoticeRepositoryPort.list_all()`로 저장된 공고를 조회하고, `notice_type` 기준으로 `support_notices`, `bid_notices` 입력을 구성한 뒤 `ExcelExporterPort`에 전달한다. 이 단계에서는 실제 파일 생성 대신 `FakeExcelExporter`로 workbook 입력 구조와 `RunSummary.exported_files`를 검증한다.
- Consequences: export Use Case는 저장소 구현체와 엑셀 생성 구현을 알지 않고 동작한다. 실제 Excel exporter는 같은 `ExportWorkbookInput` 계약 위에 추가할 수 있다.

## 2026-04-17 - 엑셀 출력 포맷 기준

- Status: Accepted
- Context: 실제 Excel exporter 구현 전에 컬럼 순서, 표시 형식, 파일명 규칙을 고정하지 않으면 fake exporter 테스트와 실제 파일 생성 구현 사이에 기준 차이가 생길 수 있다.
- Decision: 엑셀 출력 포맷 기준은 `doc/excel_export_format.md`와 `app.exporters.formatting`으로 고정한다. 필수 컬럼 순서는 `source`, `notice_type`, `primary_domain`, `title`, `organization`, `posted_at`, `end_at`, `status`, `url`, `match_keywords`, `collected_at`이다. 날짜는 `YYYY-MM-DD`, 파일명 날짜는 `YYYYMMDD`, `match_keywords`는 키워드만 `, `로 연결한다. `business_domains`는 내부 저장용으로 유지하고 엑셀에는 출력하지 않는다.
- Consequences: 실제 Excel exporter는 파일 생성 라이브러리를 도입하더라도 동일한 포맷터와 테스트 기준을 따라야 한다. 빈 `bid_notices` 시트는 허용하되 실제 파일 생성 시 헤더는 생성해야 한다.

## 2026-04-16 - 공통 데이터 전달 기준

- Status: Accepted
- Context: 기업마당과 나라장터의 원천 데이터 구조가 다르므로 내부 처리 기준이 필요하다.
- Decision: 내부 계층 간 데이터 전달은 공통 `Notice` 모델을 기준으로 한다.
- Consequences: 원천 API DTO는 Infrastructure 계층에 머물고, Application/Domain 계층은 `Notice` 모델을 사용한다.

## 2026-04-16 - 산출물 시트 기준

- Status: Accepted
- Context: README에서 엑셀 산출물의 최소 시트 구성을 명시했다.
- Decision: 엑셀 산출물은 최소 `support_notices`, `bid_notices` 2개 시트로 구성한다.
- Consequences: 기업마당 지원사업 공고는 `support_notices`, 나라장터 입찰공고는 `bid_notices`에 출력한다.

## 2026-04-17 - 실제 XLSX exporter 구현

- Status: Accepted
- Context: fake exporter로 export 입력 구조와 포맷 기준을 검증했으므로, 같은 Port 계약 위에서 실제 `.xlsx` 파일 생성 구현이 필요하다.
- Decision: 실제 Excel exporter는 `app.exporters.XlsxExcelExporter`로 구현한다. 이 구현체는 `ExcelExporterPort` 계약을 따르고, `app.exporters.formatting`의 컬럼 순서와 표시 규칙을 그대로 사용하며, 표준 `.xlsx` 패키지 구조를 표준 라이브러리로 생성한다. `support_notices`와 `bid_notices` 시트는 항상 생성하고, 빈 시트도 헤더 행을 포함한다. URL 컬럼은 표시 문자열과 동일한 외부 hyperlink 관계를 가진다.
- Consequences: Application 계층은 fake exporter와 실제 exporter를 같은 Port로 교체할 수 있다. 실제 Excel 라이브러리 의존성 없이 MVP 파일 생성 테스트가 가능하며, 별도 서식/자동 필터/열 너비 조정은 1차 MVP 범위 밖으로 둔다.

## 2026-04-17 - CLI export 실제 XLSX 생성 연결

- Status: Accepted
- Context: SQLite 저장소와 실제 XLSX exporter가 준비되었으므로, 저장된 `Notice`를 CLI export 액션으로 바로 파일 산출할 수 있어야 한다.
- Decision: CLI `export` 액션은 `SQLiteNoticeRepository`로 저장된 공고를 조회하고, `DefaultExportNoticesUseCase`에 `XlsxExcelExporter`를 주입해 실제 `.xlsx` 파일을 생성한다. 출력 경로와 파일명 규칙, 시트명은 기존 `settings.export` 구조를 따른다. 성공 시 `export_finished` 로그에 출력 파일 경로를 기록하고, `RunSummary.exported_files`를 `run_summary` JSON으로 출력한다.
- Consequences: fixture collect로 저장된 SQLite 데이터와 이후 실제 API collect 결과는 같은 export 경로를 사용할 수 있다. fake exporter는 Use Case 단위 테스트용 대안으로 유지한다.

## 2026-04-17 - 기업마당 실제 API collect 연결

- Status: Accepted
- Context: fixture 기반 기업마당 collect 흐름이 안정화되었으므로, 동일한 DTO/normalizer/repository 경로 위에 실제 API 모드를 연결해야 한다.
- Decision: 기업마당 실제 API endpoint는 `https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do`를 사용한다. 인증키는 `crtfcKey` 파라미터로 전달하고, 값은 설정 파일이 아니라 `PROJECT1_BIZINFO_CERT_KEY` 환경 변수에서만 읽는다. `source_mode=api`일 때 CLI collect는 `BizinfoApiHttpClient -> BizinfoSourceAdapter -> BizinfoNoticeNormalizer -> DefaultCollectNoticesUseCase -> SQLiteNoticeRepository` 순서로 동작한다. 실제 API JSON은 `jsonArray.item` 응답 형태를 `BizinfoNoticeRaw`로 파싱하고, `reqstBeginEndDe` 신청기간은 종료일로 정규화한다.
- Consequences: fixture 모드는 그대로 유지되며, 실제 API collect도 기존 Domain 규칙과 저장 흐름을 재사용한다. 인증키 누락은 설정 오류로, 잘못된 인증키나 API 오류 payload는 명확한 collect 실패로 처리한다. 로그와 오류 메시지에는 인증키 원문을 남기지 않는다.

## 미확정 결정 목록

- 테스트 도구와 커버리지 기준
- 실제 나라장터 API endpoint 값
- 기업마당 API 추가 검색 필터 (`searchLclasId`, `hashtags`) 사용 여부

## 2026-04-20 - 기업마당 선택 날짜 필드 정규화 완화

- Status: Accepted
- Context: 기업마당 실제 API 응답에는 `reqstEndDe` 또는 `reqstBeginEndDe`에 `사업별 상이` 같은 자유 형식 문자열이 포함될 수 있다. `Notice.posted_at`와 `Notice.end_at`는 공통 데이터 모델에서 선택 값이며, 이 값 때문에 적격 공고 전체가 저장되지 않는 것은 1차 MVP 목적과 맞지 않는다.
- Decision: 기업마당 정규화 단계에서는 `posted_at`, `end_at`처럼 선택 날짜 필드가 지원 형식이 아니면 예외로 수집을 중단하지 않고 `None`으로 정규화한다.
- Consequences: 실제 API collect가 `BizinfoNoticeNormalizer -> SQLiteNoticeRepository -> CLI export` 경로까지 안정적으로 이어질 수 있다. 날짜 필드가 비어 있는 공고도 저장 및 엑셀 산출이 가능하며, 키워드 판정 실패 원인 점검용 진단 출력은 별도로 유지한다.

## 2026-04-20 - 실제 API 기준 키워드 세트 보정

- Status: Accepted
- Context: 기업마당 실제 API diagnostics에서 `no_keyword_match` 비중이 높았고, 상위 100건 시뮬레이션 기준 기존 키워드 세트로는 기술 범위와 가까운 `IoT`, `ICT`, `SW` 계열 공고 일부를 놓치고 있었다.
- Decision: 기본 키워드 세트는 핵심 키워드를 유지하고, 보조 키워드에 `사물인터넷`, `IoT`, `ICT`, `SW`, `소프트웨어`를 추가한다. 도메인 매핑은 `사물인터넷`/`IoT`를 `infra`, `ICT`/`SW`/`소프트웨어`를 `si`로 둔다. 강제 제외 키워드는 이번 라운드에서 변경하지 않는다.
- Consequences: 실제 API 상위 20건 기준 저장 성공 사례를 늘릴 수 있고, 상위 100건 시뮬레이션에서도 적격 판정 건수가 증가한다. 반면 잡음 가능성이 높은 `플랫폼`, `IP`, `로봇`, `반도체` 같은 후보는 보류하여 범위 확장을 통제한다.
- 설정 파일에서 도메인 매핑을 표현하는 구체적 구조
- 로그 파일 실제 기록 방식
- 필수 필드 파싱 실패율 계산 방식

## 2026-04-20 - 운영 관찰은 local 설정과 diagnostics 누적으로 관리

- Status: Accepted
- Context: 실제 API 기준 키워드 보정은 하루 결과만으로 다시 확장하면 과적합될 위험이 있다. 같은 조건으로 2~3일간 collect 결과를 비교하려면 운영용 설정, 진단 출력, 관찰 기록 형식이 고정되어 있어야 한다.
- Decision: 실제 운영 관찰은 `config/settings.local.toml`을 기준 설정으로 사용하고, `sources.g2b.enabled = false`, `runtime.source_mode = api` 조건에서 기업마당만 반복 수집한다. 반복 실행은 `scripts/observe_bizinfo_collect.py`로 수행하며, 이 스크립트는 diagnostics 출력 기반으로 `fetched_count`, `saved_count`, `skipped_count`, `skip_reason` 분포, 저장/제외 대표 사례를 로컬 history와 Markdown 관찰 로그로 누적한다.
- Consequences: 예시 설정 파일과 운영 관찰 설정이 분리되어 기준이 흔들리지 않는다. day 2, day 3도 같은 명령으로 같은 형식의 기록을 남길 수 있고, 다음 키워드 보정 라운드는 누적된 `no_keyword_match`, `excluded_keyword`, `normalization_value_error` 분포를 근거로 진행한다.

## 2026-04-21 - 내부 사용자는 키워드 override 파일과 manual runner를 사용

- Status: Accepted
- Context: 내부 사용자가 키워드를 자주 실험하고 `collect`, `export`, `observation`을 수동으로 반복 실행해야 하는데, 매번 설정 파일 전체를 직접 이해하거나 결과물 경로를 다시 추적하면 운영 마찰이 커진다.
- Decision: 사용자 조정용 키워드는 `config/keywords.override.toml`에서 관리하고, 설정 로더는 이 파일을 `config/settings.local.toml`보다 우선 적용하되 환경 변수와 CLI override보다는 낮은 우선순위로 적용한다. 수동 실행은 `scripts/manual_run.py`를 기준 진입점으로 사용하고, 실행 후 설정 파일, 키워드 override 파일, DB 경로, export 경로, observation 경로를 즉시 출력한다.
- Consequences: 코드 수정 없이 키워드 추가/제거가 가능해지고, 운영자는 collect/export/observation을 한 파일에서 일관되게 실행할 수 있다. 결과물 위치를 터미널에서 바로 확인할 수 있어 운영 가이드와 실제 흐름이 일치한다.

## 2026-04-21 - 운영자는 launcher와 status 액션으로 현재 상태를 확인한다

- Status: Accepted
- Context: 내부 운영자가 `collect`, `export`, `observe`를 반복 실행하는 단계에서는 명령어 자체를 외우는 비용보다, 현재 경로와 가장 최근 실행 결과를 즉시 확인하는 편의성이 더 중요하다.
- Decision: 운영자용 PowerShell launcher를 `scripts/run_collect.ps1`, `scripts/run_export.ps1`, `scripts/run_observe.ps1`, `scripts/run_status.ps1`로 제공한다. `scripts/manual_run.py`에는 `status` 액션을 추가해 현재 설정 경로, 키워드 override 경로, SQLite DB 경로, export output 경로, 최신 `.xlsx` 파일, observation history/report/raw 경로와 최근 collect/export/observe 결과 요약을 함께 출력한다. 최근 상태는 `data/operations/manual_run_state.json`에 저장한다.
- Consequences: 운영자는 launcher만 실행해도 주요 작업을 시작할 수 있고, `status` 한 번으로 결과물 위치와 최근 실행 상태를 빠르게 파악할 수 있다. 기존 collect/export/observe 본 흐름은 유지하면서 운영형 솔루션에 가까운 사용성을 제공한다.

## 2026-04-21 - 웹 운영자 대시보드는 CLI 엔진을 재사용하는 얇은 레이어로 시작한다

- Status: Accepted
- Context: 현재 내부 운영형 솔루션은 CLI와 launcher 중심으로 안정화되었고, 다음 단계에서는 내부 사용자가 브라우저 한 화면에서 상태와 결과물 경로를 확인하고 `collect`, `export`, `observe`를 실행할 수 있어야 한다. 그러나 collect/export 엔진을 웹에서 다시 구현하면 중복과 회귀 위험이 커진다.
- Decision: 웹 운영자 대시보드 MVP는 단일 화면 중심의 `Presentation` 레이어로 추가하고, 기존 Python 엔진은 그대로 유지한다. 웹 액션은 `scripts/manual_run.py` 또는 그에 상응하는 공용 orchestration 서비스를 subprocess/gateway 형태로 호출하며, 상태 조회는 `manual_run_state.json`, 최신 `.xlsx`, observation history/report/raw 경로를 조합해 표시한다. Docker Compose 배포는 단일 `operator-web` 컨테이너와 `config`, `data`, `output`, `doc` 볼륨 구조를 기준으로 설계한다.
- Consequences: 웹 MVP는 빠르게 붙일 수 있고, CLI와 웹이 같은 실행 경로를 재사용하므로 운영 일관성이 높아진다. 반면 현재 observation report가 `doc/`에 생성되므로 Docker에서는 `doc` 볼륨이 필요하며, 장기적으로는 generated artifact 경로를 `output` 계열로 재정리할 여지가 남는다.

## 2026-04-21 - 나라장터 1차 수집은 용역 입찰공고 중심으로 fixture 우선 구현한다

- Status: Accepted
- Context: 나라장터는 입찰공고정보서비스 내부에서도 물품, 공사, 용역 등 세부 endpoint가 갈라져 있고, 1차 MVP의 AI/인프라/SI 범위에는 용역 공고가 가장 직접적으로 맞닿아 있다. 현재 collect orchestration은 단일 source 실행 기준이므로, 먼저 fixture와 parser/normalizer를 안정화한 뒤 실제 API skeleton을 잇는 편이 안전하다.
- Decision: 나라장터 1차 수집은 `getBidPblancListInfoServc` 계열 용역 입찰공고 endpoint를 기준으로 구현한다. Infrastructure 계층에는 `G2BNoticeRaw`, parser, `G2BFixtureSourceAdapter`, `G2BApiHttpClient`, `G2BSourceAdapter`, `G2BNoticeNormalizer`를 추가하고, 서비스키는 `PROJECT1_G2B_API_KEY` 환경 변수로만 주입한다. collect는 현재 단계에서 한 번에 하나의 enabled source만 실행하도록 두고, `sources.bizinfo` 또는 `sources.g2b` 중 하나를 선택해 기존 repository/export 흐름을 재사용한다.
- Consequences: 나라장터 fixture 데이터를 `Notice`로 정규화하고 SQLite 저장과 export 흐름에 연결할 준비가 갖춰진다. 반면 bizinfo와 g2b 동시 collect orchestration은 이후 단계의 확장 작업으로 남는다.
## 2026-04-21 - 웹 운영자 대시보드 1단계는 읽기 전용 status shell로 시작한다

- Status: Accepted
- Context: 현재 내부 운영형 솔루션은 CLI와 `manual_run.py`를 기준으로 상태 요약과 결과물 경로를 안정적으로 제공하고 있다. 웹 대시보드를 붙이되, 실행 버튼까지 한 번에 넣기보다 현재 상태 조회를 먼저 웹으로 노출하는 편이 구조적으로 안전하다.
- Decision: 웹 1단계는 `app.presentation.web`에 읽기 전용 대시보드 shell을 추가하고 `GET /`와 `GET /api/status`만 제공한다. status 조합 로직은 `app.ops.operator_status`로 추출해 CLI와 웹이 동일한 상태 스냅샷을 공유한다.
- Consequences: 기존 CLI/manual runner 흐름은 그대로 유지되고, 웹은 Presentation 계층에서 상태 조회만 담당한다. 다음 단계에서는 동일한 상태 모델 위에 collect/export/observe 버튼과 action endpoint를 추가할 수 있다.

## 2026-04-21 - 웹 운영자 대시보드 2단계는 collect 단일 실행 제어만 추가한다

- Status: Accepted
- Context: 웹 1단계 read-only shell이 안정화되었고, 다음 단계에서는 운영자가 브라우저에서 최소 한 가지 실행 작업을 직접 시작할 수 있어야 한다. 하지만 collect/export/observe를 한 번에 모두 붙이면 범위가 커지고, 기존 CLI 흐름과의 회귀 위험도 함께 커진다.
- Decision: 웹 2단계에서는 `collect`만 단일 action으로 추가한다. `POST /actions/collect`는 새 수집 엔진을 만들지 않고 기존 `manual_run.py collect` 경로를 subprocess gateway로 재사용한다. 웹 프로세스 내부에는 중복 실행을 막는 최소 collect control service만 두고, 상태 표시는 `idle`, `running`, `finished`, `failed`로 제한한다.
- Consequences: 웹은 orchestration만 담당하고 collect 본 로직은 기존 CLI 경로를 그대로 재사용한다. collect 실행 결과는 대시보드 내부의 별도 요약 영역에만 표시되며, 이후 export/observe도 같은 패턴의 gateway + control service로 확장할 수 있다.

## 2026-04-21 - 웹 운영자 대시보드 3단계는 export 단일 실행 제어만 추가한다

- Status: Accepted
- Context: collect 웹 제어가 안정화되었고, 다음으로 운영자가 결과물을 브라우저에서 바로 생성할 수 있어야 한다. 하지만 observe까지 한 번에 붙이면 상태 모델과 UI 범위가 다시 커지므로 export만 같은 패턴으로 추가하는 편이 안전하다.
- Decision: 웹 3단계에서는 `export`만 단일 action으로 추가한다. `POST /actions/export`는 새 export 엔진을 만들지 않고 기존 `manual_run.py export` 경로를 subprocess gateway로 재사용한다. 웹 프로세스 내부에는 중복 실행을 막는 최소 export control service만 두고, 상태 표시는 `idle`, `running`, `finished`, `failed`로 제한한다.
- Consequences: export 결과는 대시보드 내부의 별도 요약 영역에만 표시되고, collect 제어 영역과 직접 섞이지 않는다. 이후 observe도 같은 gateway + control service 패턴으로 확장할 수 있으며, 현재 단계에서는 collect/export 간 교차 실행 제어는 도입하지 않는다.

## 2026-04-21 - 웹 운영자 대시보드 4단계는 observe 단일 실행 제어만 추가한다

- Status: Accepted
- Context: collect/export 웹 제어가 안정화되었고, 다음 단계에서는 운영자가 관찰용 스냅샷 기록도 브라우저에서 직접 시작할 수 있어야 한다. observe는 결과 경로와 요약 항목이 collect/export와 다르므로 별도 제어 영역으로 분리하는 편이 안전하다.
- Decision: 웹 4단계에서는 `observe`만 단일 action으로 추가한다. `POST /actions/observe`는 새 observe 엔진을 만들지 않고 기존 `manual_run.py observe` 경로를 subprocess gateway로 재사용한다. 웹 프로세스 내부에는 중복 실행을 막는 최소 observe control service만 두고, 상태 표시는 `idle`, `running`, `finished`, `failed`로 제한한다.
- Consequences: observe 결과는 대시보드 내부의 별도 요약 영역에만 표시되고 collect/export 제어와 직접 섞이지 않는다. 웹은 orchestration만 담당하고 observation 생성 로직은 기존 CLI 경로를 그대로 재사용한다.

## 2026-04-21 - 웹 운영자 대시보드 5단계는 읽기 전용 health endpoint를 표준 상태 점검 기준으로 둔다

- Status: Accepted
- Context: 웹 대시보드와 Docker 배포를 운영하려면 서버 생존 여부와 최소 운영 상태를 가볍게 확인할 수 있는 공통 health endpoint가 필요하다.
- Decision: `GET /health`는 collect/export/observe를 실행하지 않는 읽기 전용 endpoint로 두고, `status`, `app_name`, `server_time`, `config_path`, `sqlite_db_path`, `export_output_dir`를 기본으로 반환한다. 추가로 `settings_loaded`, `state_file_accessible`, `observation_history_exists`를 포함해 `ok`, `degraded`, `error` 상태를 구분한다.
- Consequences: 웹 대시보드와 Docker healthcheck가 같은 health contract를 재사용할 수 있다. 일부 상태 파일이나 관찰 기록이 없어도 서버 전체를 죽이지 않고 `degraded`로 판정할 수 있다.

## 2026-04-21 - Docker 로컬 스타터는 단일 웹 컨테이너와 override 기반 api 모드로 유지한다

- Status: Accepted
- Context: 내부 운영자는 로컬에서도 웹 대시보드를 표준 방식으로 실행할 수 있어야 하고, fixture 모드와 실제 API 모드를 설정만 바꿔 전환할 수 있어야 한다.
- Decision: Docker 배포는 기본 `compose.yaml`의 단일 `operator-web` 컨테이너로 시작하고, `config`, `data`, `output`, `doc`를 볼륨으로 연결한다. 실제 API 모드는 별도 이미지 분기 없이 `compose.api.yaml` override와 환경 변수 주입으로 전환한다. healthcheck는 `GET /health`를 그대로 사용한다.
- Consequences: 로컬 스타터와 실제 API 모드가 같은 웹 서버와 같은 상태/실행 경로를 재사용한다. API 키는 이미지나 저장소가 아니라 환경 변수로만 주입되며, 운영 배포 보강은 이후 단계에서 Nginx나 worker 분리로 확장할 수 있다.

## 2026-04-21 - 웹 운영자 대시보드 6단계는 Health Badge로 /health를 직접 보여준다

- Status: Accepted
- Context: 운영자는 대시보드에 들어오자마자 현재 서버 상태를 한눈에 확인할 수 있어야 한다. 경로와 최근 상태 정보만으로는 설정 로드 실패나 state file 접근 문제를 빠르게 구분하기 어렵다.
- Decision: 대시보드 상단에 Health Badge를 추가하고, 프런트엔드는 `GET /health`를 별도로 읽어 `ok`, `degraded`, `error` 상태를 시각적으로 표시한다. Badge 옆에는 `app_name`, `server_time`, `settings_loaded`, `state_file_accessible`, `observation_history_exists`만 최소 요약으로 표시한다.
- Consequences: 운영자는 collect/export/observe를 실행하기 전에 서버 상태를 즉시 판단할 수 있다. `/health`는 읽기 전용으로 유지되고, 실행 제어 로직과 직접 결합되지 않는다.

## 2026-04-21 - 웹 운영자 대시보드 7단계는 키워드 snapshot을 읽기 전용으로 먼저 노출한다

- Status: Accepted
- Context: 내부 사용자는 현재 어떤 키워드 세트가 적용되고 있는지 먼저 확인할 수 있어야 하며, 바로 편집 기능부터 붙이면 override 우선순위와 로드 경로를 이해하기 어려워질 수 있다.
- Decision: 키워드 관리는 먼저 읽기 전용 `GET /api/keywords` endpoint와 Keyword Panel로 노출한다. 이 endpoint는 기존 settings loader와 override 구조를 재사용해 `core`, `supporting`, `exclude`, override 경로, override 파일 존재 여부, 마지막 로드 경로, 적용 키워드 개수를 반환한다.
- Consequences: 웹 대시보드는 collect/export/observe/status/health와 같은 화면에서 현재 유효 키워드 세트를 설명할 수 있다. 이후 편집 기능을 붙여도 기존 settings/override 우선순위 구조를 그대로 유지할 수 있다.

## 2026-04-21 - 웹 운영자 대시보드 8단계는 supporting 키워드만 override 파일에 저장 가능하게 한다

- Status: Superseded
- Context: 내부 운영자는 웹에서 가장 자주 조정하는 키워드 집합을 최소 범위로 편집할 수 있어야 하지만, 핵심 키워드와 제외 키워드까지 한 번에 열면 범위와 위험이 커진다.
- Decision: 웹 8단계에서는 supporting 키워드만 편집 가능하게 두고, `POST /api/keywords/supporting`이 기존 `keywords.override.toml` 구조를 유지한 채 `add_supporting` / `remove_supporting`만 다시 계산해 저장한다. `core`, `exclude`는 계속 읽기 전용으로 두고, 중복/빈 문자열/공백-only 입력은 저장하지 않는다.
- Consequences: 운영자는 코드 수정 없이 supporting 키워드를 웹에서 추가/삭제하고 즉시 저장할 수 있었다. 이후 동일한 저장 패턴을 검증한 뒤 exclude, core 편집으로 확장했다.

## 2026-04-22 - 웹 키워드 편집 범위를 core, supporting, exclude 전체로 확장한다

- Status: Accepted
- Context: supporting-only 저장 패턴이 안정화되었고, 내부 운영자가 실제 관찰 결과에 맞춰 core와 exclude도 코드 수정 없이 조정할 필요가 생겼다.
- Decision: 웹 대시보드는 `POST /api/keywords/core`, `POST /api/keywords/supporting`, `POST /api/keywords/exclude` 세 endpoint를 통해 각 키워드 그룹만 독립적으로 저장한다. 각 endpoint는 기존 `keywords.override.toml` 구조를 유지한 채 자기 그룹만 갱신하고, 중복/빈 문자열/공백-only 입력은 저장하지 않는다.
- Consequences: 운영자는 세 키워드 그룹을 모두 웹에서 관리할 수 있고, 그룹별 저장 범위가 분리되어 변경 영향도 추적이 쉬워진다. bulk edit, import/export, rollback은 계속 범위 밖으로 둔다.

## 2026-04-22 - 키워드 저장 메타는 sidecar 파일로 유지한다

- Status: Accepted
- Context: 운영자가 마지막 저장 시각, 저장 대상 파일, 최근 변경 그룹, 성공/실패 상태를 새로고침 후에도 바로 확인할 수 있어야 한다.
- Decision: 키워드 본문은 기존 `keywords.override.toml`에 유지하고, 저장 메타는 인접한 `keywords.override.meta.json` sidecar 파일에 기록한다. `/api/keywords`는 `save_meta`를 함께 반환해 `saved_at`, `target_path`, `changed_group`, `status`, 필요 시 `error_message`를 노출한다.
- Consequences: override TOML schema를 바꾸지 않고도 운영 UX용 메타데이터를 안정적으로 제공할 수 있다. 저장 실패도 메타로 남겨 새로고침 이후 같은 진단 정보를 확인할 수 있다.

## 2026-04-22 - 최소 품질 게이트는 ruff와 mypy로 연결한다

- Status: Accepted
- Context: 현재 코드베이스는 기능 범위가 넓어졌지만 format, lint, type check 실행 기준이 문서와 관행에만 머물러 있었다. 기존 CLI, 웹, 테스트 흐름을 건드리지 않으면서도 로컬에서 반복 가능한 최소 품질 게이트가 필요했다.
- Decision: format과 lint는 `ruff`로, type check는 `mypy`로 연결한다. `ruff`는 `app`, `tests`, `scripts`를 대상으로 실행하고, `mypy`는 현재 단계에서 노이즈를 줄이기 위해 `app` 계층만 검사한다. 일괄 실행 진입점은 `scripts/run_quality.ps1`로 제공한다.
- Consequences: 개발자는 `.\scripts\run_quality.ps1` 한 번으로 format / lint / type check를 순서대로 확인할 수 있다. 테스트 코드와 운영 스크립트는 formatter와 lint 대상에는 포함되지만, type check 범위는 우선 `app`에 한정해 최소 기준을 안정적으로 유지한다.

## 2026-04-22 - GitHub Actions 1단계는 로컬 품질 게이트를 그대로 재사용한다

- Status: Accepted
- Context: 로컬에서 `ruff format --check`, `ruff check`, `mypy`, `unittest`, `compileall`이 통과 중이므로, 같은 기준을 CI에 옮겨야 push와 pull request 단계에서 회귀를 빠르게 잡을 수 있다.
- Decision: GitHub Actions는 단일 workflow로 시작하고, `push`와 `pull_request`마다 Python 3.13 환경에서 `requirements-dev.txt`를 설치한 뒤 `ruff format --check`, `ruff check`, `mypy`, `python -m unittest discover -v`, `python -m compileall app tests scripts`를 순서대로 실행한다. 각 검사는 별도 step으로 분리해 실패 지점을 로그에서 바로 구분할 수 있게 한다.
- Consequences: 로컬과 CI의 품질 게이트 기준이 크게 어긋나지 않게 유지된다. 향후 mypy 범위 확장이나 릴리즈 자동화도 같은 workflow 기반 위에서 단계적으로 확장할 수 있다.
## 2026-04-23 - 설정 화면 source 저장은 단일 enabled source 제약을 따른다

- Status: Accepted
- Context: 현재 collect 엔진은 기업마당과 나라장터를 동시에 실행하는 multi-source orchestration을 아직 지원하지 않는다. 설정 화면에서 두 source를 동시에 enabled로 저장할 수 있으면 UI 저장 상태와 collect 실행 규칙이 충돌할 수 있다.
- Decision: 설정 화면 3단계에서는 `POST /api/settings/sources`가 기업마당/나라장터 enabled 상태와 `runtime.source_mode`만 저장한다. 저장 대상은 기존 `settings.override.toml`이며, `source_mode`는 `api` 또는 `fixture`만 허용한다. 기본 source는 정확히 하나만 enabled로 저장할 수 있게 하고, 모두 disabled 또는 둘 다 enabled인 경우 사용자 친화적인 설정 오류로 거부한다.
- Consequences: 운영자는 웹에서 source 활성 상태와 source mode를 안전하게 변경할 수 있다. collect 핵심 엔진은 수정하지 않고 UI 저장 규칙을 현재 실행 제약에 맞췄으며, 향후 multi-source orchestration을 구현할 때 이 제약을 별도 결정으로 완화할 수 있다.

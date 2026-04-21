# 엑셀 출력 포맷 기준

## 1. 목적

이 문서는 1차 MVP 엑셀 산출물의 시트, 컬럼, 표시 형식, 파일명 규칙을 정의한다.  
실제 Excel exporter 구현 전에 포맷 기준을 문서와 테스트로 고정해, fake exporter와 실제 exporter 사이의 기준 차이를 줄인다.

## 2. 적용 범위

- 포함: 시트명, 필수 컬럼 순서, 날짜 표시, URL 표시, `match_keywords` 표시, 빈 시트 허용, 파일명 규칙
- 제외: 실제 Excel 파일 생성 라이브러리 도입, 셀 스타일, 컬럼 너비 자동 조정, 실제 파일 저장 구현

## 3. 시트 기준

1차 MVP 엑셀 산출물은 아래 2개 시트를 가진다.

| 시트명 | 대상 공고 |
| --- | --- |
| `support_notices` | 기업마당 지원사업 공고, `notice_type = support` |
| `bid_notices` | 나라장터 입찰공고, `notice_type = bid` |

현재 기업마당 fixture 기준으로는 `support_notices`에 데이터가 있고 `bid_notices`는 비어 있을 수 있다.  
빈 시트는 허용하며, 실제 Excel exporter 구현 시 빈 시트에도 헤더는 생성해야 한다.

## 4. 필수 컬럼 순서

두 시트는 동일한 컬럼 순서를 사용한다.

| 순서 | 컬럼명 | 값 기준 |
| --- | --- | --- |
| 1 | `source` | `Notice.source.value` |
| 2 | `notice_type` | `Notice.notice_type.value` |
| 3 | `primary_domain` | `Notice.primary_domain.value` |
| 4 | `title` | `Notice.title` |
| 5 | `organization` | `Notice.organization` |
| 6 | `posted_at` | `YYYY-MM-DD` 또는 빈 문자열 |
| 7 | `end_at` | `YYYY-MM-DD` 또는 빈 문자열 |
| 8 | `status` | `Notice.status.value` |
| 9 | `url` | 클릭 가능한 URL 문자열 |
| 10 | `match_keywords` | 매칭 키워드 문자열 |
| 11 | `collected_at` | `YYYY-MM-DD` |

`business_domains`는 내부 저장 및 분류용 값으로 유지하고, 엑셀에는 출력하지 않는다.  
엑셀 보고용 대표 도메인은 `primary_domain`만 출력한다.

## 5. 날짜 표시 기준

- `posted_at`, `end_at`은 값이 있으면 `YYYY-MM-DD`로 표시한다.
- `posted_at`, `end_at`이 `None`이면 빈 문자열로 표시한다.
- `collected_at`은 timezone-aware `datetime`의 날짜 부분을 `YYYY-MM-DD`로 표시한다.
- 날짜/시간 전체 timestamp 출력은 1차 MVP 엑셀 기준에 포함하지 않는다.

## 6. URL 표시 기준

- 엑셀 행 데이터에는 `Notice.url` 원문 URL 문자열을 출력한다.
- 실제 Excel exporter 구현 시 해당 URL 문자열은 같은 URL을 대상으로 하는 hyperlink로 설정해야 한다.
- URL 표시 텍스트와 hyperlink target은 동일하게 둔다.

## 7. match_keywords 표시 기준

`match_keywords`는 `MatchedKeyword.keyword` 값만 출력한다.

표시 규칙:

- 저장된 매칭 순서를 유지한다.
- 중복 키워드는 최초 1회만 표시한다.
- 구분자는 쉼표와 공백 `, `을 사용한다.
- `group`, `domain`은 엑셀 표시값에 포함하지 않는다.

예시:

```text
AI, 데이터
```

## 8. 파일명 규칙

기본 파일명 패턴은 아래와 같다.

```text
notices_{run_date}_{run_id}.xlsx
```

규칙:

- `{run_date}`는 `YYYYMMDD` 형식이다.
- `{run_id}`는 실행 ID를 그대로 사용한다.
- 파일 확장자는 `.xlsx`여야 한다.
- 파일명 패턴은 `{run_date}` 또는 `{run_id}` 중 하나 이상을 포함해야 한다.
- 기본 출력 폴더는 `settings.export.output_dir`을 따른다.

예시:

```text
notices_20260417_run-1.xlsx
```

## 9. 테스트 기준

실제 Excel exporter 구현 전에는 `app.exporters.formatting`의 순수 포맷 규칙을 테스트 기준으로 삼는다.

검증 항목:

- 컬럼 순서가 고정되어 있다.
- `business_domains`는 행 출력에서 제외된다.
- `primary_domain`은 출력된다.
- 날짜는 `YYYY-MM-DD` 또는 빈 문자열이다.
- URL은 원문 문자열로 출력된다.
- `match_keywords`는 키워드만 `, `로 연결된다.
- 빈 시트 입력은 허용된다.
- 파일명은 기본 패턴과 확장자 규칙을 따른다.

## 10. 1차 확정 사항

- 시트명은 `support_notices`, `bid_notices`로 한다.
- 두 시트는 동일한 필수 컬럼 순서를 사용한다.
- `business_domains`는 엑셀에 출력하지 않고 `primary_domain`만 출력한다.
- 빈 `bid_notices` 시트는 허용한다.
- 실제 exporter는 이 문서와 `app.exporters.formatting` 테스트를 기준으로 구현한다.

## 11. 실제 exporter 구현 기준

2026-04-17 기준 실제 `.xlsx` 생성은 `app.exporters.XlsxExcelExporter`가 담당한다.

- 실제 exporter는 `ExcelExporterPort` 계약을 구현한다.
- 실제 exporter는 `app.exporters.formatting`의 컬럼 순서와 표시 형식을 그대로 사용한다.
- `support_notices`, `bid_notices` 시트는 항상 생성한다.
- 데이터가 없는 시트도 헤더 행은 생성한다.
- `url` 컬럼은 표시 문자열과 동일한 값을 대상으로 하는 Excel hyperlink 관계를 가진다.
- 파일명은 `settings.export.filename_pattern`과 동일한 기본 규칙인 `notices_{run_date}_{run_id}.xlsx`를 따른다.
- 실제 exporter는 표준 `.xlsx` 패키지 구조를 생성하며, 1차 MVP에서는 별도 서식, 자동 필터, 열 너비 자동 조정은 범위 밖으로 둔다.

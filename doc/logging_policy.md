# 로그 구조 정의

## 1. 목적

이 문서는 1차 MVP 운영 로그의 필수 항목과 이벤트 구조를 정의한다.  
로그는 반복 실행, 장애 추적, 수동 재실행 판단을 지원하기 위한 운영 기준 데이터이다.

## 2. 적용 범위

- 포함: 실행 시작/종료, 실행 ID, 실행 액션, 실행 결과 상태, 소스별 건수, 오류 유형, 출력 파일 경로
- 제외: 실제 외부 API 호출 로그, DB 저장 로그, 엑셀 파일 생성 구현

## 3. 기본 원칙

- 로그는 `ops` 계층의 공통 운영 모델로 정의한다.
- 모든 로그 이벤트는 `run_id`를 포함한다.
- 실행 단위 로그와 소스 단위 로그를 구분한다.
- 오류 로그는 예외 처리 정책의 오류 유형을 함께 기록한다.
- 1차 MVP의 기본 로그 포맷은 `jsonl`이다.
- 로그 파일 경로와 포맷은 `settings_schema.md`의 `logging` 섹션을 따른다.

## 4. 필수 로그 항목

| 항목 | 필수 여부 | 설명 |
| --- | --- | --- |
| `timestamp` | 필수 | 로그 이벤트 생성 시각 |
| `run_id` | 필수 | 한 번의 실행을 식별하는 ID |
| `event_type` | 필수 | `run_started`, `run_finished`, `source_finished`, `error` 등 |
| `action` | 필수 | `collect`, `export`, `all` 중 하나 |
| `status` | 필수 | `running`, `success`, `partial_success`, `failed` 중 하나 |
| `source` | 선택 | `bizinfo`, `g2b` 등 소스명 |
| `fetched_count` | 선택 | 조회 건수 |
| `saved_count` | 선택 | 저장 건수 |
| `excluded_count` | 선택 | 제외 건수 |
| `error_type` | 선택 | `retryable`, `non_fatal`, `fatal`, `configuration` 중 하나 |
| `error_message` | 선택 | 오류 메시지 |
| `output_file_path` | 선택 | 엑셀 산출물 경로 |
| `metadata` | 선택 | 추가 진단 정보 |

## 5. 이벤트 유형

| event_type | 발생 시점 | 주요 필드 |
| --- | --- | --- |
| `run_started` | CLI 실행 시작 | `run_id`, `action`, `status` |
| `run_finished` | CLI 실행 종료 | `run_id`, `action`, `status`, `output_file_path` |
| `source_started` | 특정 소스 수집 시작 | `run_id`, `action`, `source`, `status` |
| `source_finished` | 특정 소스 수집 종료 | `run_id`, `action`, `source`, `fetched_count`, `saved_count`, `excluded_count`, `status` |
| `export_finished` | 엑셀 산출 종료 | `run_id`, `action`, `output_file_path`, `status` |
| `error` | 오류 발생 | `run_id`, `action`, `error_type`, `error_message`, `status` |

## 6. 실행 결과 상태

| status | 의미 |
| --- | --- |
| `running` | 실행 중 |
| `success` | 전체 성공 |
| `partial_success` | 비치명적 오류가 있었지만 전체 실행은 완료 |
| `failed` | 치명적 오류 또는 설정 오류로 실패 |

## 7. 실행 ID 규칙

기본 실행 ID 생성 방식은 `timestamp_uuid`이다.

형식:

```text
YYYYMMDDTHHMMSSffffffZ_8자리UUID
```

예시:

```text
20260416T081530123456Z_a1b2c3d4
```

실행 ID는 로그, 산출물 파일명, 장애 추적에 공통으로 사용한다.

## 8. 소스별 건수 기준

| 필드 | 의미 |
| --- | --- |
| `fetched_count` | 원천 소스에서 조회한 건수 |
| `saved_count` | 적격 판정 후 저장한 건수 |
| `excluded_count` | 강제 제외, 부적격, 필수 필드 누락 등으로 제외한 건수 |

아직 실제 수집/저장 로직이 없는 단계에서는 값이 없을 수 있다.  
수집 흐름 구현 후에는 `source_finished` 이벤트에 세 건수를 모두 기록한다.

## 9. 출력 파일 경로 기준

엑셀 산출물이 생성된 경우 `output_file_path`에 최종 파일 경로를 기록한다.  
엑셀 산출물이 생성되지 않는 `collect` 액션에서는 비워둘 수 있다.

## 10. 1차 확정 사항

- 기본 로그 포맷은 `jsonl`이다.
- 모든 로그 이벤트는 `run_id`, `event_type`, `action`, `status`를 가진다.
- 실행 시작/종료 이벤트는 CLI 흐름에서 공통으로 남긴다.
- 오류 이벤트는 예외 처리 정책의 오류 유형을 함께 기록한다.
- 소스별 조회/저장/제외 건수는 수집 흐름 구현 시 `source_finished` 이벤트에 기록한다.

## 11. 남은 결정 사항

- 로그 파일 실제 기록 방식
- 로그 rotation 정책
- 외부 API 공지성 장애의 상세 metadata 형식


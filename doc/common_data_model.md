# 공통 데이터 모델 정의

## 1. 목적

이 문서는 기업마당 지원사업 공고와 나라장터 입찰공고를 내부에서 동일하게 처리하기 위한 공통 데이터 모델을 정의한다.  
외부 API 응답 형식은 소스마다 다르지만, `Application`과 `Domain` 계층은 이 문서의 `Notice` 모델을 기준으로 동작한다.

## 2. 적용 범위

이번 문서는 1차 MVP의 공통 데이터 모델만 다룬다.

- 포함: `Notice` 필드, 필수/선택 기준, enum 값, 날짜 기준, URL 기준, 중복 판단 키
- 제외: 외부 API 호출 구현, DB 저장 구현, 엑셀 출력 구현, 실제 코드 모델 생성

## 3. 모델 원칙

- 내부 계층 간 데이터 전달은 `Notice` 모델을 기준으로 한다.
- 원천 API DTO는 `Infrastructure` 계층에 머문다.
- 원천 응답을 `Notice`로 변환하는 정규화는 `Infrastructure` 또는 `Application` 경계에서 수행한다.
- 키워드 판정과 도메인 분류 규칙은 `Domain` 계층의 비즈니스 규칙으로 둔다.
- 엑셀 필수 컬럼은 `Notice`에서 산출 가능해야 한다.
- 동일한 공고를 여러 번 수집해도 같은 `DeduplicationKey`가 생성되어야 한다.

## 4. Notice 필드 정의

| 필드명 | 필수 여부 | 타입 기준 | 설명 |
| --- | --- | --- | --- |
| `source` | 필수 | `NoticeSource` | 공고 출처. 1차 MVP에서는 `bizinfo`, `g2b`를 사용한다. |
| `source_notice_id` | 선택 | `str` | 원천 시스템의 공고 식별자. 제공되지 않으면 URL 또는 복합 키로 중복 판단한다. |
| `notice_type` | 필수 | `NoticeType` | 공고 유형. 기업마당은 기본 `support`, 나라장터는 기본 `bid`이다. |
| `business_domains` | 필수 | `list[BusinessDomain]` | 매칭된 사업 도메인 목록. 다중 선택을 허용한다. |
| `primary_domain` | 필수 | `BusinessDomain` | 보고용 대표 도메인 1개. `business_domains` 중 하나여야 한다. |
| `title` | 필수 | `str` | 공고명. 중복 판단 fallback에도 사용한다. |
| `organization` | 필수 | `str` | 공고 기관 또는 발주 기관. |
| `posted_at` | 선택 | `date` | 게시일. 알 수 없으면 `None`으로 둔다. 엑셀 출력 시 빈 값으로 변환한다. |
| `end_at` | 선택 | `date` | 접수 마감일 또는 입찰 마감일. 알 수 없으면 `None`으로 둔다. |
| `status` | 필수 | `NoticeStatus` | 공고 상태. 원천 상태를 공통 상태로 변환한다. |
| `url` | 필수 | `str` | 상세 공고 URL. 클릭 가능한 `http` 또는 `https` URL이어야 한다. |
| `match_keywords` | 필수 | `list[MatchedKeyword]` | 적격 판정에 사용된 매칭 키워드 목록. |
| `collected_at` | 필수 | timezone-aware `datetime` | 수집 시각. 기본 시간대는 `Asia/Seoul`이다. |
| `raw_source_name` | 선택 | `str` | 원천 시스템에 표시된 출처명 또는 세부 서비스명. |
| `summary` | 선택 | `str` | 원천에서 제공하는 요약 또는 설명. AI 요약은 1차 MVP 범위가 아니므로 포함하지 않는다. |

## 5. 필수 값과 필수 컬럼의 구분

엑셀 필수 컬럼은 항상 생성되어야 한다.  
다만 원천 API에서 일부 날짜를 제공하지 않는 경우가 있으므로 `posted_at`, `end_at`은 모델에서 선택 값으로 둔다.

- 필수 값: `source`, `notice_type`, `business_domains`, `primary_domain`, `title`, `organization`, `status`, `url`, `match_keywords`, `collected_at`
- 선택 값: `source_notice_id`, `posted_at`, `end_at`, `raw_source_name`, `summary`
- 필수 컬럼: `README.md`의 산출물 기준에 명시된 모든 컬럼

## 6. Enum 기준

### 6-1. NoticeSource

| 값 | 의미 |
| --- | --- |
| `bizinfo` | 기업마당 지원사업정보 API |
| `g2b` | 나라장터 입찰공고정보서비스 |

### 6-2. NoticeType

| 값 | 의미 | 1차 MVP 사용 여부 |
| --- | --- | --- |
| `support` | 지원사업 공고 | 사용 |
| `bid` | 입찰공고 | 사용 |
| `rnd` | R&D 공고 | 예약 |
| `startup` | 창업지원 공고 | 예약 |

### 6-3. BusinessDomain

| 값 | 의미 | 대표 키워드 예시 |
| --- | --- | --- |
| `ai` | AI, 인공지능 | AI, 인공지능 |
| `dx` | 디지털전환 | 디지털전환, DX, 디지털트윈 |
| `si` | 시스템 통합 | 시스템 통합, SI, 정보화 |
| `infra` | 인프라 | 인프라, 서버, 네트워크, 클라우드 |
| `data` | 데이터 | 데이터, 빅데이터 |
| `security` | 보안 | 보안 |
| `maintenance` | 유지보수 | IT서비스, 유지보수 |

### 6-4. NoticeStatus

| 값 | 의미 |
| --- | --- |
| `open` | 접수 또는 입찰 진행 중 |
| `closed` | 마감 |
| `scheduled` | 예정 |
| `unknown` | 원천 상태를 공통 상태로 판단할 수 없음 |

### 6-5. KeywordGroup

| 값 | 의미 |
| --- | --- |
| `core` | 핵심 키워드 |
| `supporting` | 보조 키워드 |
| `exclude` | 강제 제외 키워드 |

## 7. MatchedKeyword 기준

`match_keywords`는 단순 문자열 배열이 아니라 매칭 근거를 추적할 수 있는 값 객체로 본다.  
엑셀 출력 시에는 `keyword` 값만 쉼표로 연결해 표시할 수 있다.

| 필드명 | 필수 여부 | 타입 기준 | 설명 |
| --- | --- | --- | --- |
| `keyword` | 필수 | `str` | 매칭된 키워드 |
| `group` | 필수 | `KeywordGroup` | 핵심, 보조, 강제 제외 구분 |
| `domain` | 선택 | `BusinessDomain` | 연결된 사업 도메인. 강제 제외 키워드는 비워둘 수 있다. |

## 8. 날짜와 시간 기준

- `posted_at`, `end_at`은 날짜 단위로 관리한다.
- 내부 타입 기준은 `date`이다.
- 원천 값이 날짜와 시간을 함께 제공해도 1차 MVP에서는 날짜만 사용한다.
- `collected_at`은 timezone-aware `datetime`으로 관리한다.
- `collected_at`의 기본 시간대는 `Asia/Seoul`이다.
- 엑셀 출력 시 날짜는 `YYYY-MM-DD` 형식으로 변환한다.

## 9. URL 기준

- `url`은 필수 값이다.
- `url`은 `http://` 또는 `https://`로 시작해야 한다.
- 엑셀 출력 시 클릭 가능한 하이퍼링크로 변환 가능해야 한다.
- URL이 없거나 클릭 불가능하면 해당 공고는 필수 필드 파싱 실패로 기록한다.

## 10. 중복 판단 키

중복 판단은 `DeduplicationKey`로 수행한다.

### 10-1. 키 생성 우선순위

1. `source_notice_id`가 있으면 `source + source_notice_id`를 사용한다.
2. `source_notice_id`가 없고 `url`이 안정적이면 `source + normalized_url`을 사용한다.
3. 둘 다 어렵다면 `source + normalized_title + normalized_organization + posted_at + end_at`을 사용한다.

### 10-2. DeduplicationKey 필드

| 필드명 | 필수 여부 | 타입 기준 | 설명 |
| --- | --- | --- | --- |
| `source` | 필수 | `NoticeSource` | 공고 출처 |
| `key_type` | 필수 | `str` | `source_notice_id`, `url`, `content_fingerprint` 중 하나 |
| `key_value` | 필수 | `str` | 정규화된 중복 판단 값 |

### 10-3. 정규화 규칙

- 제목과 기관명은 앞뒤 공백을 제거한다.
- 연속 공백은 하나의 공백으로 축약한다.
- URL은 추적용 query parameter가 있으면 제거할 수 있다.
- 날짜가 없으면 빈 문자열로 처리하되, 해당 fallback 키의 신뢰도는 낮게 기록한다.

## 11. 엑셀 컬럼 매핑

| 엑셀 컬럼 | Notice 필드 |
| --- | --- |
| `source` | `source` |
| `notice_type` | `notice_type` |
| `primary_domain` | `primary_domain` |
| `title` | `title` |
| `organization` | `organization` |
| `posted_at` | `posted_at` |
| `end_at` | `end_at` |
| `status` | `status` |
| `url` | `url` |
| `match_keywords` | `match_keywords.keyword` 목록 |
| `collected_at` | `collected_at` |

## 12. 1차 확정 사항

- 공통 모델 이름은 `Notice`로 한다.
- 중복 판단 모델 이름은 `DeduplicationKey`로 한다.
- 기업마당 `notice_type` 기본값은 `support`로 한다.
- 나라장터 `notice_type` 기본값은 `bid`로 한다.
- 내부 수집 시각은 `Asia/Seoul` 기준 timezone-aware `datetime`으로 둔다.
- 엑셀 날짜 출력은 `YYYY-MM-DD`로 통일한다.
- 실제 코드 반영은 `TASKS.md` 2단계에서 수행한다.

## 13. 남은 결정 사항

- URL query parameter 제거 범위
- `source_notice_id`가 없는 원천 데이터의 fallback 키 신뢰도 기록 방식
- fixture 저장 위치와 파일명 규칙

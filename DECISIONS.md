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

## 미확정 결정 목록

- 저장소 구현 방식
- 테스트 도구와 커버리지 기준
- fixture 저장 위치와 파일명 규칙
- 실제 기업마당 API endpoint 값
- 실제 나라장터 API endpoint 값
- API 키 필수 여부와 인증 파라미터명
- 설정 파일에서 도메인 매핑을 표현하는 구체적 구조

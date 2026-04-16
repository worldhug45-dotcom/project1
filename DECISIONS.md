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

- 공통 데이터 모델 필드별 타입
- 설정 파일 포맷
- 저장소 구현 방식
- 중복 판단 키 구성
- 키워드 매칭 대소문자 처리 방식
- `primary_domain` 선정 우선순위
- 외부 API 실패 재시도 횟수
- 로그 출력 위치와 포맷
- 엑셀 파일명 규칙
- 테스트 도구와 커버리지 기준
- fixture 저장 위치와 파일명 규칙

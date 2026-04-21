# TASKS

이 문서는 `README.md`를 기준으로 1차 MVP 구현을 작은 작업 단위로 나누기 위한 작업 지시서이다.  
각 작업은 한 번에 하나씩 진행하며, 완료 후 `DECISIONS.md`와 `CHECKLIST.md`를 갱신한다.

문서 기준 확정 단계의 핵심 항목이 완료되었으므로, 이제부터 1차 MVP 코드 구현을 시작한다.
구현은 `README.md` 범위와 본 문서의 작업 순서를 따르며, 범위 밖 기능은 즉시 구현하지 않는다.

## 작업 원칙

- 기능 완성보다 계층과 인터페이스 고정을 우선한다.
- 외부 API 호출, DB 저장, 엑셀 출력은 해당 작업 범위가 되기 전까지 구현하지 않는다.
- 범위 밖 기능은 즉시 구현하지 않고 별도 변경요청으로 분리한다.
- 하드코딩이 필요한 값은 먼저 설정 구조로 분리한다.
- 새 소스 추가가 기존 로직 수정이 아니라 어댑터 추가로 가능해야 한다.
- 상위 아키텍처는 `Presentation` / `Application` / `Domain` / `Infrastructure` 계층을 따른다.
- 하위 구현 모듈은 `sources` / `filters` / `normalizers` / `persistence` / `exporters` / `ops`처럼 역할 기준으로 구성할 수 있다.

## 프롬프트 형식

AI에게 작업을 요청할 때는 아래 형식을 사용한다.

```text
목표:

이번 작업 범위:

건드리면 안 되는 범위:

산출물:

완료 조건:
```

## 0단계: 구현 전 기준 고정

0단계는 구현 전에 문서 기준을 확정하는 단계이며, 실제 코드 반영은 이후 단계에서 수행한다.

- [x] 공통 데이터 모델 정의
- [x] 설정 파일 구조 정의
- [x] 중복 판단 키 정의
- [x] 키워드 판정 규칙 정의
- [x] 로그 필수 항목 정의
- [x] 예외 처리 정책 정의
- [x] 엑셀 시트/컬럼 기준 정의
- [ ] 테스트 범위 정의

## 1단계: 프로젝트 골격 고정

- [x] 권장 프로젝트 폴더 구조 생성
- [x] Python 패키지 경계 정의
- [x] 실행 진입점 `app/main.py` 생성
- [x] CLI 액션 `collect`, `export`, `all` 틀 정의
- [x] CLI `collect` 액션 기업마당 fixture 모드 연결
- [x] CLI `export` 액션 실제 `.xlsx` 생성 흐름 연결
- [x] 환경별 설정 파일 위치 정의
- [x] 기본 설정 로더 인터페이스 정의
- [x] 필수 설정값 검증 흐름 정의

## 2단계: Domain 계층 고정

2단계는 0단계에서 문서로 확정한 도메인 기준을 실제 코드 모델로 반영하는 단계이다.

- [x] `Notice` 공통 데이터 모델 정의
- [x] `NoticeType` 값 정의
- [x] `BusinessDomain` 값 정의
- [x] `NoticeSource` 값 정의
- [x] `NoticeStatus` 값 정의
- [x] `MatchedKeyword` 표현 방식 정의
- [x] 중복 판단용 `DeduplicationKey` 정의
- [x] 날짜 값 변환 규칙 정의
- [x] URL 값 검증 규칙 정의
- [x] 키워드 판정 규칙의 Domain 계층 소속 확정
- [x] `business_domains`, `primary_domain` 분류 규칙의 Domain 계층 소속 확정

## 3단계: Application 계층 인터페이스 고정

- [x] 공고 수집 Use Case 인터페이스 정의
- [x] 엑셀 산출 Use Case 인터페이스 정의
- [x] 소스 어댑터 Port 정의
- [ ] 키워드 판정 규칙 서비스 소속 계층 확정
- [ ] 원천 데이터 정규화 책임 계층 확정
- [ ] 정규화 흐름 orchestration 책임 정의
- [x] 저장소 Port 정의
- [x] 저장소 조회 Port 계약 정의
- [x] 엑셀 Exporter Port 정의
- [x] 실행 결과 요약 모델 정의
- [x] 기업마당 fixture 기반 collect Use Case 초안 구현
- [x] export Use Case 초안 구현
- [x] CLI collect 실행 결과를 `RunSummary` / `SourceRunSummary`로 확인 가능하게 연결
- [x] CLI export 실행 결과를 `RunSummary.exported_files`로 확인 가능하게 연결
- [x] CLI collect `source_mode=api` 실제 기업마당 수집 경로 연결

## 4단계: 운영 기반 고정

- [x] 로그 이벤트 모델 정의
- [x] 실행 ID 생성 규칙 정의
- [x] 실행 시작/종료 로그 구조 정의
- [x] 소스별 조회/저장/제외 건수 로그 구조 정의
- [x] CLI collect fixture 실행 시 소스별 조회/저장/제외 건수 로그 연결
- [x] CLI collect api 실행 시 소스별 조회/저장/제외 건수 로그 연결
- [x] 오류 유형 로그 구조 정의
- [x] 재시도 가능 오류 기준 정의
- [x] 비치명적 오류 기준 정의
- [x] 치명적 오류 기준 정의
- [x] 저장 실패 시 fatal 오류 로그 흐름 정의
- [x] CLI export 성공 시 `export_finished` 로그 흐름 정의

## 5단계: Infrastructure 어댑터 초안

외부 API 연동 전, 각 소스의 샘플 응답 fixture를 확보하고 DTO/정규화 테스트에 사용한다.

- [x] 기업마당 조회 어댑터 인터페이스 초안 작성
- [ ] 나라장터 조회 어댑터 인터페이스 초안 작성
- [x] 기업마당 샘플 응답 fixture 확보
- [ ] 나라장터 샘플 응답 fixture 확보
- [x] 외부 API 응답 DTO 초안 작성
- [x] fixture 기반 DTO 파싱 테스트 초안 작성
- [x] 기업마당 실제 API 클라이언트 구현
- [x] API 클라이언트 타임아웃 설정 연결
- [x] 재시도 정책 설정 연결
- [ ] 외부 API 점검/공지성 오류 기록 방식 정의

## 6단계: 판정과 정규화

- [ ] 키워드 사전 설정 파일 분리
- [ ] 핵심 키워드 매칭 규칙 구현
- [ ] 보조 키워드 매칭 규칙 구현
- [ ] 강제 제외 키워드 매칭 규칙 구현
- [ ] `business_domains` 다중 태깅 규칙 구현
- [ ] `primary_domain` 선정 규칙 구현
- [x] 기업마당 원천 데이터를 `Notice`로 정규화
- [x] 기업마당 실제 API JSON `jsonArray.item` 응답 파싱 연결
- [ ] 나라장터 원천 데이터를 `Notice`로 정규화

## 7단계: 저장과 재실행 안전성

- [x] 저장소 구현 방식 확정
- [x] SQLite 저장소 초안 구현
- [x] SQLite 저장 스키마 정의
- [x] 중복 저장 방지 규칙 구현
- [x] 적격 공고 저장 흐름 구현
- [x] 재실행 시 동일 건 중복 저장률 0% 검증
- [x] 저장 실패를 치명적 오류로 처리
- [x] 저장 결과 요약 반환
- [x] SQLite 저장소 조회 계약 구현
- [x] InMemory 저장소 조회 계약 구현

## 8단계: 엑셀 산출물

- [x] export Use Case가 사용할 저장소 조회 형태 정의
- [x] `support_notices` 시트 입력 단위 생성
- [x] `bid_notices` 시트 입력 단위 생성
- [x] fake ExcelExporterPort 구현
- [x] export 실행 결과를 `RunSummary.exported_files`에 반영
- [x] collect -> SQLite 저장 -> fake export 흐름 검증
- [x] 엑셀 출력 포맷 기준 문서 작성
- [x] 엑셀 필수 컬럼 순서 테스트 기준 고정
- [x] 엑셀 날짜 표시 형식 테스트 기준 고정
- [x] 엑셀 URL 표시 형식 테스트 기준 고정
- [x] 엑셀 `match_keywords` 표시 형식 테스트 기준 고정
- [x] 엑셀 파일명 규칙 테스트 기준 고정
- [x] 실제 Excel exporter 구현
- [x] 실제 `.xlsx` 파일 생성
- [x] 실제 `support_notices` 시트 생성
- [x] 실제 `bid_notices` 시트 생성
- [x] 실제 URL hyperlink 관계 생성
- [x] CLI export에서 SQLite 저장소 조회 결과를 실제 `.xlsx`로 생성
- [x] 필수 컬럼 순서 고정
- [x] 날짜 형식 `YYYY-MM-DD` 적용
- [x] URL 클릭 가능 형식 적용
- [x] `match_keywords` 표시 형식 적용
- [ ] 최근 공고를 5분 이내 검토 가능한 가독성 확인

## 9단계: 테스트와 품질

- [ ] 키워드 판정 단위 테스트 작성
- [ ] 날짜 변환 단위 테스트 작성
- [ ] 중복 키 생성 단위 테스트 작성
- [x] 정규화 단위 테스트 작성
- [x] fixture 기반 정규화 테스트 작성
- [x] 조회에서 저장까지 통합 테스트 작성
- [x] CLI collect fixture 모드 테스트 작성
- [x] CLI collect api 모드 mocking 테스트 작성
- [x] collect + SQLite 저장 테스트 작성
- [x] SQLite 중복 저장 방지 테스트 작성
- [x] 저장 실패 fatal 처리 단위 테스트 작성
- [x] 저장 실패 CLI 로그 흐름 테스트 작성
- [x] export 준비용 저장소 조회 계약 테스트 작성
- [x] export Use Case 단위 테스트 작성
- [x] collect -> SQLite 저장 -> fake export 통합 테스트 작성
- [x] 엑셀 출력 포맷 테스트 초안 작성
- [x] 엑셀 시트/컬럼 생성 테스트 작성
- [x] 실제 `.xlsx` 파일 생성 테스트 작성
- [x] CLI collect -> SQLite 저장 -> CLI export -> 실제 `.xlsx` 생성 테스트 작성
- [ ] format 검사 연결
- [ ] lint 검사 연결
- [ ] type check 연결

## 10단계: MVP 완료 검증

- [ ] 기업마당 상위 20건 조회 성공 확인
- [ ] 나라장터 상위 20건 조회 성공 확인
- [ ] 필수 필드 파싱 성공률 95% 이상 확인
- [ ] 적격 판정 건 100% 저장 확인
- [ ] 동일 건 재수집 시 중복 저장률 0% 확인
- [ ] 기업마당 실제 API 수동 collect 검증
- [x] 엑셀 생성 성공 확인
- [ ] 로그 생성 성공 확인
- [ ] 수동 재실행 성공 확인

## 11단계: 기업마당 실제 API 수동 검증 메모

- [x] `source_mode=api`에서 기업마당 실제 API collect 성공 확인
- [x] 실제 API 응답 기준 `saved_count > 0` 저장 성공 사례 확인
- [x] SQLite 저장 결과를 CLI export로 `.xlsx` 생성 확인
- [x] 수동 검증 절차를 `doc/bizinfo_api_manual_verification.md`에 정리

## 12단계: 실제 API 기준 키워드 보정

- [x] diagnostics 기준 `no_keyword_match` 원인 분석
- [x] 실제 API 상위 100건 기준 후보 키워드 시뮬레이션
- [x] `사물인터넷`, `IoT`, `ICT`, `SW`, `소프트웨어` 보조 키워드 반영
- [x] 도메인 매핑 보정안 반영
- [x] 분석 결과를 `doc/keyword_adjustment_analysis.md`에 정리

## 13단계: 운영 관찰 준비와 day 1 기록

- [x] 운영용 `config/settings.local.toml`에 보정된 키워드 세트 반영
- [x] 기업마당 단독 관찰용 저장 경로와 출력 경로 고정
- [x] diagnostics 기반 관찰 기록 스크립트 추가
- [x] day 1 실제 collect 관찰 스냅샷 기록
- [x] day 2 실제 collect 관찰 스냅샷 기록
- [ ] day 3 실제 collect 관찰 스냅샷 기록
- [x] `skip_reason` 분포와 저장/제외 대표 사례를 관찰 로그로 누적할 수 있게 정리

## 14단계: 내부 사용자 수동 운영 지원

- [x] 사용자용 `config/keywords.override.toml` 구조 추가
- [x] 키워드 override 자동 로딩 구조 구현
- [x] collect/export/observe 수동 실행 wrapper 추가
- [x] 실행 후 결과물 위치 출력
- [x] 실행 결과 요약/경로 출력 형식 일관화
- [x] 실패 시 다음 확인 안내 문구 추가
- [x] 운영 가이드 상단에 복붙용 명령 5개 정리
- [x] collect/export/observe PowerShell launcher 추가
- [x] `status` 액션으로 현재 경로와 최근 상태 요약 출력
- [x] 가장 최근 `.xlsx` 파일 경로 출력
- [x] 최근 collect/export/observe 상태 요약 출력
- [x] 사용자용 수동 운영 가이드 문서 추가

## 15단계: 웹 운영자 대시보드 MVP 설계

- [x] 웹 운영자 대시보드 MVP 구조안 문서화
- [x] 단일 운영 화면 구성안 문서화
- [x] 글래스모피즘 디자인 가이드 정의
- [x] Docker Compose 배포 구조 초안 문서화
- [x] 구현용 TODO와 권장 구현 순서 정리
- [ ] 웹 Presentation shell 구현
- [ ] `GET /api/status` 상태 조회 endpoint 구현
- [ ] `collect` 웹 액션 연결
- [ ] `export` 웹 액션 연결
- [ ] `observe` 웹 액션 연결
- [ ] 웹 전용 job registry 또는 실행 중 상태 표시 구조 구현
- [ ] `/health` endpoint와 Docker healthcheck 구현

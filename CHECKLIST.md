# CHECKLIST

이 문서는 작업 완료 여부를 검증하기 위한 체크리스트이다.  
각 구현 작업이 끝날 때마다 관련 항목을 확인하고 필요한 경우 결과를 기록한다.

## 공통 검토 기준

- [x] `README.md`의 1차 MVP 범위를 벗어나지 않았다.
- [x] 문서로 확정된 기준을 코드에 반영했다.
- [x] 코드 구현이 `README.md`의 1차 MVP 범위를 벗어나지 않았다.
- [x] 범위 밖 기능은 별도 변경요청으로 분리했다.
- [x] 책임이 한 계층이나 한 모듈에 과도하게 섞이지 않았다.
- [x] 상위 계층 구조와 하위 역할 모듈 구조가 충돌하지 않는다.
- [x] 비즈니스 규칙은 Domain 계층에 위치한다.
- [x] 키워드 판정과 도메인 분류 규칙은 Domain 계층에 위치한다.
- [x] 원천 응답 정규화 책임은 Infrastructure 또는 Application 경계에 위치한다.
- [x] 외부 API, DB, 파일 시스템 의존성은 Infrastructure 계층으로 분리했다.
- [x] 하드코딩해야 할 값은 설정으로 분리했다.
- [ ] 동일 작업을 재실행해도 결과가 깨지지 않는다.
- [ ] 새 소스 추가가 기존 핵심 로직 수정 없이 가능하다.

## 구현 전 체크리스트

- [x] 공통 데이터 모델이 확정되었다.
- [x] 설정 파일 구조가 확정되었다.
- [x] 중복 판단 키가 확정되었다.
- [x] 키워드 판정 규칙이 확정되었다.
- [x] 로그 필수 항목이 확정되었다.
- [x] 예외 처리 정책이 확정되었다.
- [x] 엑셀 시트/컬럼 기준이 확정되었다.
- [ ] 테스트 범위가 확정되었다.

## 데이터 모델 체크리스트

- [x] `notice_type`은 `support`, `bid`, `rnd`, `startup` 기준과 충돌하지 않는다.
- [x] `business_domains`는 다중 선택을 지원한다.
- [x] `primary_domain`은 대표 1개만 가진다.
- [x] `match_keywords`는 매칭된 키워드 목록을 보존한다.
- [x] 날짜는 내부에서 일관된 타입으로 관리한다.
- [x] 엑셀 출력 날짜는 `YYYY-MM-DD` 형식으로 변환 가능하다.
- [x] URL은 클릭 가능한 값으로 검증 가능하다.
- [x] 중복 판단 키를 안정적으로 생성할 수 있다.
- [x] 공통 데이터 모델이 코드에 반영되었다.

## 설정 체크리스트

- [x] 설정 파일 포맷이 확정되었다.
- [x] 설정 섹션 목록이 확정되었다.
- [x] 필수 설정값 목록이 확정되었다.
- [x] 설정 기본값 기준이 확정되었다.
- [x] override 우선순위가 확정되었다.
- [x] 비밀값 처리 방식이 확정되었다.
- [x] 잘못된 설정의 실패 방식이 확정되었다.
- [x] 키워드 목록을 코드에 하드코딩하지 않았다.
- [x] fixture 모드 여부를 설정 또는 CLI 옵션으로 구분할 수 있다.
- [x] 기업마당 인증키는 `PROJECT1_BIZINFO_CERT_KEY` 환경 변수로만 주입된다.
- [ ] 시트명을 코드에 하드코딩하지 않았다.
- [ ] 파일명 규칙을 코드에 하드코딩하지 않았다.
- [ ] 활성 소스 목록을 코드에 하드코딩하지 않았다.
- [ ] 재시도 횟수를 코드에 하드코딩하지 않았다.
- [ ] 타임아웃 값을 코드에 하드코딩하지 않았다.
- [ ] 출력 경로를 코드에 하드코딩하지 않았다.
- [x] 필수 설정값은 실행 시작 시 검증된다.

## 수집 체크리스트

- [x] 기업마당 조회 인터페이스가 정의되었다.
- [x] 나라장터 조회 인터페이스가 정의되었다.
- [x] 기업마당 샘플 응답 fixture가 확보되었다.
- [x] 나라장터 샘플 응답 fixture가 확보되었다.
- [x] 외부 API DTO와 내부 `Notice` 모델이 분리되었다.
- [x] 샘플 응답 fixture 기반으로 DTO 파싱을 검증할 수 있다.
- [x] 실제 API JSON `jsonArray.item` 응답을 DTO로 파싱할 수 있다.
- [x] 외부 API 없이 핵심 정규화 로직을 검증할 수 있다.
- [x] 외부 API 없이 CLI collect 흐름을 검증할 수 있다.
- [x] `source_mode=api`에서 기업마당 실제 API 수집 경로를 탈 수 있다.
- [ ] 외부 API 점검이나 공지성 중단을 내부 장애와 구분한다.
- [ ] 일부 선택 필드 누락은 비치명적 오류로 처리 가능하다.
- [ ] 한 트랙 전체 수집 실패는 치명적 실패로 처리 가능하다.

## 키워드 판정 체크리스트

- [x] 매칭 대상 필드가 확정되었다.
- [x] 전처리 규칙이 확정되었다.
- [x] 강제 제외/핵심/보조 키워드 우선순위가 확정되었다.
- [x] 도메인 매핑표가 확정되었다.
- [x] `primary_domain` 선정 규칙이 확정되었다.
- [x] 적격 판정 기준이 확정되었다.
- [x] 핵심 키워드 매칭이 동작한다.
- [x] 보조 키워드 매칭이 동작한다.
- [x] 강제 제외 키워드 매칭이 동작한다.
- [x] 강제 제외 키워드는 적격 판정에서 우선 처리된다.
- [x] 매칭된 키워드가 `match_keywords`에 기록된다.
- [x] `business_domains`와 `primary_domain`이 일관되게 산출된다.

## 저장 체크리스트

- [x] 적격 판정된 공고는 저장된다.
- [x] 동일 건 재수집 시 중복 저장되지 않는다.
- [x] SQLite 저장소 초안이 `NoticeRepositoryPort`를 구현한다.
- [x] SQLite 저장 스키마가 `Notice`와 `DeduplicationKey` 기준을 반영한다.
- [x] SQLite 테이블 초기화 책임이 저장소 계층에 위치한다.
- [x] 이후 export가 읽을 수 있는 기본 조회 경로가 있다.
- [x] 조회 계약이 `NoticeRepositoryPort`에 정의되어 있다.
- [x] InMemory와 SQLite 저장소가 같은 조회 계약을 지원한다.
- [x] 저장 실패는 치명적 오류로 처리된다.
- [x] 저장 실패 시 `RunSummary` 상태는 `failed`이다.
- [x] 저장 실패 시 `SourceRunSummary.error_count`가 증가한다.
- [x] 저장 결과 건수가 실행 결과 요약에 반영된다.
- [x] 저장소 접근은 저장소 계층으로 통일된다.

## 엑셀 산출물 체크리스트

- [x] `support_notices` 시트가 생성된다.
- [x] `bid_notices` 시트가 생성된다.
- [x] `support_notices` 시트 입력 단위가 생성된다.
- [x] `bid_notices` 시트 입력 단위가 생성된다.
- [x] 필수 컬럼 순서가 문서로 확정되었다.
- [x] 필수 컬럼이 모두 포함된다.
- [x] 날짜 형식은 `YYYY-MM-DD`이다.
- [x] URL 표시 기준이 확정되었다.
- [x] `match_keywords` 표시 기준이 확정되었다.
- [x] `business_domains`는 엑셀 출력에서 제외된다.
- [x] 빈 시트 허용 기준이 확정되었다.
- [x] 파일명 규칙이 확정되었다.
- [x] 실제 `.xlsx` 파일이 생성된다.
- [x] URL은 실제 Excel hyperlink 관계로 연결된다.
- [x] CLI export 액션으로 실제 `.xlsx` 파일을 생성할 수 있다.
- [ ] 최근 공고를 5분 이내 검토 가능한 가독성을 갖춘다.
- [x] 엑셀 Exporter Port가 정의되었다.
- [x] export Use Case가 저장소에서 읽을 최소 조회 형태가 정의되었다.
- [x] fake exporter로 export 입력 구조를 검증할 수 있다.

## Application 체크리스트

- [x] 공고 수집 Use Case 계약이 정의되었다.
- [x] 기업마당 fixture 기반 collect Use Case 초안이 구현되었다.
- [x] 나라장터 fixture 기반 collect Use Case 초안이 구현되었다.
- [x] 엑셀 산출 Use Case 계약이 정의되었다.
- [x] 소스 어댑터 Port가 정의되었다.
- [x] 저장소 Port가 정의되었다.
- [x] 엑셀 Exporter Port가 정의되었다.
- [x] 실행 결과 요약 모델이 정의되었다.
- [x] collect / export / all 액션이 같은 실행 결과 모델을 공유할 수 있다.
- [x] Application 계층은 흐름 제어 계약만 가진다.
- [x] collect 결과가 `RunSummary` / `SourceRunSummary`로 집계된다.
- [x] export 결과가 `RunSummary.exported_files`로 집계된다.
- [x] export Use Case는 저장소 조회와 exporter 호출 orchestration만 담당한다.
- [x] CLI collect 액션이 기업마당 fixture collect Use Case에 연결된다.
- [x] CLI collect 액션이 나라장터 fixture collect Use Case에 연결된다.
- [x] CLI collect 액션이 기업마당 실제 API collect Use Case에 연결된다.
- [x] CLI export 액션이 SQLite 저장소와 실제 Excel exporter에 연결된다.

## 로그 체크리스트

- [x] 실행 시작 시각이 기록된다.
- [x] 실행 종료 시각이 기록된다.
- [x] 실행 ID가 기록된다.
- [x] 실행 액션이 기록된다.
- [x] 실행 결과 상태가 기록된다.
- [x] 소스명이 기록된다.
- [x] 조회 건수가 기록된다.
- [x] 저장 건수가 기록된다.
- [x] 제외 건수가 기록된다.
- [x] 오류 유형이 기록된다.
- [x] 저장 실패 시 error 로그가 `fatal`로 기록된다.
- [x] 저장 실패 시 run_finished 로그가 `failed`로 기록된다.
- [x] export 성공 시 `export_finished` 로그가 기록된다.
- [x] 출력 파일 경로가 기록된다.
- [x] 로그와 오류 메시지에 인증키 원문이 노출되지 않는다.

## 테스트 체크리스트

- [ ] 키워드 판정 단위 테스트가 있다.
- [ ] 날짜 변환 단위 테스트가 있다.
- [x] 중복 키 생성 단위 테스트가 있다.
- [x] 정규화 단위 테스트가 있다.
- [x] fixture 기반 정규화 테스트가 있다.
- [x] 외부 API 없이 테스트를 실행할 수 있다.
- [x] 조회에서 저장까지 통합 테스트가 있다.
- [x] CLI collect fixture 모드 테스트가 있다.
- [x] CLI collect api 모드 mocking 테스트가 있다.
- [x] collect + SQLite 저장 테스트가 있다.
- [x] SQLite 중복 저장 방지 테스트가 있다.
- [x] 저장 실패 fatal 처리 단위 테스트가 있다.
- [x] 저장 실패 CLI 로그 흐름 테스트가 있다.
- [x] export 준비용 저장소 조회 계약 테스트가 있다.
- [x] export Use Case 단위 테스트가 있다.
- [x] collect -> SQLite 저장 -> fake export 통합 테스트가 있다.
- [x] 엑셀 출력 포맷 테스트 초안이 있다.
- [x] 엑셀 시트/컬럼 생성 테스트가 있다.
- [x] 실제 `.xlsx` 파일 생성 테스트가 있다.
- [x] CLI collect -> SQLite 저장 -> CLI export -> 실제 `.xlsx` 생성 테스트가 있다.
- [ ] format 검사를 실행했다.
- [ ] lint 검사를 실행했다.
- [ ] type check를 실행했다.

## 실제 API 수동 검증 체크리스트

- [x] `source_mode=api`에서 기업마당 실제 API collect가 성공한다.
- [x] 실제 API 응답 기준으로 SQLite 저장 성공 사례가 확인되었다.
- [x] 저장된 데이터를 CLI export로 실제 `.xlsx` 파일까지 생성할 수 있다.
- [x] fixture 모드는 기존대로 유지된다.
- [x] 인증키가 로그와 코드에 노출되지 않는다.

## 실제 API 기반 키워드 보정 체크리스트

- [x] `no_keyword_match` 상위 원인을 diagnostics로 확인했다.
- [x] 실제 API 응답 기준 후보 키워드 시뮬레이션을 수행했다.
- [x] 보정 키워드와 도메인 매핑이 문서와 설정에 반영되었다.
- [x] 강제 제외 키워드는 이번 라운드에서 유지 여부를 검토했다.

## 운영 관찰 체크리스트

- [x] 운영용 `config/settings.local.toml`에 보정된 키워드 세트가 반영되었다.
- [x] 기업마당 단독 관찰 조건으로 `g2b`가 비활성화되었다.
- [x] diagnostics 기반 관찰 기록 스크립트가 있다.
- [x] day 1 실제 collect 관찰 기록이 남았다.
- [x] day 2 실제 collect 관찰 기록이 남았다.
- [ ] day 3 실제 collect 관찰 기록이 남았다.
- [x] `fetched_count`, `saved_count`, `skipped_count`를 날짜별로 비교할 수 있다.
- [x] `no_keyword_match`, `excluded_keyword`, `normalization_value_error` 분포를 날짜별로 비교할 수 있다.
- [x] 저장 대표 사례와 제외 대표 사례를 함께 확인할 수 있다.
- [x] 다음 라운드 검토 후보가 분리되어 있다.

## 내부 사용자 수동 운영 체크리스트

- [x] 코드 수정 없이 키워드 추가/제거가 가능하다.
- [x] `config/keywords.override.toml` 구조가 있다.
- [x] `collect`, `export`, `observe`를 한 진입점에서 수동 실행할 수 있다.
- [x] `collect`, `export`, `observe`, `status` launcher가 있다.
- [x] 실행 후 설정 파일 경로를 바로 확인할 수 있다.
- [x] 실행 후 키워드 override 파일 경로를 바로 확인할 수 있다.
- [x] 실행 후 DB 또는 산출물 경로를 바로 확인할 수 있다.
- [x] 실행 결과 요약과 경로 출력 형식이 일관되다.
- [x] 실패 시 다음 확인 항목이 안내된다.
- [x] 운영자가 복붙해서 쓸 수 있는 명령 5개가 가이드 상단에 정리되어 있다.
- [x] `status`로 최근 collect/export/observe 상태를 빠르게 확인할 수 있다.
- [x] `status`로 가장 최근 `.xlsx` 파일 경로를 바로 확인할 수 있다.
- [x] 사용자용 운영 가이드가 있다.

## 웹 운영자 대시보드 설계 체크리스트

- [x] 웹 MVP 구조안이 문서로 정리되었다.
- [x] 웹은 기존 Python 엔진을 재사용하는 얇은 orchestration 레이어로 정의되었다.
- [x] 첫 화면에 `status`, `collect`, `export`, `observe`, 최근 결과물 경로가 포함되도록 설계되었다.
- [x] 현재 `config` 경로와 `keywords override` 경로를 화면에서 확인할 수 있도록 설계되었다.
- [x] 글래스모피즘 디자인 가이드가 정의되었다.
- [x] Docker Compose 배포 구조와 볼륨 구성이 정리되었다.
- [ ] 웹 Presentation shell이 구현되었다.
- [ ] 웹에서 `collect`, `export`, `observe` 실행이 가능하다.
- [ ] 웹에서 최근 결과물 위치와 최근 상태를 즉시 확인할 수 있다.
- [ ] `/health` endpoint와 컨테이너 healthcheck가 구현되었다.

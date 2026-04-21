# 기업마당 collect 관찰 기록

이 문서는 `source_mode=api` 기준 기업마당 실제 collect 결과를 2~3일간 같은 조건으로 비교하기 위한 운영 기록이다.

## 관찰 조건

- config: `config/settings.local.toml`
- action: `collect`
- source_mode: `api`
- diagnostics: `on`
- g2b: `disabled`
- storage: 관찰용 snapshot DB를 실행마다 새로 사용

## 비교 표

| date | run_id | status | fetched | saved | skipped | error | no_keyword_match | excluded_keyword | normalization_value_error | other |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-20 | `20260420T045421284029Z_918b36b7` | success | 20 | 4 | 16 | 0 | 9 | 7 | 0 | 0 |
| 2026-04-21 | `20260421T002232814103Z_f10495eb` | success | 20 | 4 | 16 | 0 | 11 | 5 | 0 | 0 |
| 2026-04-21 | `20260421T015804299957Z_7b662c08` | success | 20 | 4 | 16 | 0 | 11 | 5 | 0 | 0 |

## 누적 요약

- 누적 관찰 일수: `3`일
- 누적 fetched_count: `60`
- 누적 saved_count: `12`
- 누적 skipped_count: `48`
- 누적 error_count: `0`
- 3일 누적 관찰이 완료되었다.
- no_keyword_match 상위 skipped 제목:
  - `[서남권] 2026년 지역혁신클러스터육성(비R&D) 기업지원사업 모집 통합 공고`: `2`회
  - `[충북] 2026년 바이오기업 GMP인증 지원사업 공고`: `2`회
  - `2026년 K-EXPO USA K-뷰티 팝업 스토어 참여기업 모집 공고`: `2`회
  - `[충북] 2026년 벤처 및 스타트업 기업 공동연구장비 활용 지원사업 참여기업 모집 공고`: `2`회
  - `2026년 경북 원자력 선도기업 육성사업 지원기업 모집 공고`: `2`회
  - `[경북] 경주시 2026년 중소기업 기숙사 임차비 지원사업 참여기업 모집 공고`: `2`회
  - `2026년 해외 동반진출 K-브랜드 보호 전략 지원사업 기업 모집 공고`: `2`회
  - `[경기] 부천시 2026년 홍콩 코스모프로프 아시아 COSMOPROF ASIA 2026 참가지원 계획 공고`: `2`회
- excluded_keyword 상위 제외 사례:
  - `[대전] 2026년 소셜 임팩트 랩(Lab) 예비 창업기업 모집 공고`: `2`회
  - `[충북] 2026년 2차 기숙사임차비지원사업 참여기업 추가모집 공고`: `2`회
  - `[대전] 2026년 소셜임팩트 체인저스 7기 소셜벤처 분야 창업기업 모집 공고`: `2`회
  - `[부산] 2026년 산학연계 현장실습 지원사업 하계 계절학기 참여기업 모집 공고`: `2`회
  - `2026년 웹소설 번역비 지원 사업 추가 모집 공고`: `2`회
- excluded_keyword 재검토 후보:
  - `교육`: `6`회
  - `채용`: `4`회
  - `문화`: `2`회
- 저장 대표 사례 누적:
  - `2026년 2차 정보보호핵심원천기술개발사업 신규지원 대상과제 공고`: `2`회
  - `2026년 K테크서비스 중소벤처기업 사우디 파트너십 구축 지원사업 참여기업 모집 공고`: `2`회
  - `2026년 IoT 보안인증 인증시험 수수료 지원 공고`: `2`회
  - `2026년 2차 서울테크노파크 수요기술조사사업 참여기업 모집 공고`: `2`회

## 실행 명령

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
python scripts/observe_bizinfo_collect.py --config config/settings.local.toml
```

## 관찰 1: 2026-04-20

- run_id: `20260420T045421284029Z_918b36b7`
- status: `success`
- fetched_count: `20`
- saved_count: `4`
- skipped_count: `16`
- error_count: `0`
- skip_reason 분포:
  - `excluded_keyword`: `7`
  - `no_keyword_match`: `9`
- 저장 대표 사례:
  - [���] ��õ�� 2026�� �繰���ͳ�(IoT) ������� ���� ������� ����� | 기관=��⵵ | primary_domain=infra | keywords=supporting=['�繰���ͳ�', 'IoT']
  - [���] �Ȼ�� 2026�� ���ұ�� ���� �������(3�ܰ�)�ű����� ������ ���� | 기관=��⵵ | primary_domain=si | keywords=supporting=['SW']
  - [�泲] 2026�� ��������� ������ ��� ������� ������� �߰� ���� ���� | 기관=��󳲵� | primary_domain=si | keywords=supporting=['ICT', 'SW']
- 제외 대표 사례:
  - [�λ�] 2026�� �������� �簢���� ���߰������(��������) ������� �������� | 기관=�λ걤���� | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [�λ�] 2026�� �������������� ������� ���� ���� | 기관=�λ걤���� | skip_reason=excluded_keyword | keywords=exclude=['����'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [����] 2026�� ���� ��Ƽ in ���� ��� ������� ���� ���� | 기관=����Ư����ġ�� | skip_reason=excluded_keyword | keywords=exclude=['���'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [���] ����� 2026�� ��ŸƮ�� ������ġ ������� ���� ���� ���� | 기관=��⵵ | skip_reason=excluded_keyword | keywords=exclude=['���'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [��õ] ������������ 2026�� �Ѥ��� IP SOLUTION ������� ���� ���� | 기관=��õ������ | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.

## 관찰 2: 2026-04-21

- run_id: `20260421T002232814103Z_f10495eb`
- status: `success`
- fetched_count: `20`
- saved_count: `4`
- skipped_count: `16`
- error_count: `0`
- skip_reason 분포:
  - `excluded_keyword`: `5`
  - `no_keyword_match`: `11`
- 저장 대표 사례:
  - 2026년 2차 정보보호핵심원천기술개발사업 신규지원 대상과제 공고 | 기관=과학기술정보통신부 | primary_domain=security | keywords=supporting=['보안']
  - 2026년 K테크서비스 중소벤처기업 사우디 파트너십 구축 지원사업 참여기업 모집 공고 | 기관=중소벤처기업부 | primary_domain=ai | keywords=core=['AI']
  - 2026년 IoT 보안인증 인증시험 수수료 지원 공고 | 기관=과학기술정보통신부 | primary_domain=infra | keywords=supporting=['보안', 'IoT', '사물인터넷']
  - 2026년 2차 서울테크노파크 수요기술조사사업 참여기업 모집 공고 | 기관=서울특별시 | primary_domain=infra | keywords=supporting=['네트워크']
- 제외 대표 사례:
  - [서남권] 2026년 지역혁신클러스터육성(비R&D) 기업지원사업 모집 통합 공고 | 기관=전라남도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 바이오기업 GMP인증 지원사업 공고 | 기관=충청북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 K-EXPO USA K-뷰티 팝업 스토어 참여기업 모집 공고 | 기관=중소벤처기업부 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 벤처 및 스타트업 기업 공동연구장비 활용 지원사업 참여기업 모집 공고 | 기관=충청북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [대전] 2026년 소셜 임팩트 랩(Lab) 예비 창업기업 모집 공고 | 기관=대전광역시 | skip_reason=excluded_keyword | keywords=exclude=['교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 2차 기숙사임차비지원사업 참여기업 추가모집 공고 | 기관=충청북도 | skip_reason=excluded_keyword | keywords=exclude=['채용'] | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 경북 원자력 선도기업 육성사업 지원기업 모집 공고 | 기관=경상북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [경북] 경주시 2026년 중소기업 기숙사 임차비 지원사업 참여기업 모집 공고 | 기관=경상북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [대전] 2026년 소셜임팩트 체인저스 7기 소셜벤처 분야 창업기업 모집 공고 | 기관=대전광역시 | skip_reason=excluded_keyword | keywords=exclude=['교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 해외 동반진출 K-브랜드 보호 전략 지원사업 기업 모집 공고 | 기관=지식재산처 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [부산] 2026년 산학연계 현장실습 지원사업 하계 계절학기 참여기업 모집 공고 | 기관=부산광역시 | skip_reason=excluded_keyword | keywords=exclude=['채용', '교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [경기] 부천시 2026년 홍콩 코스모프로프 아시아 COSMOPROF ASIA 2026 참가지원 계획 공고 | 기관=경기도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 웹소설 번역비 지원 사업 추가 모집 공고 | 기관=문화체육관광부 | skip_reason=excluded_keyword | keywords=exclude=['문화'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [전남] 2026년 1차 국방기술진흥연구소 전남국방벤처센터 협약기업 모집 공고 | 기관=방위사업청 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [경기] 부천시 2026년 한국전자전(KES 2026) 참가기업 모집 공고 | 기관=경기도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [울산] 2026년 상반기 산업안전보건 국제표준 인증기업 지원사업 시행 공고 | 기관=울산광역시 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.

## 관찰 3: 2026-04-21

- run_id: `20260421T015804299957Z_7b662c08`
- status: `success`
- fetched_count: `20`
- saved_count: `4`
- skipped_count: `16`
- error_count: `0`
- skip_reason 분포:
  - `excluded_keyword`: `5`
  - `no_keyword_match`: `11`
- 저장 대표 사례:
  - 2026년 2차 정보보호핵심원천기술개발사업 신규지원 대상과제 공고 | 기관=과학기술정보통신부 | primary_domain=security | keywords=supporting=['보안']
  - 2026년 K테크서비스 중소벤처기업 사우디 파트너십 구축 지원사업 참여기업 모집 공고 | 기관=중소벤처기업부 | primary_domain=ai | keywords=core=['AI']
  - 2026년 IoT 보안인증 인증시험 수수료 지원 공고 | 기관=과학기술정보통신부 | primary_domain=infra | keywords=supporting=['보안', 'IoT', '사물인터넷']
  - 2026년 2차 서울테크노파크 수요기술조사사업 참여기업 모집 공고 | 기관=서울특별시 | primary_domain=infra | keywords=supporting=['네트워크']
- 제외 대표 사례:
  - [서남권] 2026년 지역혁신클러스터육성(비R&D) 기업지원사업 모집 통합 공고 | 기관=전라남도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 바이오기업 GMP인증 지원사업 공고 | 기관=충청북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 K-EXPO USA K-뷰티 팝업 스토어 참여기업 모집 공고 | 기관=중소벤처기업부 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 벤처 및 스타트업 기업 공동연구장비 활용 지원사업 참여기업 모집 공고 | 기관=충청북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [대전] 2026년 소셜 임팩트 랩(Lab) 예비 창업기업 모집 공고 | 기관=대전광역시 | skip_reason=excluded_keyword | keywords=exclude=['교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [충북] 2026년 2차 기숙사임차비지원사업 참여기업 추가모집 공고 | 기관=충청북도 | skip_reason=excluded_keyword | keywords=exclude=['채용'] | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 경북 원자력 선도기업 육성사업 지원기업 모집 공고 | 기관=경상북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [경북] 경주시 2026년 중소기업 기숙사 임차비 지원사업 참여기업 모집 공고 | 기관=경상북도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [대전] 2026년 소셜임팩트 체인저스 7기 소셜벤처 분야 창업기업 모집 공고 | 기관=대전광역시 | skip_reason=excluded_keyword | keywords=exclude=['교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 해외 동반진출 K-브랜드 보호 전략 지원사업 기업 모집 공고 | 기관=지식재산처 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [부산] 2026년 산학연계 현장실습 지원사업 하계 계절학기 참여기업 모집 공고 | 기관=부산광역시 | skip_reason=excluded_keyword | keywords=exclude=['채용', '교육'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [경기] 부천시 2026년 홍콩 코스모프로프 아시아 COSMOPROF ASIA 2026 참가지원 계획 공고 | 기관=경기도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - 2026년 웹소설 번역비 지원 사업 추가 모집 공고 | 기관=문화체육관광부 | skip_reason=excluded_keyword | keywords=exclude=['문화'] | detail=Bizinfo notice is not eligible by keyword rules.
  - [전남] 2026년 1차 국방기술진흥연구소 전남국방벤처센터 협약기업 모집 공고 | 기관=방위사업청 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [경기] 부천시 2026년 한국전자전(KES 2026) 참가기업 모집 공고 | 기관=경기도 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.
  - [울산] 2026년 상반기 산업안전보건 국제표준 인증기업 지원사업 시행 공고 | 기관=울산광역시 | skip_reason=no_keyword_match | detail=Bizinfo notice is not eligible by keyword rules.


## 다음 라운드 검토 후보

- 국방기술/국방벤처: day 2 no_keyword_match 사례가 나와 방산·국방 SI/infra 인접 키워드 후보로 관찰 지속
- 전자전/KES: 전자·하드웨어 계열 전시회 공고가 target scope인지 잡음인지 day 3까지 추가 확인 필요
- 플랫폼: 인접성은 있으나 일반 사업/마케팅 문맥 잡음이 여전히 커서 보류 유지
- IP: 브랜드/IP 보호 전략 문맥이 기술 도메인과 직접 연결되는지 근거가 더 필요해 보류 유지
- 교육: excluded_keyword 재검토 후보이지만 2일 누적 기준 비적격 사례가 우세해 아직 유지

## 메모

- 이번 라운드에서는 제외 키워드 규칙을 직접 수정하지 않고 근거만 누적한다.
- 동일 조건 비교를 위해 config, source_mode, page_size, retry 설정은 관찰 기간 동안 고정한다.

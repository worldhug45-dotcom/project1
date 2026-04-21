# fixture 기준

## 1. 목적

이 문서는 외부 API 없이 파싱과 정규화를 검증하기 위한 fixture 위치와 형식을 정의한다.

## 2. 기본 원칙

- fixture는 테스트 전용 데이터로 `tests/fixtures` 아래에 둔다.
- 원천 API 응답 형식과 비슷한 JSON 구조를 유지한다.
- fixture에는 API 키, 토큰, 개인정보 등 비밀값을 포함하지 않는다.
- fixture 기반 테스트는 외부 API 호출 없이 실행되어야 한다.

## 3. 기업마당 fixture

기업마당 지원사업 공고 fixture 위치:

```text
tests/fixtures/bizinfo/support_notices.json
```

기본 JSON 구조:

```json
{
  "response": {
    "body": {
      "items": []
    }
  }
}
```

1차 MVP에서 사용하는 원천 필드:

| 필드 | 내부 의미 |
| --- | --- |
| `pblancId` | `source_notice_id` |
| `pblancNm` | `title` |
| `jrsdInsttNm` | `organization` |
| `creatPnttm` | `posted_at` |
| `reqstEndDe` | `end_at` |
| `pblancSttusNm` | `status` |
| `pblancUrl` | `url` |
| `bsnsSumryCn` | `summary` |

## 4. 1차 확정 사항

- 기업마당 fixture는 `tests/fixtures/bizinfo/support_notices.json`에 둔다.
- fixture 기반 파싱은 `BizinfoNoticeRaw` DTO로 변환한다.
- fixture 기반 정규화는 `BizinfoNoticeRaw`를 `Notice`로 변환한다.

## 4. 나라장터 fixture

나라장터 입찰공고 fixture 위치:

```text
tests/fixtures/g2b/bid_notices.json
```

권장 형식:

- `response.header.resultCode`
- `response.header.resultMsg`
- `response.body.items`
- 각 item은 최소 아래 필드를 가진다.
  - `bidNtceNo`
  - `bidNtceOrd`
  - `bidNtceNm`
  - `dminsttNm` 또는 `ntceInsttNm`
  - `bidNtceDate`
  - `bidClseDate`
  - `bidNtceSttusNm`
  - `bidNtceDtlUrl`

기준:

- 나라장터 fixture는 `tests/fixtures/g2b/bid_notices.json`에 둔다.
- fixture 기반 파싱은 `G2BNoticeRaw` DTO로 변환한다.
- fixture 기반 정규화는 `G2BNoticeRaw`를 `Notice`로 변환한다.
- 부적격 공고는 정규화 단계에서 제외 가능해야 한다.

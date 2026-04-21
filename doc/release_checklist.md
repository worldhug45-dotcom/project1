# 릴리즈 체크리스트

이 문서는 현재 저장소를 GitHub에 반영하거나 내부 운영 버전으로 전달할 때 확인해야 할 최소 체크리스트이다.

## 1. 목적

- 현재 구현 상태와 README가 맞는지 확인한다.
- collect / export / observe / status 경로가 운영자 기준으로 실제 동작하는지 확인한다.
- GitHub 반영 전에 테스트와 수동 검증 기준을 통일한다.

## 2. 사전 확인

- [ ] `README.md`가 현재 구현 상태를 정확히 반영한다.
- [ ] `DECISIONS.md`, `TASKS.md`, `CHECKLIST.md`가 최신 상태다.
- [ ] `config/keywords.override.toml` 같은 로컬 편집 파일에 비밀값이 들어 있지 않다.
- [ ] `PROJECT1_BIZINFO_CERT_KEY`를 코드나 문서 예시에 실제 값으로 넣지 않았다.
- [ ] 작업 트리에 불필요한 임시 파일이 남아 있지 않다.

## 3. 자동 검증

- [ ] `python -m unittest discover -v`
- [ ] `python -m compileall app tests scripts`
- [ ] 테스트 실패가 없고 최근 변경 범위에 맞는 테스트가 추가되었다.

## 4. 수동 스모크 테스트

### 4-1. 상태 확인

- [ ] `.\scripts\run_status.ps1`
- [ ] 현재 `config_path`, `keyword_override_path`, `sqlite_db_path`, `export_output_dir`가 출력된다.
- [ ] 최근 `.xlsx` 경로와 최근 collect/export/observe 상태가 출력된다.

### 4-2. collect

- [ ] fixture collect

```powershell
.\scripts\run_collect.ps1 -SourceMode fixture
```

- [ ] 실제 API collect

```powershell
$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"
.\scripts\run_collect.ps1
```

- [ ] `fetched_count`, `saved_count`, `skipped_count`, `error_count`가 출력된다.
- [ ] DB 경로와 export output 경로가 출력된다.

### 4-3. export

- [ ] `.\scripts\run_export.ps1`
- [ ] `.xlsx` 파일 경로가 출력된다.
- [ ] 실제 output 디렉터리에 파일이 생성된다.

### 4-4. observe

- [ ] `.\scripts\run_observe.ps1`
- [ ] observation history / report / raw jsonl 경로가 출력된다.
- [ ] history와 report가 최신 실행 기준으로 갱신된다.

## 5. GitHub 반영 전 확인

- [ ] `git status`가 의도한 변경만 포함한다.
- [ ] 커밋 메시지가 한 번에 이해 가능하다.
- [ ] 문서/코드/테스트가 같은 범위를 설명한다.

## 6. 태그 기준

초기 내부 운영용 태그는 아래처럼 관리한다.

- 첫 운영 기준점: `v0.1.0`
- 기능 확장: `v0.2.0`, `v0.3.0`
- 버그 수정: `v0.1.1`, `v0.1.2`

태그를 만들기 전 아래를 다시 본다.

- [ ] 현재 상태가 README와 일치한다.
- [ ] 테스트와 수동 검증이 끝났다.
- [ ] 운영자가 launcher와 `status`를 기준 진입점으로 사용할 수 있다.

태그 예시:

```powershell
git tag -a v0.1.0 -m "Initial internal MVP release"
git push origin v0.1.0
```

## 7. 이번 버전 요약 템플릿

아래 템플릿으로 릴리즈 메모를 남긴다.

```text
버전:
날짜:
포함 범위:
- 기업마당 actual API collect
- SQLite 저장
- Excel export
- observation
- operator tooling

제외 범위:
- 나라장터
- all 액션 완성

검증:
- unittest discover 통과
- compileall 통과
- fixture collect / export / observe 수동 확인
```

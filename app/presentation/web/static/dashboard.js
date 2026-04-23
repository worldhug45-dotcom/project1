const statusUrl = document.body.dataset.statusUrl;
const keywordsUrl = document.body.dataset.keywordsUrl;
const settingsUrl = document.body.dataset.settingsUrl;
const keywordsCoreSaveUrl = document.body.dataset.keywordsCoreSaveUrl;
const keywordsSupportingSaveUrl = document.body.dataset.keywordsSupportingSaveUrl;
const keywordsExcludeSaveUrl = document.body.dataset.keywordsExcludeSaveUrl;
const settingsSourcesSaveUrl = document.body.dataset.settingsSourcesSaveUrl;
const settingsApiKeysSaveUrl = document.body.dataset.settingsApiKeysSaveUrl;
const healthUrl = document.body.dataset.healthUrl;
const collectUrl = document.body.dataset.collectUrl;
const exportUrl = document.body.dataset.exportUrl;
const observeUrl = document.body.dataset.observeUrl;
const langKoButton = document.getElementById("lang-ko-button");
const langEnButton = document.getElementById("lang-en-button");
const refreshButton = document.getElementById("refresh-button");
const collectButton = document.getElementById("collect-button");
const exportButton = document.getElementById("export-button");
const observeButton = document.getElementById("observe-button");
const collectStatusBadge = document.getElementById("collect-status-badge");
const exportStatusBadge = document.getElementById("export-status-badge");
const observeStatusBadge = document.getElementById("observe-status-badge");
const collectMessage = document.getElementById("collect-message");
const exportMessage = document.getElementById("export-message");
const observeMessage = document.getElementById("observe-message");
const collectSummary = document.getElementById("collect-summary");
const exportSummary = document.getElementById("export-summary");
const observeSummary = document.getElementById("observe-summary");
const errorBanner = document.getElementById("error-banner");
const updatedAt = document.getElementById("updated-at");
const readOnlyBadge = document.getElementById("read-only-badge");
const pathsGrid = document.getElementById("paths-grid");
const settingsManagementRoot = document.getElementById("settings-management-root");
const recentActions = document.getElementById("recent-actions");
const launcherList = document.getElementById("launcher-list");
const pageKicker = document.getElementById("page-kicker");
const pageHeading = document.getElementById("page-heading");
const pageSubtitle = document.getElementById("page-subtitle");
const dashboardTitle = document.getElementById("dashboard-title");
const dashboardSubtitle = document.getElementById("dashboard-subtitle");
const dashboardKeywordsCoreCount = document.getElementById("dashboard-keywords-core-count");
const dashboardKeywordsSupportingCount = document.getElementById("dashboard-keywords-supporting-count");
const dashboardKeywordsExcludeCount = document.getElementById("dashboard-keywords-exclude-count");
const dashboardKeywordsSavedAt = document.getElementById("dashboard-keywords-saved-at");
const dashboardKeywordsGroup = document.getElementById("dashboard-keywords-group");
const dashboardKeywordsTargetPath = document.getElementById("dashboard-keywords-target-path");
const dashboardHealthAppName = document.getElementById("dashboard-health-app-name");
const dashboardHealthServerTime = document.getElementById("dashboard-health-server-time");
const dashboardHealthSettingsLoaded = document.getElementById("dashboard-health-settings-loaded");
const dashboardHealthStateFile = document.getElementById("dashboard-health-state-file");
const dashboardHealthObservationHistory = document.getElementById(
  "dashboard-health-observation-history",
);
const artifactBoard = document.getElementById("artifact-board");
const healthBadge = document.getElementById("health-badge");
const healthAppName = document.getElementById("health-app-name");
const healthServerTime = document.getElementById("health-server-time");
const healthSettingsLoaded = document.getElementById("health-settings-loaded");
const healthStateFileAccessible = document.getElementById("health-state-file-accessible");
const healthObservationHistoryExists = document.getElementById("health-observation-history-exists");
const keywordsStatusBadge = document.getElementById("keywords-status-badge");
const keywordsMessage = document.getElementById("keywords-message");
const keywordsOverridePath = document.getElementById("keywords-override-path");
const keywordsOverrideExists = document.getElementById("keywords-override-exists");
const keywordsLastLoadedPath = document.getElementById("keywords-last-loaded-path");
const keywordsTotalCount = document.getElementById("keywords-total-count");
const keywordsSaveMetaSavedAt = document.getElementById("keywords-save-meta-saved-at");
const keywordsSaveMetaTargetPath = document.getElementById("keywords-save-meta-target-path");
const keywordsSaveMetaGroup = document.getElementById("keywords-save-meta-group");
const keywordsSaveMetaStatus = document.getElementById("keywords-save-meta-status");
const keywordsCoreCount = document.getElementById("keywords-core-count");
const keywordsSupportingCount = document.getElementById("keywords-supporting-count");
const keywordsExcludeCount = document.getElementById("keywords-exclude-count");
const keywordsCoreList = document.getElementById("keywords-core-list");
const keywordsSupportingList = document.getElementById("keywords-supporting-list");
const keywordsExcludeList = document.getElementById("keywords-exclude-list");
const keywordsCoreInput = document.getElementById("keywords-core-input");
const keywordsCoreAddButton = document.getElementById("keywords-core-add-button");
const keywordsCoreSaveButton = document.getElementById("keywords-core-save-button");
const keywordsCoreMessage = document.getElementById("keywords-core-message");
const keywordsSupportingInput = document.getElementById("keywords-supporting-input");
const keywordsSupportingAddButton = document.getElementById("keywords-supporting-add-button");
const keywordsSupportingSaveButton = document.getElementById("keywords-supporting-save-button");
const keywordsSupportingMessage = document.getElementById("keywords-supporting-message");
const keywordsExcludeInput = document.getElementById("keywords-exclude-input");
const keywordsExcludeAddButton = document.getElementById("keywords-exclude-add-button");
const keywordsExcludeSaveButton = document.getElementById("keywords-exclude-save-button");
const keywordsExcludeMessage = document.getElementById("keywords-exclude-message");
const LANGUAGE_STORAGE_KEY = "project1.dashboard.language";
const DEFAULT_LANGUAGE = "ko";
const SUPPORTED_LANGUAGES = new Set(["ko", "en"]);
const currentPage = document.body.dataset.page || "dashboard";
const PATH_LABEL_KEYS = {
  "Config path": "paths.labels.configPath",
  "Keywords override": "paths.labels.keywordsOverride",
  "SQLite DB": "paths.labels.sqliteDb",
  "Export output": "paths.labels.exportOutput",
  "Current source mode": "summary.sourceMode",
  "Latest exported file": "paths.labels.latestExportedFile",
  "Observation history": "paths.labels.observationHistory",
  "Observation report": "paths.labels.observationReport",
  "Observation raw JSONL": "paths.labels.observationRawJsonl",
};
const SUMMARY_LABEL_KEYS = {
  Status: "summary.status",
  "Recorded at": "summary.recordedAt",
  "Run ID": "summary.runId",
  "Observed on": "summary.observedOn",
  "Run summary": "summary.runSummary",
  "Source mode": "summary.sourceMode",
  Fetched: "summary.fetched",
  Saved: "summary.saved",
  Skipped: "summary.skipped",
  Errors: "summary.errors",
  Error: "summary.errorMessage",
  "Exported files": "summary.exportedFiles",
  "Exported file": "summary.exportedFile",
  "Exported file path": "summary.exportedFilePath",
  "Export output dir": "summary.exportOutputDir",
  "DB Path": "summary.dbPath",
  "Latest raw JSONL": "summary.latestRawJsonl",
  "Observation history": "summary.observationHistory",
  "Observation report": "summary.observationReport",
};
const ACTION_TITLE_KEYS = {
  "Recent Collect": "recentActions.collect",
  "Recent Export": "recentActions.export",
  "Recent Observe": "recentActions.observe",
};
const ARTIFACT_BOARD_TEXT = {
  ko: {
    groups: {
      export: "최근 export 결과물",
      observation: "최근 observation 결과물",
    },
    labels: {
      createdAt: "생성 시각",
      kind: "종류",
      path: "경로",
      status: "상태",
    },
    kinds: {
      export_result: "export 결과물",
      observation_report: "observation report",
      observation_raw: "raw jsonl",
    },
    actions: {
      open: "열기",
      download: "다운로드",
    },
    empty: "최근 결과물이 아직 없습니다.",
  },
  en: {
    groups: {
      export: "Recent export artifacts",
      observation: "Recent observation artifacts",
    },
    labels: {
      createdAt: "Created at",
      kind: "Kind",
      path: "Path",
      status: "Status",
    },
    kinds: {
      export_result: "Export result",
      observation_report: "Observation report",
      observation_raw: "Raw JSONL",
    },
    actions: {
      open: "Open",
      download: "Download",
    },
    empty: "No recent artifacts are available yet.",
  },
};
const SETTINGS_READONLY_TEXT = {
  ko: {
    sourceHint:
      "이번 단계에서는 source 활성화 상태와 확장 구조만 확인한다. 실제 저장과 수정은 다음 단계에서 연결한다.",
    apiKeyHint:
      "API key는 등록 여부와 마스킹 값만 확인할 수 있으며, 실제 원문은 화면에 노출하지 않는다.",
    summary: {
      sourceMode: "현재 source mode",
      enabledSources: "활성 source 요약",
      enabledCount: "활성 source 수",
      extraSources: "추가 source 수",
    },
    labels: {
      fixturePath: "Fixture path",
      apiKeyStatus: "API key 상태",
      envVar: "환경 변수",
      maskedValue: "마스킹 값",
      registered: "등록됨",
      notRegistered: "미등록",
      description: "설명",
      sourceSkeleton: "추가 source 입력 구조",
      sourceSkeletonHint:
        "향후 추가 source 등록 시 name, endpoint, api_key_env_var, description 필드를 기준으로 확장한다.",
      additionalSourceTitle: "추가 API source",
      additionalSourceHint: "추가 source가 아직 등록되지 않았다. 다음 단계에서 등록/저장 UI를 연결한다.",
      additionalApiKeyTitle: "추가 사이트 API key 슬롯",
      additionalApiKeyHint: "추가 source별 API key 관리 슬롯은 다음 단계에서 연결한다.",
      noDescription: "설명 없음",
    },
  },
  en: {
    sourceHint:
      "This step keeps source enable states and extension structure read-only. Actual save/edit flows will be connected in the next step.",
    apiKeyHint:
      "API keys are shown only as registration state plus masked values, and the raw secret is never exposed in the screen.",
    summary: {
      sourceMode: "Current source mode",
      enabledSources: "Enabled source summary",
      enabledCount: "Enabled source count",
      extraSources: "Additional source count",
    },
    labels: {
      fixturePath: "Fixture path",
      apiKeyStatus: "API key status",
      envVar: "Environment variable",
      maskedValue: "Masked value",
      registered: "registered",
      notRegistered: "not registered",
      description: "Description",
      sourceSkeleton: "Additional source input skeleton",
      sourceSkeletonHint:
        "Future source onboarding will expand around name, endpoint, api_key_env_var, and description fields.",
      additionalSourceTitle: "Additional API source",
      additionalSourceHint:
        "No extra source is registered yet. Registration and save UI will be added in the next step.",
      additionalApiKeyTitle: "Additional site API key slot",
      additionalApiKeyHint:
        "API key slots for future sources will be wired in the next step.",
      noDescription: "No description",
    },
  },
};
const LAUNCHER_LABEL_KEYS = {
  "Status Launcher": "launchers.labels.status",
  "Collect Launcher": "launchers.labels.collect",
  "Export Launcher": "launchers.labels.export",
  "Observe Launcher": "launchers.labels.observe",
  "Dashboard Launcher": "launchers.labels.dashboard",
};
const I18N = {
  ko: {
    document: { title: "크롤링 대시보드" },
    language: { label: "언어" },
    brand: {
      kicker: "PROJECT1",
      title: "크롤링 대시보드",
      subtitle: "내부 운영 솔루션",
    },
    nav: {
      dashboard: "대시보드",
      settings: "설정",
    },
    sidebar: {
      hint: "왼쪽 메뉴로 화면을 전환하고, 상단 상태 배지로 현재 운영 상태를 빠르게 확인한다.",
    },
    page: {
      dashboard: {
        kicker: "운영 대시보드",
        title: "크롤링 운영 화면",
        subtitle:
          "collect, export, observe, 키워드 운영 현황과 최근 산출물을 한눈에 정리한 메인 화면이다.",
      },
      settings: {
        kicker: "운영 설정",
        title: "설정과 운영 정보",
        subtitle:
          "health, 경로, source placeholder, API key placeholder, 키워드 패널을 설정 화면에 모아둔다.",
      },
    },
    dashboard: {
      solution: {
        kicker: "솔루션 개요",
        description:
          "collect, export, observe, keyword 관리가 가능한 내부 운영 솔루션이다.",
        pillKeywords: "KEYWORD MANAGEMENT",
        points: {
          collect: "수집",
          collectValue: "기업마당과 나라장터 collect 흐름을 재사용한다.",
          export: "산출",
          exportValue: "SQLite 저장 결과를 Excel 산출물로 연결한다.",
          observe: "관찰",
          observeValue: "관찰 로그와 raw JSONL 경로를 함께 추적한다.",
        },
      },
      keywordSummary: {
        kicker: "키워드 요약",
        title: "현재 키워드 상태",
      },
      runtime: {
        kicker: "운영 상태",
        title: "헬스 요약",
      },
      artifacts: {
        kicker: "결과물 게시판",
        title: "최근 산출물",
        hint: "최근 export 결과, observation report, raw JSONL 경로를 카드 형태로 확인한다.",
        latestExport: "최근 export 파일",
        observationReport: "관찰 리포트",
        rawJsonl: "최근 raw JSONL",
        outputDirectory: "Export 출력 경로",
        empty: "아직 표시할 최근 산출물이 없다.",
      },
    },
    settings: {
      status: {
        title: "상태 정보",
        readOnly: "READ ONLY STATUS",
      },
      sources: {
        kicker: "Source 관리",
        title: "수집 소스 구성",
        bizinfo: {
          title: "기업마당",
          description: "현재 source 설정과 연결 상태를 여기에서 관리할 예정이다.",
        },
        g2b: {
          title: "나라장터",
          description: "나라장터 source 확장과 운영 제어는 다음 단계에서 이어진다.",
        },
        future: {
          title: "추가 API Source",
          description: "새 source 추가를 위한 placeholder 영역이다.",
        },
      },
      apiKeys: {
        kicker: "API Key 관리",
        title: "연동 키 관리",
        bizinfo: {
          title: "기업마당 인증키",
          description:
            "이번 단계에서는 read-only placeholder만 제공하고, 실제 저장 기능은 다음 단계에서 구현한다.",
        },
        g2b: {
          title: "나라장터 서비스키",
          description: "환경 변수 기반 운영 구조를 유지하고, 관리 UI는 이후 단계에서 확장한다.",
        },
      },
      notes: {
        kicker: "운영 메모",
        title: "다음 단계 준비",
        item1: "키워드 편집은 현재 override 파일 기준으로 즉시 반영된다.",
        item2: "API key 저장 UI는 아직 placeholder이며, 실제 저장 기능은 다음 단계에서 확장한다.",
        item3: "source 관리 영역은 기업마당, 나라장터, 추가 API source 확장을 위한 틀을 포함한다.",
      },
    },
    health: {
      kicker: "운영 상태 스냅샷",
      title: "운영 런타임 상태",
      labels: {
        appName: "앱 이름",
        serverTime: "서버 시각",
        settingsLoaded: "설정 로드",
        stateFile: "상태 파일",
        observationHistory: "관찰 히스토리",
      },
    },
    hero: {
      eyebrow: "내부 운영자 콕핏",
      title: "크롤링 대시보드",
      subtitle:
        "현재 단계는 CLI 엔진을 기준 소스로 유지하면서, 핵심·보조·제외 키워드 편집과 최근 저장 메타데이터를 하나의 운영 화면에 함께 보여준다.",
      enabled: "COLLECT + EXPORT + OBSERVE 활성화",
      readOnly: "읽기 전용",
      hint:
        "이 화면은 health와 keywords를 읽기 전용으로 확인하고, 같은 CLI 엔진 흐름 위에서 collect, export, observe를 실행할 수 있다.",
    },
    buttons: {
      refreshStatus: "상태 새로고침",
      add: "추가",
      save: "저장",
      remove: "삭제",
      runCollect: "Collect 실행",
      runExport: "Export 실행",
      runObserve: "Observe 실행",
    },
    meta: {
      updated: "스냅샷 갱신 시각",
      mode: "모드",
      modeValue: "웹 health + keywords + collect + export + observe + 공용 status",
      scope: "범위",
      scopeValue:
        "현재 경로와 최근 실행 요약을 유지하면서 health, keywords, collect, export, observe를 함께 제어한다",
    },
    keywords: {
      kicker: "키워드 스냅샷",
      title: "키워드 패널",
      message:
        "대시보드는 현재 설정과 override 구조를 기준으로 적용 중인 키워드 세트를 읽어온다. 이 단계에서는 core, supporting, exclude를 모두 수정할 수 있다.",
      meta: {
        overridePath: "Override 경로",
        overrideFile: "Override 파일",
        lastLoadedFrom: "마지막 로드 경로",
        totalKeywords: "총 키워드 수",
        lastSavedAt: "마지막 저장 시각",
        saveTarget: "저장 대상 파일",
        changedGroup: "최근 변경 그룹",
        lastSaveStatus: "마지막 저장 상태",
      },
      groups: {
        core: {
          title: "핵심",
          inputLabel: "핵심 키워드",
          placeholder: "핵심 키워드 작성란",
          hint: "핵심 키워드 작성란",
          message: "",
          empty: "현재 draft에 핵심 키워드가 없다",
          unavailable: "키워드 스냅샷을 사용할 수 없어 핵심 키워드 편집이 비활성화되었다.",
          addEmpty: "추가 전에 비어 있지 않은 핵심 키워드를 입력해 주세요.",
          duplicate: "\"{keyword}\" 는 이미 핵심 키워드 목록에 있다.",
          dirty: "저장되지 않은 핵심 키워드 변경이 준비되었다. override 파일에 반영하려면 저장하세요.",
          saving: "핵심 키워드를 override 파일에 저장하는 중...",
          saveUnavailable: "키워드 스냅샷을 사용할 수 없어 지금은 핵심 키워드를 저장할 수 없다.",
          mustRemain: "저장하려면 핵심 키워드가 최소 1개는 남아 있어야 한다.",
          saved: "핵심 키워드를 저장했다.",
          saveFailed: "핵심 키워드를 저장할 수 없다.",
        },
        supporting: {
          title: "보조",
          inputLabel: "보조 키워드",
          placeholder: "보조 키워드 작성란",
          hint: "보조 키워드 작성란",
          message: "",
          empty: "현재 draft에 보조 키워드가 없다",
          unavailable: "키워드 스냅샷을 사용할 수 없어 보조 키워드 편집이 비활성화되었다.",
          addEmpty: "추가 전에 비어 있지 않은 보조 키워드를 입력해 주세요.",
          duplicate: "\"{keyword}\" 는 이미 보조 키워드 목록에 있다.",
          dirty: "저장되지 않은 보조 키워드 변경이 준비되었다. override 파일에 반영하려면 저장하세요.",
          saving: "보조 키워드를 override 파일에 저장하는 중...",
          saveUnavailable: "키워드 스냅샷을 사용할 수 없어 지금은 보조 키워드를 저장할 수 없다.",
          mustRemain: "저장하려면 보조 키워드가 최소 1개는 남아 있어야 한다.",
          saved: "보조 키워드를 저장했다.",
          saveFailed: "보조 키워드를 저장할 수 없다.",
        },
        exclude: {
          title: "제외",
          inputLabel: "제외 키워드",
          placeholder: "제외 키워드 작성란",
          hint: "제외 키워드 작성란",
          message: "",
          empty: "현재 draft에 제외 키워드가 없다",
          unavailable: "키워드 스냅샷을 사용할 수 없어 제외 키워드 편집이 비활성화되었다.",
          addEmpty: "추가 전에 비어 있지 않은 제외 키워드를 입력해 주세요.",
          duplicate: "\"{keyword}\" 는 이미 제외 키워드 목록에 있다.",
          dirty: "저장되지 않은 제외 키워드 변경이 준비되었다. override 파일에 반영하려면 저장하세요.",
          saving: "제외 키워드를 override 파일에 저장하는 중...",
          saveUnavailable: "키워드 스냅샷을 사용할 수 없어 지금은 제외 키워드를 저장할 수 없다.",
          mustRemain: "저장하려면 제외 키워드가 최소 1개는 남아 있어야 한다.",
          saved: "제외 키워드를 저장했다.",
          saveFailed: "제외 키워드를 저장할 수 없다.",
        },
      },
    },
    controls: {
      singleRun: "단일 실행",
      collect: {
        kicker: "Collect 제어",
        hint: "대시보드는 기존 manual collect 흐름을 재사용하며, 같은 서버 프로세스 안에서 중복 실행을 막는다.",
        running: "Collect가 백그라운드에서 실행 중이다. 끝날 때까지 중복 요청은 막힌다.",
        finished: "Collect가 완료되었다. 공용 status 스냅샷도 함께 갱신되었다.",
        default: "버튼을 한 번만 사용하면 된다. 대시보드는 기존 manual collect 흐름을 그대로 재사용한다.",
        requestFailedPrefix: "Collect 요청 실패: ",
      },
      export: {
        kicker: "Export 제어",
        hint: "대시보드는 기존 manual export 흐름을 재사용하며, 결과 요약을 이 패널 안에 유지한다.",
        running: "Export가 백그라운드에서 실행 중이다. 끝날 때까지 중복 요청은 막힌다.",
        finished: "Export가 완료되었다. 최신 export 파일 경로도 함께 갱신되었다.",
        default: "버튼을 한 번만 사용하면 된다. 대시보드는 기존 manual export 흐름을 그대로 재사용한다.",
        requestFailedPrefix: "Export 요청 실패: ",
      },
      observe: {
        kicker: "Observe 제어",
        hint: "대시보드는 기존 manual observe 흐름을 재사용하며, 관찰 요약을 이 패널 안에 유지한다.",
        running: "Observe가 백그라운드에서 실행 중이다. 끝날 때까지 중복 요청은 막힌다.",
        finished: "Observe가 완료되었다. 최신 관찰 경로가 공용 status 스냅샷에 반영되었다.",
        default: "버튼을 한 번만 사용하면 된다. 대시보드는 기존 manual observe 흐름을 그대로 재사용한다.",
        requestFailedPrefix: "Observe 요청 실패: ",
      },
    },
    rules: {
      kicker: "Stage 11 규칙",
      title: "현재 경계",
      item1: "<code>/health</code>는 별도로 조회되며, 대시보드 상단 read-only badge만 갱신한다.",
      item2: "<code>/api/keywords</code>는 공용 키워드 스냅샷과 최신 저장 메타데이터를 함께 반환한다.",
      item3: "<code>/api/keywords/core</code>, <code>/api/keywords/supporting</code>, <code>/api/keywords/exclude</code>는 각자 자기 그룹만 저장한다.",
      item4: "이 단계에서는 collect, export, observe를 웹 화면에서 직접 제어할 수 있다.",
      item5: "<code>manual_run.py collect</code> 경로를 그대로 재사용하며, 새로운 엔진은 추가하지 않는다.",
      item6: "<code>manual_run.py export</code> 경로를 그대로 재사용한다.",
      item7: "<code>manual_run.py observe</code> 경로를 그대로 재사용한다.",
      item8: "core, supporting, exclude 키워드는 각자 패널에서 수정할 수 있다.",
      item9: "최근 저장 상태, 시각, 대상 파일, 변경 그룹은 override 파일 옆의 작은 메타 파일을 통해 새로고침 후에도 유지된다.",
      item10: "같은 action이 이미 실행 중이면, 새 실행 대신 현재 running 상태를 그대로 반환한다.",
    },
    paths: {
      kicker: "활성 런타임 경로",
      title: "현재 작업 경로",
      labels: {
        configPath: "설정 경로",
        keywordsOverride: "키워드 override",
        sqliteDb: "SQLite DB",
        exportOutput: "Export 출력 경로",
        latestExportedFile: "최근 export 파일",
        observationHistory: "관찰 히스토리",
        observationReport: "관찰 리포트",
        observationRawJsonl: "관찰 raw JSONL",
      },
    },
    notes: {
      kicker: "운영자 메모",
      title: "공용 스냅샷",
      item1: "CLI <code>status</code>와 web <code>status</code>는 같은 operator snapshot을 공유한다.",
      item2: "collect가 끝나면 <code>GET /api/status</code>가 최신 collect 결과를 반영하되, 나머지 화면은 그대로 유지한다.",
      item3: "export가 끝나면 최신 export 파일 경로와 최근 export 상태가 공용 스냅샷에 반영된다.",
      item4: "observe가 끝나면 observation history, report, raw JSONL 경로가 공용 스냅샷에 반영된다.",
    },
    recent: { kicker: "최근 활동", title: "Collect / Export / Observe" },
    launchers: {
      kicker: "런처",
      title: "빠른 실행 경로",
      labels: {
        status: "상태 런처",
        collect: "Collect 런처",
        export: "Export 런처",
        observe: "Observe 런처",
        dashboard: "대시보드 런처",
      },
    },
    recentActions: {
      collect: "최근 Collect",
      export: "최근 Export",
      observe: "최근 Observe",
    },
    summary: {
      status: "상태",
      recordedAt: "기록 시각",
      runId: "실행 ID",
      observedOn: "관찰 날짜",
      runSummary: "실행 요약",
      sourceMode: "소스 모드",
      fetched: "조회 건수",
      saved: "저장 건수",
      skipped: "제외 건수",
      errors: "오류 건수",
      errorMessage: "오류 메시지",
      exportedFiles: "Export 파일 수",
      exportedFile: "Export 파일",
      exportedFilePath: "Export 파일 경로",
      exportOutputDir: "Export 출력 경로",
      dbPath: "DB 경로",
      observationHistory: "관찰 히스토리",
      observationReport: "관찰 리포트",
      latestRawJsonl: "최근 raw JSONL",
    },
    sourceMode: {
      fixture: "fixture",
      api: "api",
    },
    keywordGroup: {
      core: "핵심",
      supporting: "보조",
      exclude: "제외",
      not_available: "정보 없음",
    },
    errors: {
      statusFetchFailed: "상태 조회 실패: ",
      keywordsUnavailable: "키워드 스냅샷을 불러올 수 없다.",
    },
    status: {
      ok: "정상",
      degraded: "주의",
      loading: "불러오는 중",
      loadingLong: "불러오는 중...",
      ready: "준비됨",
      idle: "대기",
      running: "실행 중",
      finished: "완료",
      failed: "실패",
      success: "성공",
      error: "오류",
      config_error: "설정 오류",
      available: "있음",
      accessible: "접근 가능",
      loaded: "로드됨",
      present: "있음",
      missing: "없음",
      not_available: "정보 없음",
      not_loaded: "미로드",
      not_accessible: "접근 불가",
    },
  },
  en: {
    document: { title: "Crawling Dashboard" },
    language: { label: "Language" },
    brand: {
      kicker: "PROJECT1",
      title: "Crawling Dashboard",
      subtitle: "Internal Operator Solution",
    },
    nav: {
      dashboard: "Dashboard",
      settings: "Settings",
    },
    sidebar: {
      hint: "Switch pages from the left menu and use the top health badge to confirm the current operator state.",
    },
    page: {
      dashboard: {
        kicker: "Operator Dashboard",
        title: "Crawling Operations",
        subtitle:
          "The main screen brings collect, export, observe, keyword operations, and the latest artifacts into one operator view.",
      },
      settings: {
        kicker: "Operator Settings",
        title: "Settings and Runtime Info",
        subtitle:
          "Health, paths, source placeholders, API key placeholders, and the keyword panel are grouped into the settings screen.",
      },
    },
    dashboard: {
      solution: {
        kicker: "Solution Overview",
        description:
          "An internal operator solution that can run collect, export, observe, and keyword management.",
        pillKeywords: "KEYWORD MANAGEMENT",
        points: {
          collect: "Collect",
          collectValue: "Reuses the Bizinfo and G2B collect flows.",
          export: "Export",
          exportValue: "Connects SQLite results to Excel output artifacts.",
          observe: "Observe",
          observeValue: "Tracks observation logs together with raw JSONL paths.",
        },
      },
      keywordSummary: {
        kicker: "Keyword Summary",
        title: "Current Keyword State",
      },
      runtime: {
        kicker: "Runtime Health",
        title: "Health Summary",
      },
      artifacts: {
        kicker: "Artifact Board",
        title: "Recent Artifacts",
        hint: "Review the latest export file, observation report, and raw JSONL paths as operator cards.",
        latestExport: "Latest exported file",
        observationReport: "Observation report",
        rawJsonl: "Latest raw JSONL",
        outputDirectory: "Export output dir",
        empty: "There are no recent artifacts to show yet.",
      },
    },
    settings: {
      status: {
        title: "Runtime Status",
        readOnly: "READ ONLY STATUS",
      },
      sources: {
        kicker: "Source Management",
        title: "Collect Source Configuration",
        bizinfo: {
          title: "Bizinfo",
          description: "The source settings and connection state will be managed here in a later step.",
        },
        g2b: {
          title: "G2B",
          description: "The G2B source expansion and runtime control will continue in the next step.",
        },
        future: {
          title: "Future API Source",
          description: "Placeholder area for additional source onboarding.",
        },
      },
      apiKeys: {
        kicker: "API Key Management",
        title: "Integration Key Management",
        bizinfo: {
          title: "Bizinfo cert key",
          description:
            "This step keeps a read-only placeholder only. Real save/edit capability will be added later.",
        },
        g2b: {
          title: "G2B service key",
          description: "The environment-variable-driven structure stays in place and a management UI can be added later.",
        },
      },
      notes: {
        kicker: "Operator Notes",
        title: "Next Step Prep",
        item1: "Keyword edits are applied immediately through the current override file flow.",
        item2: "The API key UI is still a placeholder. Real save capability can be added in the next step.",
        item3: "The source management area keeps placeholders for Bizinfo, G2B, and future API sources.",
      },
    },
    health: {
      kicker: "Health Snapshot",
      title: "Operator Runtime Health",
      labels: {
        appName: "App name",
        serverTime: "Server time",
        settingsLoaded: "Settings loaded",
        stateFile: "State file",
        observationHistory: "Observation history",
      },
    },
    hero: {
      eyebrow: "Internal Operator Cockpit",
      title: "Crawling Dashboard",
      subtitle:
        "Stage 11 keeps the CLI engine as the source of truth, allows core, supporting, and exclude keyword editing, and adds recent keyword save metadata to the shared operator dashboard.",
      enabled: "COLLECT + EXPORT + OBSERVE ENABLED",
      readOnly: "READ ONLY",
      hint:
        "This surface can show read-only health and keywords, then trigger collect, export, and observe while keeping the CLI engine as the shared source of truth.",
    },
    buttons: {
      refreshStatus: "Refresh Status",
      add: "Add",
      save: "Save",
      remove: "Remove",
      runCollect: "Run Collect",
      runExport: "Run Export",
      runObserve: "Run Observe",
    },
    meta: {
      updated: "Snapshot Updated",
      mode: "Mode",
      modeValue: "Web health + keywords + collect + export + observe + shared status",
      scope: "Scope",
      scopeValue:
        "Read-only health and keywords plus collect, export, and observe control with current paths and latest action summaries",
    },
    keywords: {
      kicker: "Keyword Snapshot",
      title: "Keyword Panel",
      message:
        "The dashboard shows the currently effective keyword set after config and override resolution. Core, supporting, and exclude keywords can all be edited in this stage.",
      meta: {
        overridePath: "Override path",
        overrideFile: "Override file",
        lastLoadedFrom: "Last loaded from",
        totalKeywords: "Total keywords",
        lastSavedAt: "Last saved at",
        saveTarget: "Save target",
        changedGroup: "Recent changed group",
        lastSaveStatus: "Last save status",
      },
      groups: {
        core: {
          title: "Core",
          inputLabel: "Core keyword",
          placeholder: "Core keyword field",
          hint: "Core keyword field",
          message: "",
          empty: "No core keywords in the current draft",
          unavailable: "Keyword snapshot is unavailable. Core keyword editing is disabled.",
          addEmpty: "Enter a non-empty core keyword before adding it.",
          duplicate: "\"{keyword}\" is already in the core keyword list.",
          dirty: "Unsaved core keyword changes are ready. Save to apply them to the override file.",
          saving: "Saving core keywords to the override file...",
          saveUnavailable: "Keyword snapshot is unavailable, so core keywords cannot be saved right now.",
          mustRemain: "At least one core keyword must remain before saving.",
          saved: "Core keywords saved.",
          saveFailed: "Core keywords could not be saved.",
        },
        supporting: {
          title: "Supporting",
          inputLabel: "Supporting keyword",
          placeholder: "Supporting keyword field",
          hint: "Supporting keyword field",
          message: "",
          empty: "No supporting keywords in the current draft",
          unavailable: "Keyword snapshot is unavailable. Supporting keyword editing is disabled.",
          addEmpty: "Enter a non-empty supporting keyword before adding it.",
          duplicate: "\"{keyword}\" is already in the supporting keyword list.",
          dirty: "Unsaved supporting keyword changes are ready. Save to apply them to the override file.",
          saving: "Saving supporting keywords to the override file...",
          saveUnavailable: "Keyword snapshot is unavailable, so supporting keywords cannot be saved right now.",
          mustRemain: "At least one supporting keyword must remain before saving.",
          saved: "Supporting keywords saved.",
          saveFailed: "Supporting keywords could not be saved.",
        },
        exclude: {
          title: "Exclude",
          inputLabel: "Exclude keyword",
          placeholder: "Exclude keyword field",
          hint: "Exclude keyword field",
          message: "",
          empty: "No exclude keywords in the current draft",
          unavailable: "Keyword snapshot is unavailable. Exclude keyword editing is disabled.",
          addEmpty: "Enter a non-empty exclude keyword before adding it.",
          duplicate: "\"{keyword}\" is already in the exclude keyword list.",
          dirty: "Unsaved exclude keyword changes are ready. Save to apply them to the override file.",
          saving: "Saving exclude keywords to the override file...",
          saveUnavailable: "Keyword snapshot is unavailable, so exclude keywords cannot be saved right now.",
          mustRemain: "At least one exclude keyword must remain before saving.",
          saved: "Exclude keywords saved.",
          saveFailed: "Exclude keywords could not be saved.",
        },
      },
    },
    controls: {
      singleRun: "Single Run Execution",
      collect: {
        kicker: "Collect Control",
        hint: "The dashboard reuses the existing manual collect flow and blocks duplicate runs in the same server process.",
        running: "Collect is running in the background. Duplicate requests are blocked until it finishes.",
        finished: "Collect finished. The shared status snapshot has been refreshed.",
        default: "Use the button once. The dashboard reuses the existing manual collect flow.",
        requestFailedPrefix: "Collect request failed: ",
      },
      export: {
        kicker: "Export Control",
        hint: "The dashboard reuses the existing manual export flow and keeps the result summary in its own panel.",
        running: "Export is running in the background. Duplicate export requests are blocked until it finishes.",
        finished: "Export finished. The latest exported file path has been refreshed.",
        default: "Use the button once. The dashboard reuses the existing manual export flow.",
        requestFailedPrefix: "Export request failed: ",
      },
      observe: {
        kicker: "Observe Control",
        hint: "The dashboard reuses the existing manual observe flow and keeps the observation summary in its own panel.",
        running: "Observe is running in the background. Duplicate observe requests are blocked until it finishes.",
        finished: "Observe finished. The shared status snapshot has been refreshed with the latest observation paths.",
        default: "Use the button once. The dashboard reuses the existing manual observe flow.",
        requestFailedPrefix: "Observe request failed: ",
      },
    },
    rules: {
      kicker: "Stage 11 Rules",
      title: "Current Boundaries",
      item1: "<code>/health</code> is queried separately and only powers the read-only badge at the top of the dashboard.",
      item2: "<code>/api/keywords</code> now returns the shared keyword snapshot plus the latest keyword save metadata.",
      item3: "<code>/api/keywords/core</code>, <code>/api/keywords/supporting</code>, and <code>/api/keywords/exclude</code> each save only their own keyword group changes.",
      item4: "Collect, export, and observe are controllable from the web shell in this stage.",
      item5: "The same <code>manual_run.py collect</code> path is reused instead of introducing a new engine.",
      item6: "The same <code>manual_run.py export</code> path is reused for export.",
      item7: "The same <code>manual_run.py observe</code> path is reused for observation runs.",
      item8: "Core, supporting, and exclude keywords can all be edited from their own panels in the dashboard.",
      item9: "Recent keyword save status, time, target file, and changed group survive page refresh through a tiny metadata file next to the override file.",
      item10: "If the same action is already active, the dashboard returns the current running state instead of starting another one.",
    },
    paths: {
      kicker: "Active Runtime Paths",
      title: "Current Working Paths",
      labels: {
        configPath: "Config path",
        keywordsOverride: "Keywords override",
        sqliteDb: "SQLite DB",
        exportOutput: "Export output",
        latestExportedFile: "Latest exported file",
        observationHistory: "Observation history",
        observationReport: "Observation report",
        observationRawJsonl: "Observation raw JSONL",
      },
    },
    notes: {
      kicker: "Operator Notes",
      title: "Shared Snapshot",
      item1: "CLI <code>status</code> and web <code>status</code> still share the same operator snapshot.",
      item2: "After collect finishes, <code>GET /api/status</code> reflects the latest collect result without replacing the rest of the dashboard.",
      item3: "After export finishes, the latest exported file path and recent export status are refreshed in the shared snapshot.",
      item4: "After observe finishes, the observation history, report, and raw JSONL paths are refreshed in the shared snapshot.",
    },
    recent: { kicker: "Recent Activity", title: "Collect / Export / Observe" },
    launchers: {
      kicker: "Launchers",
      title: "Quick Entry Points",
      labels: {
        status: "Status Launcher",
        collect: "Collect Launcher",
        export: "Export Launcher",
        observe: "Observe Launcher",
        dashboard: "Dashboard Launcher",
      },
    },
    recentActions: {
      collect: "Recent Collect",
      export: "Recent Export",
      observe: "Recent Observe",
    },
    summary: {
      status: "Status",
      recordedAt: "Recorded at",
      runId: "Run ID",
      observedOn: "Observed on",
      runSummary: "Run summary",
      sourceMode: "Source mode",
      fetched: "Fetched",
      saved: "Saved",
      skipped: "Skipped",
      errors: "Errors",
      errorMessage: "Error message",
      exportedFiles: "Exported files",
      exportedFile: "Exported file",
      exportedFilePath: "Exported file path",
      exportOutputDir: "Export output dir",
      dbPath: "DB Path",
      observationHistory: "Observation history",
      observationReport: "Observation report",
      latestRawJsonl: "Latest raw JSONL",
    },
    sourceMode: {
      fixture: "fixture",
      api: "api",
    },
    keywordGroup: {
      core: "core",
      supporting: "supporting",
      exclude: "exclude",
      not_available: "not available",
    },
    errors: {
      statusFetchFailed: "Status fetch failed: ",
      keywordsUnavailable: "Keyword snapshot could not be loaded.",
    },
    status: {
      ok: "ok",
      degraded: "degraded",
      loading: "loading",
      loadingLong: "Loading...",
      ready: "ready",
      idle: "idle",
      running: "running",
      finished: "finished",
      failed: "failed",
      success: "success",
      error: "error",
      config_error: "config error",
      available: "available",
      accessible: "accessible",
      loaded: "loaded",
      present: "present",
      missing: "missing",
      not_available: "not available",
      not_loaded: "not loaded",
      not_accessible: "not accessible",
    },
  },
};
const SETTINGS_UI_TEXT = {
  ko: {
    sources: {
      kicker: "Source 관리",
      title: "수집 소스 구성",
      message:
        "기업마당과 나라장터 활성 상태를 관리하고, 다음 단계에서 붙일 추가 API source 등록 구조도 함께 저장한다.",
      enabledToggle: "활성화",
      sourceModeLabel: "Source mode",
      sourceModeApi: "api",
      sourceModeFixture: "fixture",
      endpointLabel: "Endpoint",
      apiKeyLabel: "API key",
      saveButton: "소스 설정 저장",
      saved: "source 설정을 저장했습니다.",
      saving: "source 설정을 저장하고 있습니다...",
      mustKeepOne: "적어도 하나의 기본 source는 활성 상태를 유지해야 합니다.",
      extraEmpty: "아직 등록된 추가 API source가 없습니다.",
      extraKicker: "추가 Source 등록",
      extraTitle: "추가 API Source",
      extraHint:
        "다음 단계에서 backend source adapter를 붙일 수 있도록 이름, endpoint, API key env var 구조를 먼저 저장한다.",
      extraNameLabel: "Source 이름",
      extraEndpointLabel: "API endpoint",
      extraEnvVarLabel: "API key env var",
      extraDescriptionLabel: "설명",
      extraNamePlaceholder: "Source 이름",
      extraEndpointPlaceholder: "API endpoint",
      extraEnvVarPlaceholder: "PROJECT1_NEW_SOURCE_API_KEY",
      extraDescriptionPlaceholder: "설명",
      extraAddButton: "추가 source 등록",
      addNameRequired: "추가 source 이름을 입력해 주세요.",
      addEndpointRequired: "추가 source endpoint를 입력해 주세요.",
      addEnvVarRequired: "API key env var를 입력해 주세요.",
      addEnvVarInvalid: "API key env var는 환경 변수 이름 형식이어야 합니다.",
      addDuplicate: "{name} source가 이미 초안에 있습니다.",
      bizinfoCardTitle: "기업마당 수집 소스",
      g2bCardTitle: "나라장터 수집 소스",
    },
    apiKeys: {
      kicker: "API Key 관리",
      title: "연동 키 관리",
      message:
        "민감정보는 마스킹해서 표시하고, 새 값을 입력한 항목만 config/.env.local 기준으로 안전하게 갱신한다.",
      maskedLabel: "현재 마스킹 값",
      envVarLabel: "환경 변수",
      saveButton: "API key 저장",
      saved: "API key 설정을 저장했습니다.",
      saving: "API key 설정을 저장하고 있습니다...",
      empty: "변경할 API key 값을 하나 이상 입력해 주세요.",
      bizinfoTitle: "기업마당 인증키",
      g2bTitle: "나라장터 서비스키",
      bizinfoCardTitle: "기업마당 API key",
      g2bCardTitle: "나라장터 API key",
      bizinfoPlaceholder: "새 기업마당 인증키 입력 시에만 변경",
      g2bPlaceholder: "새 나라장터 서비스키 입력 시에만 변경",
    },
    saveMeta: {
      savedAt: "마지막 저장 시각",
      targetPath: "저장 대상 파일",
      changedSection: "최근 변경 영역",
      status: "마지막 저장 상태",
      notAvailable: "정보 없음",
      sectionSources: "source 설정",
      sectionApiKeys: "API key",
    },
    labels: {
      enabled: "활성",
      disabled: "비활성",
      configured: "설정됨",
      notConfigured: "미설정",
      remove: "삭제",
    },
  },
  en: {
    sources: {
      kicker: "Source Management",
      title: "Collect Source Configuration",
      message:
        "Manage Bizinfo and G2B enable states here, and persist a draft structure for onboarding future API sources.",
      enabledToggle: "Enabled",
      sourceModeLabel: "Source mode",
      sourceModeApi: "api",
      sourceModeFixture: "fixture",
      endpointLabel: "Endpoint",
      apiKeyLabel: "API key",
      saveButton: "Save source settings",
      saved: "Source settings were saved.",
      saving: "Saving source settings...",
      feedbackSaveFailed: "Source settings could not be saved.",
      mustKeepOne: "At least one built-in source must remain enabled.",
      extraEmpty: "There are no additional API sources registered yet.",
      extraKicker: "Additional Source Registration",
      extraTitle: "Additional API Source",
      extraHint:
        "Persist the name, endpoint, and API key env var contract first so a backend source adapter can be attached later.",
      extraNameLabel: "Source name",
      extraEndpointLabel: "API endpoint",
      extraEnvVarLabel: "API key env var",
      extraDescriptionLabel: "Description",
      extraNamePlaceholder: "Source name",
      extraEndpointPlaceholder: "API endpoint",
      extraEnvVarPlaceholder: "PROJECT1_NEW_SOURCE_API_KEY",
      extraDescriptionPlaceholder: "Description",
      extraAddButton: "Register extra source",
      addNameRequired: "Enter an extra source name.",
      addEndpointRequired: "Enter an extra source endpoint.",
      addEnvVarRequired: "Enter an API key env var.",
      addEnvVarInvalid: "The API key env var must look like an environment variable name.",
      addDuplicate: "{name} is already present in the draft.",
      bizinfoCardTitle: "Bizinfo collect source",
      g2bCardTitle: "G2B collect source",
    },
    apiKeys: {
      kicker: "API Key Management",
      title: "Integration Key Management",
      message:
        "Sensitive values stay masked, and only fields with a newly entered value are safely persisted into config/.env.local.",
      maskedLabel: "Current masked value",
      envVarLabel: "Environment variable",
      saveButton: "Save API keys",
      saved: "API key settings were saved.",
      saving: "Saving API key settings...",
      empty: "Enter at least one API key value to update.",
      feedbackSaveFailed: "API key settings could not be saved.",
      bizinfoTitle: "Bizinfo cert key",
      g2bTitle: "G2B service key",
      bizinfoCardTitle: "Bizinfo API key",
      g2bCardTitle: "G2B API key",
      bizinfoPlaceholder: "Only update when a new Bizinfo key is entered",
      g2bPlaceholder: "Only update when a new G2B key is entered",
    },
    saveMeta: {
      savedAt: "Last saved at",
      targetPath: "Target file",
      changedSection: "Last changed section",
      status: "Last save status",
      notAvailable: "not available",
      sectionSources: "source settings",
      sectionApiKeys: "API key",
    },
    labels: {
      enabled: "enabled",
      disabled: "disabled",
      configured: "configured",
      notConfigured: "not configured",
      remove: "Remove",
    },
  },
};
let pollingHandle = null;
let currentLanguage = loadStoredLanguage();
let currentKeywordsStatus = "loading";
let lastStatusPayload = null;
let lastHealthPayload = null;
let lastKeywordsPayload = null;
let lastSettingsPayload = null;
let coreDraftKeywords = [];
let coreDraftDirty = false;
let coreSaveInFlight = false;
let supportingDraftKeywords = [];
let supportingDraftDirty = false;
let supportingSaveInFlight = false;
let excludeDraftKeywords = [];
let excludeDraftDirty = false;
let excludeSaveInFlight = false;
let settingsSourceDraft = {
  bizinfoEnabled: false,
  g2bEnabled: false,
  sourceMode: "api",
  extraSources: [],
};
let settingsExtraSourceForm = {
  name: "",
  endpoint: "",
  api_key_env_var: "",
  description: "",
};
let settingsApiKeyDraft = {
  bizinfo: "",
  g2b: "",
};
let settingsSourceDraftDirty = false;
let settingsSourceSaveInFlight = false;
let settingsApiKeySaveInFlight = false;
let coreFeedback = {
  tone: "neutral",
  key: "keywords.groups.core.message",
};
let supportingFeedback = {
  tone: "neutral",
  key: "keywords.groups.supporting.message",
};
let excludeFeedback = {
  tone: "neutral",
  key: "keywords.groups.exclude.message",
};
let settingsSourceFeedback = {
  tone: "neutral",
  key: "settings.sources.message",
};
let settingsApiKeysFeedback = {
  tone: "neutral",
  key: "settings.apiKeys.message",
};

function loadStoredLanguage() {
  try {
    const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (saved && SUPPORTED_LANGUAGES.has(saved)) {
      return saved;
    }
  } catch (_error) {
    return DEFAULT_LANGUAGE;
  }
  return DEFAULT_LANGUAGE;
}

function setLanguage(language, options = {}) {
  if (!SUPPORTED_LANGUAGES.has(language)) {
    return;
  }
  currentLanguage = language;
  document.documentElement.lang = language;
  if (options.persist !== false) {
    try {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch (_error) {
      // Ignore localStorage failures and keep the in-memory language state.
    }
  }
  updateLanguageButtons();
  applyStaticTranslations();
  rerenderSnapshots();
}

function updateLanguageButtons() {
  langKoButton.classList.toggle("is-active", currentLanguage === "ko");
  langEnButton.classList.toggle("is-active", currentLanguage === "en");
  langKoButton.setAttribute("aria-pressed", currentLanguage === "ko" ? "true" : "false");
  langEnButton.setAttribute("aria-pressed", currentLanguage === "en" ? "true" : "false");
}

function applyStaticTranslations() {
  document.title = t("document.title");
  for (const element of document.querySelectorAll("[data-i18n]")) {
    const key = element.dataset.i18n;
    element.textContent = t(key);
  }
  for (const element of document.querySelectorAll("[data-i18n-html]")) {
    const key = element.dataset.i18nHtml;
    element.innerHTML = t(key);
  }
  for (const element of document.querySelectorAll("[data-i18n-placeholder]")) {
    const key = element.dataset.i18nPlaceholder;
    element.setAttribute("placeholder", t(key));
  }
  applyPageTranslations();
}

function applyPageTranslations() {
  const pageKey = currentPage === "settings" ? "page.settings" : "page.dashboard";
  pageKicker.textContent = t(`${pageKey}.kicker`);
  pageHeading.textContent = t(`${pageKey}.title`);
  pageSubtitle.textContent = t(`${pageKey}.subtitle`);
}

function rerenderSnapshots() {
  if (lastStatusPayload) {
    renderDashboard(lastStatusPayload);
  }
  if (lastHealthPayload) {
    renderHealth(lastHealthPayload);
  }
  if (lastKeywordsPayload) {
    renderKeywords(lastKeywordsPayload);
  }
  if (lastSettingsPayload) {
    renderSettings(lastSettingsPayload);
  }
}

function t(key, params = {}) {
  const value = lookupTranslation(currentLanguage, key) ?? lookupTranslation("en", key) ?? key;
  if (typeof value !== "string") {
    return key;
  }
  return Object.entries(params).reduce(
    (text, [paramKey, paramValue]) => text.replaceAll(`{${paramKey}}`, String(paramValue)),
    value,
  );
}

function settingsText(key, params = {}) {
  const value = lookupSettingsText(currentLanguage, key)
    ?? lookupSettingsText("en", key)
    ?? key;
  if (typeof value !== "string") {
    return key;
  }
  return Object.entries(params).reduce(
    (text, [paramKey, paramValue]) => text.replaceAll(`{${paramKey}}`, String(paramValue)),
    value,
  );
}

function lookupTranslation(language, key) {
  return key.split(".").reduce((currentValue, segment) => {
    if (currentValue && typeof currentValue === "object" && segment in currentValue) {
      return currentValue[segment];
    }
    return null;
  }, I18N[language]);
}

function lookupSettingsText(language, key) {
  return key.split(".").reduce((currentValue, segment) => {
    if (currentValue && typeof currentValue === "object" && segment in currentValue) {
      return currentValue[segment];
    }
    return null;
  }, SETTINGS_UI_TEXT[language]);
}

function translateStatus(status) {
  const normalized = String(status || "not_available").replaceAll(" ", "_");
  const translated = lookupTranslation(currentLanguage, `status.${normalized}`);
  return typeof translated === "string" ? translated : String(status || t("status.not_available"));
}

function translatePathLabel(label) {
  const key = PATH_LABEL_KEYS[label];
  return key ? t(key) : label;
}

function translateSummaryLabel(label) {
  const key = SUMMARY_LABEL_KEYS[label];
  return key ? t(key) : label;
}

function translateActionTitle(title) {
  const key = ACTION_TITLE_KEYS[title];
  return key ? t(key) : title;
}

function translateLauncherLabel(label) {
  const key = LAUNCHER_LABEL_KEYS[label];
  return key ? t(key) : label;
}

function translateSourceMode(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const translated = lookupTranslation(currentLanguage, `sourceMode.${normalized}`);
  return typeof translated === "string" ? translated : String(value || t("status.not_available"));
}

function translateSummaryValue(label, value) {
  if (label === "Status" || label === "Run summary") {
    return translateStatus(value);
  }
  if (label === "Source mode") {
    return translateSourceMode(value);
  }
  return translateDisplayValue(value);
}

function translateKeywordGroup(group) {
  const normalized = String(group || "not_available").replaceAll(" ", "_");
  const translated = lookupTranslation(currentLanguage, `keywordGroup.${normalized}`);
  return typeof translated === "string" ? translated : String(group || t("status.not_available"));
}

function translateDisplayValue(value) {
  const normalized = String(value || "").trim().toLowerCase().replaceAll(" ", "_");
  if (normalized in (I18N.en.status || {})) {
    return translateStatus(normalized);
  }
  return String(value);
}

function artifactText(key) {
  const value = lookupArtifactText(currentLanguage, key) ?? lookupArtifactText("en", key);
  return typeof value === "string" ? value : key;
}

function settingsReadonlyText(key) {
  const value = lookupSettingsReadonlyText(currentLanguage, key)
    ?? lookupSettingsReadonlyText("en", key);
  return typeof value === "string" ? value : key;
}

function lookupArtifactText(language, key) {
  return key.split(".").reduce((value, segment) => {
    if (value && typeof value === "object") {
      return value[segment];
    }
    return undefined;
  }, ARTIFACT_BOARD_TEXT[language]);
}

function lookupSettingsReadonlyText(language, key) {
  return key.split(".").reduce((value, segment) => {
    if (value && typeof value === "object") {
      return value[segment];
    }
    return undefined;
  }, SETTINGS_READONLY_TEXT[language]);
}

function buildFeedback(tone, key, params = {}) {
  return { tone, key, params };
}

function buildRawFeedback(tone, rawText) {
  return { tone, rawText };
}

function feedbackText(feedback) {
  if (!feedback) {
    return "";
  }
  if (feedback.rawText) {
    return feedback.rawText;
  }
  return t(feedback.key, feedback.params || {});
}

async function loadStatus() {
  try {
    const response = await fetch(statusUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    lastStatusPayload = payload;
    renderDashboard(payload);
    return payload;
  } catch (error) {
    renderError(`${t("errors.statusFetchFailed")}${error.message}`);
    schedulePolling(30000);
    return null;
  }
}

async function loadHealth() {
  try {
    const response = await fetch(healthUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    lastHealthPayload = payload;
    renderHealth(payload);
    return payload;
  } catch (error) {
    lastHealthPayload = {
      status: "error",
      app_name: "not available",
      server_time: "not available",
      settings_loaded: false,
      state_file_accessible: false,
      observation_history_exists: false,
    };
    renderHealth(lastHealthPayload);
    return null;
  }
}

async function loadKeywords() {
  try {
    const response = await fetch(keywordsUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    lastKeywordsPayload = payload;
    renderKeywords(payload);
    return payload;
  } catch (error) {
    lastKeywordsPayload = {
      status: "error",
      override_path: "not available",
      override_exists: false,
      last_loaded_path: "not available",
      keyword_counts: { core: 0, supporting: 0, exclude: 0, total: 0 },
      keywords: { core: [], supporting: [], exclude: [] },
      save_meta: {
        status: "error",
        saved_at: "not available",
        target_path: "not available",
        changed_group: "not available",
        error_message: t("errors.keywordsUnavailable"),
      },
      error_message: t("errors.keywordsUnavailable"),
    };
    renderKeywords(lastKeywordsPayload);
    return null;
  }
}

async function loadSettingsSnapshot() {
  try {
    const response = await fetch(settingsUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    lastSettingsPayload = payload;
    renderSettings(payload);
    return payload;
  } catch (error) {
    lastSettingsPayload = {
      status: "error",
      config_path: "not available",
      override_path: "not available",
      override_exists: false,
      env_local_path: "not available",
      env_local_exists: false,
      current_source_mode: "not_available",
      sources: {},
      extra_sources: [],
      save_meta: {
        status: "error",
        saved_at: settingsText("saveMeta.notAvailable"),
        target_path: "not available",
        changed_section: "not_available",
        error_message: "Settings snapshot could not be loaded.",
      },
      error_message: "Settings snapshot could not be loaded.",
    };
    renderSettings(lastSettingsPayload);
    return null;
  }
}

async function loadDashboard() {
  await Promise.allSettled([loadStatus(), loadHealth(), loadKeywords(), loadSettingsSnapshot()]);
}

function renderDashboard(payload) {
  dashboardTitle.textContent = t("hero.title");
  dashboardSubtitle.textContent = t("dashboard.solution.description");
  updatedAt.textContent = payload.updated_at;
  errorBanner.classList.toggle("hidden", payload.status !== "error");
  errorBanner.textContent = payload.error_message || "";

  readOnlyBadge.textContent = payload.read_only ? t("hero.readOnly") : t("hero.enabled");
  readOnlyBadge.className = payload.status === "error"
    ? "status-pill status-error"
    : "status-pill status-ready";

  renderPathGrid(payload.paths || []);

  recentActions.innerHTML = "";
  for (const action of payload.recent_actions || []) {
    const panel = document.createElement("article");
    panel.className = "action-panel";
    panel.innerHTML = `
      <div class="action-panel-header">
        <h3 class="action-panel-title">${escapeHtml(translateActionTitle(action.title))}</h3>
        <span class="${statusClass(action.status)}">${escapeHtml(translateStatus(action.status))}</span>
      </div>
      <div class="summary-list">
        ${(action.items || []).map((item) => `
          <div class="summary-row">
            <span class="label">${escapeHtml(translateSummaryLabel(item.label))}</span>
            <span class="value">${escapeHtml(translateSummaryValue(item.label, item.value))}</span>
          </div>
        `).join("")}
      </div>
    `;
    recentActions.appendChild(panel);
  }

  renderLaunchers(payload.launchers || []);
  renderArtifactBoard(payload.artifacts || []);

  const collectControl = payload.collect_control || null;
  const exportControl = payload.export_control || null;
  const observeControl = payload.observe_control || null;
  renderCollectControl(collectControl);
  renderExportControl(exportControl);
  renderObserveControl(observeControl);
  schedulePolling(
    (collectControl || {}).status === "running"
      || (exportControl || {}).status === "running"
      || (observeControl || {}).status === "running"
      ? 2000
      : 30000,
  );
}

function renderPathGrid(items) {
  pathsGrid.innerHTML = "";
  for (const item of items || []) {
    const element = document.createElement("article");
    element.className = "path-item";
    element.innerHTML = `
      <span class="label">${escapeHtml(translatePathLabel(item.label))}</span>
      <code>${escapeHtml(translateDisplayValue(item.value))}</code>
    `;
    pathsGrid.appendChild(element);
  }
}

function renderLaunchers(items) {
  launcherList.innerHTML = "";
  for (const launcher of items || []) {
    const element = document.createElement("article");
    element.className = "launcher-item";
    element.innerHTML = `
      <span class="label">${escapeHtml(translateLauncherLabel(launcher.label))}</span>
      <code>${escapeHtml(launcher.value)}</code>
    `;
    launcherList.appendChild(element);
  }
}

function renderArtifactBoard(items) {
  const artifacts = Array.isArray(items) ? items.filter(Boolean) : [];
  const groups = [
    {
      key: "export",
      title: artifactText("groups.export"),
      items: artifacts.filter((item) => item.group === "export"),
    },
    {
      key: "observation",
      title: artifactText("groups.observation"),
      items: artifacts.filter((item) => item.group === "observation"),
    },
  ].filter((group) => group.items.length > 0);

  artifactBoard.innerHTML = "";
  if (!groups.length) {
    const empty = document.createElement("article");
    empty.className = "artifact-empty";
    empty.textContent = artifactText("empty");
    artifactBoard.appendChild(empty);
    return;
  }

  for (const group of groups) {
    const element = document.createElement("section");
    element.className = "artifact-group";
    element.innerHTML = `
      <div class="artifact-group-header">
        <h3 class="artifact-group-title">${escapeHtml(group.title)}</h3>
        <span class="artifact-group-count">${escapeHtml(String(group.items.length))}</span>
      </div>
      <div class="artifact-board-list">
        ${group.items.map((item) => renderArtifactRow(item)).join("")}
      </div>
    `;
    artifactBoard.appendChild(element);
  }
}

function renderArtifactRow(item) {
  const createdAt = item.created_at || t("status.not_available");
  const path = item.path || t("status.not_available");
  const status = item.status || "not_available";
  const kind = item.kind || "not_available";
  const openLink = item.open_url
    ? `
      <a class="artifact-link" href="${escapeHtml(item.open_url)}" target="_blank" rel="noreferrer">
        ${escapeHtml(artifactText("actions.open"))}
      </a>
    `
    : "";
  const downloadLink = item.download_url
    ? `
      <a class="artifact-link artifact-link-download" href="${escapeHtml(item.download_url)}" target="_blank" rel="noreferrer">
        ${escapeHtml(artifactText("actions.download"))}
      </a>
    `
    : "";

  return `
    <article class="artifact-row">
      <div class="artifact-row-header">
        <strong class="artifact-row-title">${escapeHtml(item.name || path)}</strong>
        <span class="${statusClass(status)}">${escapeHtml(translateStatus(status))}</span>
      </div>
      <div class="artifact-meta-grid">
        <div class="artifact-meta-item">
          <span class="label">${escapeHtml(artifactText("labels.createdAt"))}</span>
          <span class="value">${escapeHtml(translateDisplayValue(createdAt))}</span>
        </div>
        <div class="artifact-meta-item">
          <span class="label">${escapeHtml(artifactText("labels.kind"))}</span>
          <span class="value">${escapeHtml(artifactText(`kinds.${kind}`))}</span>
        </div>
        <div class="artifact-meta-item artifact-meta-item-path">
          <span class="label">${escapeHtml(artifactText("labels.path"))}</span>
          <code>${escapeHtml(path)}</code>
        </div>
        <div class="artifact-meta-item">
          <span class="label">${escapeHtml(artifactText("labels.status"))}</span>
          <span class="value">${escapeHtml(translateStatus(status))}</span>
        </div>
      </div>
      <div class="artifact-actions">
        ${openLink}
        ${downloadLink}
      </div>
    </article>
  `;
}

function renderHealth(payload) {
  const status = payload.status || "error";
  healthBadge.className = healthStatusClass(status);
  healthBadge.textContent = translateStatus(status);
  healthAppName.textContent = payload.app_name || t("status.not_available");
  healthServerTime.textContent = payload.server_time || t("status.not_available");
  healthSettingsLoaded.textContent = booleanLabel(payload.settings_loaded, "status.loaded", "status.not_loaded");
  healthStateFileAccessible.textContent = booleanLabel(
    payload.state_file_accessible,
    "status.accessible",
    "status.not_accessible",
  );
  healthObservationHistoryExists.textContent = booleanLabel(
    payload.observation_history_exists,
    "status.available",
    "status.missing",
  );
  dashboardHealthAppName.textContent = payload.app_name || t("status.not_available");
  dashboardHealthServerTime.textContent = payload.server_time || t("status.not_available");
  dashboardHealthSettingsLoaded.textContent = booleanLabel(
    payload.settings_loaded,
    "status.loaded",
    "status.not_loaded",
  );
  dashboardHealthStateFile.textContent = booleanLabel(
    payload.state_file_accessible,
    "status.accessible",
    "status.not_accessible",
  );
  dashboardHealthObservationHistory.textContent = booleanLabel(
    payload.observation_history_exists,
    "status.available",
    "status.missing",
  );
}

function renderKeywords(payload) {
  lastKeywordsPayload = payload;
  const status = payload.status || "error";
  const counts = payload.keyword_counts || {};
  const keywords = payload.keywords || {};
  const saveMeta = payload.save_meta || {};
  currentKeywordsStatus = status;

  if (!coreDraftDirty && !coreSaveInFlight) {
    coreDraftKeywords = [...(keywords.core || [])];
  }
  if (!supportingDraftDirty && !supportingSaveInFlight) {
    supportingDraftKeywords = [...(keywords.supporting || [])];
  }
  if (!excludeDraftDirty && !excludeSaveInFlight) {
    excludeDraftKeywords = [...(keywords.exclude || [])];
  }

  keywordsStatusBadge.className = keywordsStatusClass(status);
  keywordsStatusBadge.textContent = translateStatus(status);
  keywordsOverridePath.textContent = payload.override_path || t("status.not_available");
  keywordsOverrideExists.textContent = booleanLabel(
    payload.override_exists,
    "status.present",
    "status.missing",
  );
  keywordsLastLoadedPath.textContent = payload.last_loaded_path || t("status.not_available");
  keywordsTotalCount.textContent = String(counts.total || 0);
  renderKeywordSaveMeta(saveMeta);
  keywordsCoreCount.textContent = String(
    coreDraftDirty ? coreDraftKeywords.length : (counts.core || 0),
  );
  keywordsSupportingCount.textContent = String(
    supportingDraftDirty ? supportingDraftKeywords.length : (counts.supporting || 0),
  );
  keywordsExcludeCount.textContent = String(
    excludeDraftDirty ? excludeDraftKeywords.length : (counts.exclude || 0),
  );
  dashboardKeywordsCoreCount.textContent = String(counts.core || 0);
  dashboardKeywordsSupportingCount.textContent = String(counts.supporting || 0);
  dashboardKeywordsExcludeCount.textContent = String(counts.exclude || 0);
  dashboardKeywordsSavedAt.textContent = saveMeta.saved_at || t("status.not_available");
  dashboardKeywordsGroup.textContent = translateKeywordGroup(saveMeta.changed_group);
  dashboardKeywordsTargetPath.textContent = saveMeta.target_path || t("status.not_available");

  if (status === "error" && payload.error_message) {
    keywordsMessage.textContent = payload.error_message;
  } else {
    keywordsMessage.textContent = t("keywords.message");
  }

  renderCoreKeywordEditor();
  renderSupportingKeywordEditor();
  renderExcludeKeywordEditor();
}

function renderKeywordSaveMeta(meta) {
  const status = meta.status || "not_available";
  keywordsSaveMetaSavedAt.textContent = meta.saved_at || t("status.not_available");
  keywordsSaveMetaTargetPath.textContent = meta.target_path || t("status.not_available");
  keywordsSaveMetaGroup.textContent = translateKeywordGroup(meta.changed_group);
  keywordsSaveMetaStatus.className = statusClass(status);
  keywordsSaveMetaStatus.textContent = translateStatus(status);
}

function syncSettingsSourceDraftIfNeeded(bizinfo, g2b, currentSourceMode, extraSources) {
  if (settingsSourceDraftDirty || settingsSourceSaveInFlight) {
    return;
  }
  const normalizedMode = ["api", "fixture"].includes(currentSourceMode) ? currentSourceMode : "api";
  settingsSourceDraft = {
    bizinfoEnabled: Boolean(bizinfo.enabled),
    g2bEnabled: Boolean(g2b.enabled),
    sourceMode: normalizedMode,
    extraSources: extraSources.map((item) => ({
      name: String(item.name || ""),
      endpoint: String(item.endpoint || ""),
      api_key_env_var: String(item.api_key_env_var || ""),
      enabled: Boolean(item.enabled),
      description: String(item.description || ""),
    })),
  };
}

function renderSettings(payload) {
  if (!settingsManagementRoot) {
    return;
  }

  lastSettingsPayload = payload;
  const sources = payload.sources || {};
  const extraSources = Array.isArray(payload.extra_sources) ? payload.extra_sources : [];
  const bizinfo = sources.bizinfo || buildDefaultManagedSource("bizinfo");
  const g2b = sources.g2b || buildDefaultManagedSource("g2b");
  const currentSourceMode = payload.current_source_mode || "not_available";
  syncSettingsSourceDraftIfNeeded(bizinfo, g2b, currentSourceMode, extraSources);
  const builtInSources = [bizinfo, g2b];
  const enabledSources = builtInSources.filter((item) => item.enabled);
  const enabledSourceSummary = enabledSources.length
    ? enabledSources.map((item) => item.display_name || item.key).join(" / ")
    : t("status.not_available");
  const additionalSourceCards = extraSources.length
    ? extraSources.map((item) => renderAdditionalSourceCard(item)).join("")
    : renderAdditionalSourcePlaceholder();
  const additionalApiKeyCards = extraSources.length
    ? extraSources.map((item) => renderAdditionalApiKeyCard(item)).join("")
    : renderAdditionalApiKeyPlaceholder();
  const sourceFeedbackText = settingsFeedbackText(settingsSourceFeedback);
  const apiKeyFeedbackText = settingsFeedbackText(settingsApiKeysFeedback);

  settingsManagementRoot.innerHTML = `
    <section class="panel glass-panel reveal settings-manager-card">
      <div class="section-header">
        <p class="section-kicker">${escapeHtml(settingsText("sources.kicker"))}</p>
        <h2>${escapeHtml(settingsText("sources.title"))}</h2>
      </div>
      <div class="settings-save-meta-grid">
        <article class="keyword-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("summary.sourceMode"))}</span>
          <strong>${escapeHtml(translateSourceMode(currentSourceMode))}</strong>
        </article>
        <article class="keyword-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("summary.enabledSources"))}</span>
          <strong>${escapeHtml(enabledSourceSummary)}</strong>
        </article>
        <article class="keyword-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("summary.enabledCount"))}</span>
          <strong>${escapeHtml(String(enabledSources.length))}</strong>
        </article>
        <article class="keyword-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("summary.extraSources"))}</span>
          <strong>${escapeHtml(String(extraSources.length))}</strong>
        </article>
      </div>
      <p class="hint readonly-note">${escapeHtml(settingsText("sources.message"))}</p>
      <label class="managed-select-row" for="settings-source-mode-select">
        <span>${escapeHtml(settingsText("sources.sourceModeLabel"))}</span>
        <select
          id="settings-source-mode-select"
          ${settingsSourceSaveInFlight ? "disabled" : ""}
        >
          <option value="api" ${settingsSourceDraft.sourceMode === "api" ? "selected" : ""}>
            ${escapeHtml(settingsText("sources.sourceModeApi"))}
          </option>
          <option value="fixture" ${settingsSourceDraft.sourceMode === "fixture" ? "selected" : ""}>
            ${escapeHtml(settingsText("sources.sourceModeFixture"))}
          </option>
        </select>
      </label>
      <div class="managed-source-grid">
        ${renderManagedSourceCard("bizinfo", bizinfo, settingsSourceDraft.bizinfoEnabled)}
        ${renderManagedSourceCard("g2b", g2b, settingsSourceDraft.g2bEnabled)}
      </div>
      <p
        id="settings-sources-message"
        class="keyword-editor-message ${keywordFeedbackClass(settingsSourceFeedback.tone)}"
        aria-live="polite"
      >${escapeHtml(sourceFeedbackText)}</p>
      <div class="settings-actions-row settings-source-actions">
        <button
          id="settings-sources-save-button"
          class="primary-button"
          type="button"
          ${settingsSourceSaveInFlight ? "disabled" : ""}
        >
          ${escapeHtml(settingsText("sources.saveButton"))}
        </button>
      </div>
      <section class="embedded-form-section">
        <div class="section-header section-header-compact">
          <div>
            <p class="section-kicker">${escapeHtml(settingsText("sources.extraKicker"))}</p>
            <h3>${escapeHtml(settingsText("sources.extraTitle"))}</h3>
          </div>
        </div>
        <p class="hint readonly-note">${escapeHtml(settingsReadonlyText("labels.sourceSkeletonHint"))}</p>
        <div class="managed-source-grid">
          ${additionalSourceCards}
        </div>
        <div class="settings-static-list">
          <article class="managed-source-meta-item">
            <span class="label">${escapeHtml(settingsReadonlyText("labels.sourceSkeleton"))}</span>
            <code>name</code>
            <code>endpoint</code>
            <code>api_key_env_var</code>
            <code>description</code>
          </article>
        </div>
      </section>
    </section>
    <section class="panel glass-panel reveal settings-manager-card">
      <div class="section-header">
        <p class="section-kicker">${escapeHtml(settingsText("apiKeys.kicker"))}</p>
        <h2>${escapeHtml(settingsText("apiKeys.title"))}</h2>
      </div>
      <p class="hint readonly-note">${escapeHtml(settingsReadonlyText("apiKeyHint"))}</p>
      <div class="managed-source-grid">
        ${renderApiKeyCard("bizinfo", bizinfo, settingsApiKeyDraft.bizinfo)}
        ${renderApiKeyCard("g2b", g2b, settingsApiKeyDraft.g2b)}
        ${additionalApiKeyCards}
      </div>
      <p
        id="settings-api-keys-message"
        class="keyword-editor-message ${keywordFeedbackClass(settingsApiKeysFeedback.tone)}"
        aria-live="polite"
      >${escapeHtml(apiKeyFeedbackText)}</p>
      <div class="settings-actions-row settings-api-key-actions">
        <button
          id="settings-api-keys-save-button"
          class="primary-button"
          type="button"
          ${settingsApiKeySaveInFlight ? "disabled" : ""}
        >
          ${escapeHtml(settingsText("apiKeys.saveButton"))}
        </button>
      </div>
    </section>
  `;
  bindSettingsManagementHandlers(payload.status || "ready");
}

function renderReadOnlySourceCard(sourceKey, source) {
  const enabled = Boolean(source.enabled);
  return `
    <article class="managed-source-card">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(source.display_name || source.key || sourceKey)}</span>
          <strong>${escapeHtml(settingsText(`sources.${sourceKey}CardTitle`))}</strong>
        </div>
        <span class="${enabled ? "status-pill status-ready" : "status-pill status-neutral"}">${escapeHtml(enabled ? settingsText("labels.enabled") : settingsText("labels.disabled"))}</span>
      </div>
      <p class="hint readonly-note">${escapeHtml(source.endpoint || t("status.not_available"))}</p>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("sources.endpointLabel"))}</span>
          <code>${escapeHtml(source.endpoint || t("status.not_available"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.fixturePath"))}</span>
          <code>${escapeHtml(source.fixture_path || t("status.not_available"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.apiKeyStatus"))}</span>
          <code>${escapeHtml(source.api_key_configured ? settingsReadonlyText("labels.registered") : settingsReadonlyText("labels.notRegistered"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.envVar"))}</span>
          <code>${escapeHtml(source.api_key_env_var || t("status.not_available"))}</code>
        </article>
      </div>
    </article>
  `;
}

function renderAdditionalSourceCard(source) {
  const enabled = Boolean(source.enabled);
  return `
    <article class="managed-source-card">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(settingsReadonlyText("labels.additionalSourceTitle"))}</span>
          <strong>${escapeHtml(source.name || t("status.not_available"))}</strong>
        </div>
        <span class="${enabled ? "status-pill status-ready" : "status-pill status-neutral"}">${escapeHtml(enabled ? settingsText("labels.enabled") : settingsText("labels.disabled"))}</span>
      </div>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("sources.endpointLabel"))}</span>
          <code>${escapeHtml(source.endpoint || t("status.not_available"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.envVar"))}</span>
          <code>${escapeHtml(source.api_key_env_var || t("status.not_available"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.description"))}</span>
          <code>${escapeHtml(source.description || settingsReadonlyText("labels.noDescription"))}</code>
        </article>
      </div>
    </article>
  `;
}

function renderAdditionalSourcePlaceholder() {
  return `
    <article class="managed-source-card managed-source-card-placeholder">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(settingsReadonlyText("labels.additionalSourceTitle"))}</span>
          <strong>${escapeHtml(settingsReadonlyText("labels.additionalSourceHint"))}</strong>
        </div>
        <span class="status-pill status-neutral">${escapeHtml(t("status.not_available"))}</span>
      </div>
      <p class="hint readonly-note">${escapeHtml(settingsReadonlyText("labels.sourceSkeletonHint"))}</p>
    </article>
  `;
}

function renderReadOnlyApiKeyCard(sourceKey, source) {
  const configured = Boolean(source.api_key_configured);
  const title = sourceKey === "bizinfo"
    ? settingsText("apiKeys.bizinfoCardTitle")
    : settingsText("apiKeys.g2bCardTitle");
  const labelTitle = sourceKey === "bizinfo"
    ? settingsText("apiKeys.bizinfoTitle")
    : settingsText("apiKeys.g2bTitle");
  return `
    <article class="managed-source-card">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(labelTitle)}</span>
          <strong>${escapeHtml(title)}</strong>
        </div>
        <span class="${configured ? "status-pill status-ready" : "status-pill status-neutral"}">${escapeHtml(configured ? settingsReadonlyText("labels.registered") : settingsReadonlyText("labels.notRegistered"))}</span>
      </div>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.maskedValue"))}</span>
          <code>${escapeHtml(source.api_key_masked || settingsText("labels.notConfigured"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.envVar"))}</span>
          <code>${escapeHtml(source.api_key_env_var || t("status.not_available"))}</code>
        </article>
      </div>
      <p class="hint readonly-note">${escapeHtml(settingsReadonlyText("apiKeyHint"))}</p>
    </article>
  `;
}

function renderAdditionalApiKeyCard(source) {
  return `
    <article class="managed-source-card managed-source-card-placeholder">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(settingsReadonlyText("labels.additionalApiKeyTitle"))}</span>
          <strong>${escapeHtml(source.name || t("status.not_available"))}</strong>
        </div>
        <span class="status-pill status-neutral">${escapeHtml(settingsReadonlyText("labels.notRegistered"))}</span>
      </div>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.envVar"))}</span>
          <code>${escapeHtml(source.api_key_env_var || t("status.not_available"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsReadonlyText("labels.description"))}</span>
          <code>${escapeHtml(source.description || settingsReadonlyText("labels.noDescription"))}</code>
        </article>
      </div>
    </article>
  `;
}

function renderAdditionalApiKeyPlaceholder() {
  return `
    <article class="managed-source-card managed-source-card-placeholder">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(settingsReadonlyText("labels.additionalApiKeyTitle"))}</span>
          <strong>${escapeHtml(settingsReadonlyText("labels.additionalApiKeyHint"))}</strong>
        </div>
        <span class="status-pill status-neutral">${escapeHtml(t("status.not_available"))}</span>
      </div>
      <p class="hint readonly-note">${escapeHtml(settingsReadonlyText("apiKeyHint"))}</p>
    </article>
  `;
}

function renderManagedSourceCard(sourceKey, source, draftEnabled) {
  const statusLabel = draftEnabled ? settingsText("labels.enabled") : settingsText("labels.disabled");
  return `
    <article class="managed-source-card">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(source.display_name || source.key || sourceKey)}</span>
          <strong>${escapeHtml(settingsText(`sources.${sourceKey}CardTitle`))}</strong>
        </div>
        <span class="${draftEnabled ? "status-pill status-ready" : "status-pill status-neutral"}">${escapeHtml(statusLabel)}</span>
      </div>
      <label class="managed-toggle-row" for="settings-source-${sourceKey}-enabled">
        <input
          id="settings-source-${sourceKey}-enabled"
          type="checkbox"
          ${draftEnabled ? "checked" : ""}
          ${settingsSourceSaveInFlight ? "disabled" : ""}
        >
        <span>${escapeHtml(settingsText("sources.enabledToggle"))}</span>
      </label>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("sources.endpointLabel"))}</span>
          <code>${escapeHtml(source.endpoint || "not available")}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("sources.apiKeyLabel"))}</span>
          <code>${escapeHtml(source.api_key_masked || settingsText("labels.notConfigured"))}</code>
        </article>
      </div>
    </article>
  `;
}

function renderApiKeyCard(sourceKey, source, draftValue) {
  const title = sourceKey === "bizinfo"
    ? settingsText("apiKeys.bizinfoCardTitle")
    : settingsText("apiKeys.g2bCardTitle");
  const labelTitle = sourceKey === "bizinfo"
    ? settingsText("apiKeys.bizinfoTitle")
    : settingsText("apiKeys.g2bTitle");
  const placeholder = sourceKey === "bizinfo"
    ? settingsText("apiKeys.bizinfoPlaceholder")
    : settingsText("apiKeys.g2bPlaceholder");
  const configured = Boolean(source.api_key_configured);
  return `
    <article class="managed-source-card">
      <div class="managed-source-head">
        <div>
          <span class="label">${escapeHtml(labelTitle)}</span>
          <strong>${escapeHtml(title)}</strong>
        </div>
        <span class="${configured ? "status-pill status-ready" : "status-pill status-neutral"}">${escapeHtml(configured ? settingsText("labels.configured") : settingsText("labels.notConfigured"))}</span>
      </div>
      <div class="managed-source-meta">
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("apiKeys.maskedLabel"))}</span>
          <code>${escapeHtml(source.api_key_masked || settingsText("labels.notConfigured"))}</code>
        </article>
        <article class="managed-source-meta-item">
          <span class="label">${escapeHtml(settingsText("apiKeys.envVarLabel"))}</span>
          <code>${escapeHtml(source.api_key_env_var || "not available")}</code>
        </article>
      </div>
      <label class="keyword-editor-input">
        <span class="sr-only">${escapeHtml(title)}</span>
        <input
          id="settings-api-key-${sourceKey}-input"
          type="password"
          autocomplete="new-password"
          placeholder="${escapeHtml(placeholder)}"
          value="${escapeHtml(draftValue || "")}"
          ${settingsApiKeySaveInFlight ? "disabled" : ""}
        >
      </label>
    </article>
  `;
}

function renderExtraSourceDrafts() {
  if (!settingsSourceDraft.extraSources.length) {
    return `<span class="keyword-empty">${escapeHtml(settingsText("sources.extraEmpty"))}</span>`;
  }
  return settingsSourceDraft.extraSources.map((item, index) => `
    <span class="keyword-chip keyword-chip-editable extra-source-chip">
      <span class="keyword-chip-text">
        <strong>${escapeHtml(item.name)}</strong>
        <small>${escapeHtml(item.endpoint)}</small>
        <small>${escapeHtml(item.api_key_env_var)}</small>
      </span>
      <button
        class="keyword-chip-remove"
        type="button"
        data-remove-extra-source-index="${index}"
        ${settingsSourceSaveInFlight ? "disabled" : ""}
      >
        ${escapeHtml(settingsText("labels.remove"))}
      </button>
    </span>
  `).join("");
}

function bindSettingsManagementHandlers(status) {
  const bizinfoToggle = document.getElementById("settings-source-bizinfo-enabled");
  const g2bToggle = document.getElementById("settings-source-g2b-enabled");
  const sourceModeSelect = document.getElementById("settings-source-mode-select");
  const extraNameInput = document.getElementById("settings-extra-source-name");
  const extraEndpointInput = document.getElementById("settings-extra-source-endpoint");
  const extraEnvVarInput = document.getElementById("settings-extra-source-env-var");
  const extraDescriptionInput = document.getElementById("settings-extra-source-description");
  const addExtraSourceButton = document.getElementById("settings-extra-source-add-button");
  const saveSourcesButton = document.getElementById("settings-sources-save-button");
  const saveApiKeysButton = document.getElementById("settings-api-keys-save-button");
  const bizinfoApiKeyInput = document.getElementById("settings-api-key-bizinfo-input");
  const g2bApiKeyInput = document.getElementById("settings-api-key-g2b-input");

  if (bizinfoToggle) {
    bizinfoToggle.addEventListener("change", () => {
      settingsSourceDraft.bizinfoEnabled = bizinfoToggle.checked;
      settingsSourceDraftDirty = true;
      settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.message"));
      renderSettings(lastSettingsPayload || { status });
    });
  }
  if (g2bToggle) {
    g2bToggle.addEventListener("change", () => {
      settingsSourceDraft.g2bEnabled = g2bToggle.checked;
      settingsSourceDraftDirty = true;
      settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.message"));
      renderSettings(lastSettingsPayload || { status });
    });
  }
  if (sourceModeSelect) {
    sourceModeSelect.addEventListener("change", () => {
      settingsSourceDraft.sourceMode = sourceModeSelect.value;
      settingsSourceDraftDirty = true;
      settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.message"));
      renderSettings(lastSettingsPayload || { status });
    });
  }

  for (const [fieldKey, element] of [
    ["name", extraNameInput],
    ["endpoint", extraEndpointInput],
    ["api_key_env_var", extraEnvVarInput],
    ["description", extraDescriptionInput],
  ]) {
    if (!element) {
      continue;
    }
    element.addEventListener("input", () => {
      settingsExtraSourceForm[fieldKey] = element.value;
    });
  }

  if (bizinfoApiKeyInput) {
    bizinfoApiKeyInput.addEventListener("input", () => {
      settingsApiKeyDraft.bizinfo = bizinfoApiKeyInput.value;
    });
  }
  if (g2bApiKeyInput) {
    g2bApiKeyInput.addEventListener("input", () => {
      settingsApiKeyDraft.g2b = g2bApiKeyInput.value;
    });
  }

  if (addExtraSourceButton) {
    addExtraSourceButton.addEventListener("click", () => {
      addExtraSourceDraft();
    });
  }
  if (saveSourcesButton) {
    saveSourcesButton.addEventListener("click", () => {
      saveSourceSettings();
    });
  }
  if (saveApiKeysButton) {
    saveApiKeysButton.addEventListener("click", () => {
      saveApiKeySettings();
    });
  }

  for (const removeButton of document.querySelectorAll("[data-remove-extra-source-index]")) {
    removeButton.addEventListener("click", () => {
      const index = Number(removeButton.getAttribute("data-remove-extra-source-index"));
      removeExtraSourceDraft(index);
    });
  }
}

function buildDefaultManagedSource(sourceKey) {
  return {
    key: sourceKey,
    display_name: sourceKey === "bizinfo" ? "Bizinfo" : "G2B",
    enabled: false,
    endpoint: "not available",
    api_key_masked: settingsText("labels.notConfigured"),
    api_key_env_var: sourceKey === "bizinfo" ? "PROJECT1_BIZINFO_CERT_KEY" : "PROJECT1_G2B_API_KEY",
    api_key_configured: false,
  };
}

function settingsFeedbackText(feedback) {
  if (!feedback) {
    return "";
  }
  if (feedback.rawText) {
    return feedback.rawText;
  }
  if (!feedback.key || feedback.tone === "neutral") {
    return "";
  }
  return settingsText(String(feedback.key).replace(/^settings\./, ""), feedback.params || {});
}

function addExtraSourceDraft() {
  const name = normalizeKeyword(settingsExtraSourceForm.name);
  const endpoint = normalizeKeyword(settingsExtraSourceForm.endpoint);
  const apiKeyEnvVar = normalizeKeyword(settingsExtraSourceForm.api_key_env_var).toUpperCase();
  const description = normalizeKeyword(settingsExtraSourceForm.description);

  if (!name) {
    settingsSourceFeedback = buildRawFeedback("error", settingsText("sources.addNameRequired"));
    renderSettings(lastSettingsPayload || {});
    return;
  }
  if (!endpoint) {
    settingsSourceFeedback = buildRawFeedback("error", settingsText("sources.addEndpointRequired"));
    renderSettings(lastSettingsPayload || {});
    return;
  }
  if (!apiKeyEnvVar) {
    settingsSourceFeedback = buildRawFeedback("error", settingsText("sources.addEnvVarRequired"));
    renderSettings(lastSettingsPayload || {});
    return;
  }
  if (!/^[A-Z][A-Z0-9_]*$/.test(apiKeyEnvVar)) {
    settingsSourceFeedback = buildRawFeedback("error", settingsText("sources.addEnvVarInvalid"));
    renderSettings(lastSettingsPayload || {});
    return;
  }
  if (settingsSourceDraft.extraSources.some((item) => sameKeyword(item.name, name))) {
    settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.addDuplicate", { name }));
    renderSettings(lastSettingsPayload || {});
    return;
  }

  settingsSourceDraft.extraSources = [
    ...settingsSourceDraft.extraSources,
    {
      name,
      endpoint,
      api_key_env_var: apiKeyEnvVar,
      enabled: false,
      description,
    },
  ];
  settingsExtraSourceForm = {
    name: "",
    endpoint: "",
    api_key_env_var: "",
    description: "",
  };
  settingsSourceDraftDirty = true;
  settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.message"));
  renderSettings(lastSettingsPayload || {});
}

function removeExtraSourceDraft(index) {
  settingsSourceDraft.extraSources = settingsSourceDraft.extraSources.filter((_item, itemIndex) => itemIndex !== index);
  settingsSourceDraftDirty = true;
  settingsSourceFeedback = buildRawFeedback("warning", settingsText("sources.message"));
  renderSettings(lastSettingsPayload || {});
}

async function saveSourceSettings() {
  if (!settingsSourceDraft.bizinfoEnabled && !settingsSourceDraft.g2bEnabled) {
    settingsSourceFeedback = buildRawFeedback("error", settingsText("sources.mustKeepOne"));
    renderSettings(lastSettingsPayload || {});
    return;
  }
  if (settingsSourceDraft.bizinfoEnabled && settingsSourceDraft.g2bEnabled) {
    settingsSourceFeedback = buildRawFeedback(
      "error",
      currentLanguage === "ko"
        ? "현재 collect는 한 번에 하나의 기본 source만 실행할 수 있습니다. 기업마당 또는 나라장터 중 하나만 활성화해 주세요."
        : "Collect currently supports one built-in source at a time. Enable either Bizinfo or G2B.",
    );
    renderSettings(lastSettingsPayload || {});
    return;
  }

  settingsSourceSaveInFlight = true;
  settingsSourceFeedback = buildRawFeedback("neutral", settingsText("sources.saving"));
  renderSettings(lastSettingsPayload || {});

  try {
    const response = await fetch(settingsSourcesSaveUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source_mode: settingsSourceDraft.sourceMode,
        sources: {
          bizinfo: { enabled: settingsSourceDraft.bizinfoEnabled },
          g2b: { enabled: settingsSourceDraft.g2bEnabled },
        },
        extra_sources: settingsSourceDraft.extraSources,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.saved) {
      throw new Error(payload.error_message || settingsText("sources.feedbackSaveFailed"));
    }

    const snapshot = payload.settings_snapshot || null;
    settingsSourceDraftDirty = false;
    settingsSourceFeedback = buildRawFeedback("success", settingsText("sources.saved"));
    if (snapshot) {
      renderSettings(snapshot);
    }
    await loadStatus();
  } catch (error) {
    settingsSourceFeedback = buildRawFeedback("error", error.message);
  } finally {
    settingsSourceSaveInFlight = false;
    if (lastSettingsPayload) {
      renderSettings(lastSettingsPayload);
    }
  }
}

async function saveApiKeySettings() {
  const bizinfoValue = settingsApiKeyDraft.bizinfo.trim();
  const g2bValue = settingsApiKeyDraft.g2b.trim();
  if (!bizinfoValue && !g2bValue) {
    settingsApiKeysFeedback = buildRawFeedback("error", settingsText("apiKeys.empty"));
    renderSettings(lastSettingsPayload || {});
    return;
  }

  settingsApiKeySaveInFlight = true;
  settingsApiKeysFeedback = buildRawFeedback("neutral", settingsText("apiKeys.saving"));
  renderSettings(lastSettingsPayload || {});

  try {
    const response = await fetch(settingsApiKeysSaveUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bizinfo_api_key: bizinfoValue,
        g2b_api_key: g2bValue,
      }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.saved) {
      throw new Error(payload.error_message || settingsText("apiKeys.feedbackSaveFailed"));
    }

    const snapshot = payload.settings_snapshot || null;
    settingsApiKeyDraft = { bizinfo: "", g2b: "" };
    settingsApiKeysFeedback = buildRawFeedback("success", settingsText("apiKeys.saved"));
    if (snapshot) {
      renderSettings(snapshot);
    }
  } catch (error) {
    settingsApiKeyDraft = { bizinfo: "", g2b: "" };
    settingsApiKeysFeedback = buildRawFeedback("error", error.message);
  } finally {
    settingsApiKeySaveInFlight = false;
    if (lastSettingsPayload) {
      renderSettings(lastSettingsPayload);
    }
  }
}

function translateSettingsChangedSection(section) {
  if (section === "sources") {
    return settingsText("saveMeta.sectionSources");
  }
  if (section === "api_keys") {
    return settingsText("saveMeta.sectionApiKeys");
  }
  return settingsText("saveMeta.notAvailable");
}

function settingsFeedbackText(feedback, fallbackText) {
  if (!feedback) {
    return fallbackText;
  }
  if (feedback.rawText) {
    return feedback.rawText;
  }
  return settingsText(feedback.key, feedback.params || {});
}

function settingsFeedbackClass(tone) {
  if (tone === "success") {
    return "is-success";
  }
  if (tone === "warning") {
    return "is-warning";
  }
  if (tone === "error") {
    return "is-error";
  }
  return "is-neutral";
}

function renderCollectControl(payload) {
  const control = payload || defaultCollectControl();
  collectStatusBadge.className = statusClass(control.status);
  collectStatusBadge.textContent = translateStatus(control.status);
  collectButton.disabled = control.status === "running";

  if (control.status === "running") {
    collectMessage.textContent = t("controls.collect.running");
  } else if (control.status === "failed" && control.error_message) {
    collectMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    collectMessage.textContent = t("controls.collect.finished");
  } else {
    collectMessage.textContent = t("controls.collect.default");
  }

  renderMetricSummary(collectSummary, control.items || defaultCollectControl().items);
}

function renderExportControl(payload) {
  const control = payload || defaultExportControl();
  exportStatusBadge.className = statusClass(control.status);
  exportStatusBadge.textContent = translateStatus(control.status);
  exportButton.disabled = control.status === "running";

  if (control.status === "running") {
    exportMessage.textContent = t("controls.export.running");
  } else if (control.status === "failed" && control.error_message) {
    exportMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    exportMessage.textContent = t("controls.export.finished");
  } else {
    exportMessage.textContent = t("controls.export.default");
  }

  renderMetricSummary(exportSummary, control.items || defaultExportControl().items);
}

function renderObserveControl(payload) {
  const control = payload || defaultObserveControl();
  observeStatusBadge.className = statusClass(control.status);
  observeStatusBadge.textContent = translateStatus(control.status);
  observeButton.disabled = control.status === "running";

  if (control.status === "running") {
    observeMessage.textContent = t("controls.observe.running");
  } else if (control.status === "failed" && control.error_message) {
    observeMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    observeMessage.textContent = t("controls.observe.finished");
  } else {
    observeMessage.textContent = t("controls.observe.default");
  }

  renderMetricSummary(observeSummary, control.items || defaultObserveControl().items);
}

function renderMetricSummary(container, items) {
  container.innerHTML = "";
  for (const item of items || []) {
    const element = document.createElement("article");
    element.className = "collect-metric";
    element.innerHTML = `
      <span class="label">${escapeHtml(translateSummaryLabel(item.label))}</span>
      <span class="value">${escapeHtml(translateSummaryValue(item.label, item.value))}</span>
    `;
    container.appendChild(element);
  }
}

function renderCoreKeywordEditor() {
  const editable = true;
  const items = coreDraftKeywords;

  keywordsCoreInput.readOnly = false;
  keywordsCoreInput.disabled = coreSaveInFlight;
  keywordsCoreAddButton.disabled = coreSaveInFlight;
  keywordsCoreSaveButton.disabled = (
    coreSaveInFlight
    || !coreDraftDirty
    || !coreDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsCoreList, items, {
    emptyText: t("keywords.groups.core.empty"),
    removalDisabled: coreSaveInFlight,
    onRemove: removeCoreKeyword,
  });
  renderCoreFeedback();
}

function renderSupportingKeywordEditor() {
  const editable = currentKeywordsStatus === "ready";
  const items = supportingDraftKeywords;

  keywordsSupportingInput.readOnly = !editable || supportingSaveInFlight;
  keywordsSupportingInput.disabled = !editable || supportingSaveInFlight;
  keywordsSupportingAddButton.disabled = !editable || supportingSaveInFlight;
  keywordsSupportingSaveButton.disabled = (
    !editable
    || supportingSaveInFlight
    || !supportingDraftDirty
    || !supportingDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsSupportingList, items, {
    emptyText: t("keywords.groups.supporting.empty"),
    removalDisabled: currentKeywordsStatus !== "ready" || supportingSaveInFlight,
    onRemove: removeSupportingKeyword,
  });
  renderSupportingFeedback();
}

function renderExcludeKeywordEditor() {
  const editable = currentKeywordsStatus === "ready";
  const items = excludeDraftKeywords;

  keywordsExcludeInput.readOnly = !editable || excludeSaveInFlight;
  keywordsExcludeInput.disabled = !editable || excludeSaveInFlight;
  keywordsExcludeAddButton.disabled = !editable || excludeSaveInFlight;
  keywordsExcludeSaveButton.disabled = (
    !editable
    || excludeSaveInFlight
    || !excludeDraftDirty
    || !excludeDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsExcludeList, items, {
    emptyText: t("keywords.groups.exclude.empty"),
    removalDisabled: currentKeywordsStatus !== "ready" || excludeSaveInFlight,
    onRemove: removeExcludeKeyword,
  });
  renderExcludeFeedback();
}

function renderEditableKeywordGroup(container, items, options) {
  const emptyText = options.emptyText || "No keywords in the current draft";
  const removalDisabled = Boolean(options.removalDisabled);
  const onRemove = options.onRemove;
  container.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("span");
    empty.className = "keyword-empty";
    empty.textContent = emptyText;
    container.appendChild(empty);
    return;
  }

  for (const item of items) {
    const chip = document.createElement("span");
    chip.className = "keyword-chip keyword-chip-editable";
    chip.innerHTML = `
      <span class="keyword-chip-text">${escapeHtml(item)}</span>
      <button
        class="keyword-chip-remove"
        type="button"
        aria-label="${escapeHtml(`${t("buttons.remove")} ${item}`)}"
      >
        ${escapeHtml(t("buttons.remove"))}
      </button>
    `;
    const removeButton = chip.querySelector(".keyword-chip-remove");
    removeButton.disabled = removalDisabled;
    removeButton.addEventListener("click", () => {
      onRemove(item);
    });
    container.appendChild(chip);
  }
}

function renderCoreFeedback() {
  let tone = coreFeedback.tone;
  let text = feedbackText(coreFeedback);

  if (coreSaveInFlight) {
    tone = "neutral";
    text = t("keywords.groups.core.saving");
  } else if (tone === "neutral") {
    text = "";
  }

  keywordsCoreMessage.className = `keyword-editor-message ${keywordFeedbackClass(tone)}`;
  keywordsCoreMessage.textContent = text;
}

function renderSupportingFeedback() {
  let tone = supportingFeedback.tone;
  let text = feedbackText(supportingFeedback);

  if (currentKeywordsStatus !== "ready") {
    tone = "error";
    text = t("keywords.groups.supporting.unavailable");
  } else if (supportingSaveInFlight) {
    tone = "neutral";
    text = t("keywords.groups.supporting.saving");
  } else if (tone === "neutral") {
    text = "";
  }

  keywordsSupportingMessage.className = `keyword-editor-message ${keywordFeedbackClass(tone)}`;
  keywordsSupportingMessage.textContent = text;
}

function renderExcludeFeedback() {
  let tone = excludeFeedback.tone;
  let text = feedbackText(excludeFeedback);

  if (currentKeywordsStatus !== "ready") {
    tone = "error";
    text = t("keywords.groups.exclude.unavailable");
  } else if (excludeSaveInFlight) {
    tone = "neutral";
    text = t("keywords.groups.exclude.saving");
  } else if (tone === "neutral") {
    text = "";
  }

  keywordsExcludeMessage.className = `keyword-editor-message ${keywordFeedbackClass(tone)}`;
  keywordsExcludeMessage.textContent = text;
}

function keywordFeedbackClass(tone) {
  if (tone === "success") {
    return "is-success";
  }
  if (tone === "warning") {
    return "is-warning";
  }
  if (tone === "error") {
    return "is-error";
  }
  return "is-neutral";
}

function addSupportingKeyword() {
  if (currentKeywordsStatus !== "ready") {
    setSupportingFeedback("error", "keywords.groups.supporting.unavailable");
    renderSupportingKeywordEditor();
    return;
  }

  const keyword = normalizeKeyword(keywordsSupportingInput.value);
  if (!keyword) {
    setSupportingFeedback("error", "keywords.groups.supporting.addEmpty");
    renderSupportingKeywordEditor();
    return;
  }

  if (hasKeyword(supportingDraftKeywords, keyword)) {
    setSupportingFeedback("warning", "keywords.groups.supporting.duplicate", { keyword });
    renderSupportingKeywordEditor();
    return;
  }

  supportingDraftKeywords = [...supportingDraftKeywords, keyword];
  supportingDraftDirty = true;
  keywordsSupportingInput.value = "";
  setSupportingFeedback("warning", "keywords.groups.supporting.dirty");
  renderSupportingKeywordEditor();
}

function addCoreKeyword() {
  const keyword = normalizeKeyword(keywordsCoreInput.value);
  if (!keyword) {
    setCoreFeedback("error", "keywords.groups.core.addEmpty");
    renderCoreKeywordEditor();
    return;
  }

  if (hasKeyword(coreDraftKeywords, keyword)) {
    setCoreFeedback("warning", "keywords.groups.core.duplicate", { keyword });
    renderCoreKeywordEditor();
    return;
  }

  coreDraftKeywords = [...coreDraftKeywords, keyword];
  coreDraftDirty = true;
  keywordsCoreInput.value = "";
  setCoreFeedback("warning", "keywords.groups.core.dirty");
  renderCoreKeywordEditor();
}

function removeCoreKeyword(keyword) {
  coreDraftKeywords = coreDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  coreDraftDirty = true;
  setCoreFeedback("warning", "keywords.groups.core.dirty");
  renderCoreKeywordEditor();
}

async function saveCoreKeywords() {
  let shouldReloadKeywords = false;
  const normalizedKeywords = uniqueKeywords(coreDraftKeywords);
  if (!normalizedKeywords.length) {
    setCoreFeedback("error", "keywords.groups.core.mustRemain");
    renderCoreKeywordEditor();
    return;
  }

  coreDraftKeywords = normalizedKeywords;
  coreSaveInFlight = true;
  setCoreFeedback("neutral", "keywords.groups.core.saving");
  renderCoreKeywordEditor();

  try {
    const response = await fetch(keywordsCoreSaveUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ core_keywords: normalizedKeywords }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.saved) {
      throw new Error(payload.error_message || t("keywords.groups.core.saveFailed"));
    }

    const snapshot = payload.keywords_snapshot || null;
    coreDraftDirty = false;
    const savedCoreKeywords = (((snapshot || {}).keywords || {}).core) || [];
    coreDraftKeywords = [...savedCoreKeywords];
    setCoreFeedback("success", "keywords.groups.core.saved");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setCoreFeedbackRaw("error", error.message);
    shouldReloadKeywords = true;
  } finally {
    coreSaveInFlight = false;
    renderCoreKeywordEditor();
  }
  if (shouldReloadKeywords) {
    await loadKeywords();
  }
}

function removeSupportingKeyword(keyword) {
  supportingDraftKeywords = supportingDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  supportingDraftDirty = true;
  setSupportingFeedback("warning", "keywords.groups.supporting.dirty");
  renderSupportingKeywordEditor();
}

async function saveSupportingKeywords() {
  let shouldReloadKeywords = false;
  if (currentKeywordsStatus !== "ready") {
    setSupportingFeedback("error", "keywords.groups.supporting.saveUnavailable");
    renderSupportingKeywordEditor();
    return;
  }

  const normalizedKeywords = uniqueKeywords(supportingDraftKeywords);
  if (!normalizedKeywords.length) {
    setSupportingFeedback("error", "keywords.groups.supporting.mustRemain");
    renderSupportingKeywordEditor();
    return;
  }

  supportingDraftKeywords = normalizedKeywords;
  supportingSaveInFlight = true;
  setSupportingFeedback("neutral", "keywords.groups.supporting.saving");
  renderSupportingKeywordEditor();

  try {
    const response = await fetch(keywordsSupportingSaveUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ supporting_keywords: normalizedKeywords }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.saved) {
      throw new Error(payload.error_message || t("keywords.groups.supporting.saveFailed"));
    }

    const snapshot = payload.keywords_snapshot || null;
    supportingDraftDirty = false;
    const savedSupportingKeywords = (((snapshot || {}).keywords || {}).supporting) || [];
    supportingDraftKeywords = [...savedSupportingKeywords];
    setSupportingFeedback("success", "keywords.groups.supporting.saved");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setSupportingFeedbackRaw("error", error.message);
    shouldReloadKeywords = true;
  } finally {
    supportingSaveInFlight = false;
    renderSupportingKeywordEditor();
  }
  if (shouldReloadKeywords) {
    await loadKeywords();
  }
}

function addExcludeKeyword() {
  if (currentKeywordsStatus !== "ready") {
    setExcludeFeedback("error", "keywords.groups.exclude.unavailable");
    renderExcludeKeywordEditor();
    return;
  }

  const keyword = normalizeKeyword(keywordsExcludeInput.value);
  if (!keyword) {
    setExcludeFeedback("error", "keywords.groups.exclude.addEmpty");
    renderExcludeKeywordEditor();
    return;
  }

  if (hasKeyword(excludeDraftKeywords, keyword)) {
    setExcludeFeedback("warning", "keywords.groups.exclude.duplicate", { keyword });
    renderExcludeKeywordEditor();
    return;
  }

  excludeDraftKeywords = [...excludeDraftKeywords, keyword];
  excludeDraftDirty = true;
  keywordsExcludeInput.value = "";
  setExcludeFeedback("warning", "keywords.groups.exclude.dirty");
  renderExcludeKeywordEditor();
}

function removeExcludeKeyword(keyword) {
  excludeDraftKeywords = excludeDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  excludeDraftDirty = true;
  setExcludeFeedback("warning", "keywords.groups.exclude.dirty");
  renderExcludeKeywordEditor();
}

async function saveExcludeKeywords() {
  let shouldReloadKeywords = false;
  if (currentKeywordsStatus !== "ready") {
    setExcludeFeedback("error", "keywords.groups.exclude.saveUnavailable");
    renderExcludeKeywordEditor();
    return;
  }

  const normalizedKeywords = uniqueKeywords(excludeDraftKeywords);
  if (!normalizedKeywords.length) {
    setExcludeFeedback("error", "keywords.groups.exclude.mustRemain");
    renderExcludeKeywordEditor();
    return;
  }

  excludeDraftKeywords = normalizedKeywords;
  excludeSaveInFlight = true;
  setExcludeFeedback("neutral", "keywords.groups.exclude.saving");
  renderExcludeKeywordEditor();

  try {
    const response = await fetch(keywordsExcludeSaveUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ exclude_keywords: normalizedKeywords }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.saved) {
      throw new Error(payload.error_message || t("keywords.groups.exclude.saveFailed"));
    }

    const snapshot = payload.keywords_snapshot || null;
    excludeDraftDirty = false;
    const savedExcludeKeywords = (((snapshot || {}).keywords || {}).exclude) || [];
    excludeDraftKeywords = [...savedExcludeKeywords];
    setExcludeFeedback("success", "keywords.groups.exclude.saved");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setExcludeFeedbackRaw("error", error.message);
    shouldReloadKeywords = true;
  } finally {
    excludeSaveInFlight = false;
    renderExcludeKeywordEditor();
  }
  if (shouldReloadKeywords) {
    await loadKeywords();
  }
}

async function triggerCollect() {
  try {
    const response = await fetch(collectUrl, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json();
    renderCollectControl(payload.collect_control || null);
    await loadDashboard();
  } catch (error) {
    renderCollectControl({
      status: "failed",
      error_message: `${t("controls.collect.requestFailedPrefix")}${error.message}`,
      items: [
        { label: "Status", value: "failed" },
        { label: "Fetched", value: "0" },
        { label: "Saved", value: "0" },
        { label: "Skipped", value: "0" },
        { label: "Errors", value: "1" },
        { label: "DB Path", value: "not available" },
      ],
    });
  }
}

async function triggerExport() {
  try {
    const response = await fetch(exportUrl, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json();
    renderExportControl(payload.export_control || null);
    await loadDashboard();
  } catch (error) {
    renderExportControl({
      status: "failed",
      error_message: `${t("controls.export.requestFailedPrefix")}${error.message}`,
      items: [
        { label: "Status", value: "failed" },
        { label: "Exported files", value: "0" },
        { label: "Exported file path", value: "not available" },
        { label: "Export output dir", value: "not available" },
      ],
    });
  }
}

async function triggerObserve() {
  try {
    const response = await fetch(observeUrl, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json();
    renderObserveControl(payload.observe_control || null);
    await loadDashboard();
  } catch (error) {
    renderObserveControl({
      status: "failed",
      error_message: `${t("controls.observe.requestFailedPrefix")}${error.message}`,
      items: [
        { label: "Status", value: "failed" },
        { label: "Run ID", value: "not available" },
        { label: "Observed on", value: "not available" },
        { label: "Fetched", value: "0" },
        { label: "Saved", value: "0" },
        { label: "Skipped", value: "0" },
        { label: "Errors", value: "1" },
        { label: "Observation history", value: "not available" },
        { label: "Observation report", value: "not available" },
        { label: "Latest raw JSONL", value: "not available" },
      ],
    });
  }
}

function defaultCollectControl() {
  return {
    status: "idle",
    error_message: null,
    items: [
      { label: "Status", value: "idle" },
      { label: "Fetched", value: "0" },
      { label: "Saved", value: "0" },
      { label: "Skipped", value: "0" },
      { label: "Errors", value: "0" },
      { label: "DB Path", value: "not available" },
    ],
  };
}

function defaultExportControl() {
  return {
    status: "idle",
    error_message: null,
    items: [
      { label: "Status", value: "idle" },
      { label: "Exported files", value: "0" },
      { label: "Exported file path", value: "not available" },
      { label: "Export output dir", value: "not available" },
    ],
  };
}

function defaultObserveControl() {
  return {
    status: "idle",
    error_message: null,
    items: [
      { label: "Status", value: "idle" },
      { label: "Run ID", value: "not available" },
      { label: "Observed on", value: "not available" },
      { label: "Fetched", value: "0" },
      { label: "Saved", value: "0" },
      { label: "Skipped", value: "0" },
      { label: "Errors", value: "0" },
      { label: "Observation history", value: "not available" },
      { label: "Observation report", value: "not available" },
      { label: "Latest raw JSONL", value: "not available" },
    ],
  };
}

function renderError(message) {
  errorBanner.classList.remove("hidden");
  errorBanner.textContent = message;
  readOnlyBadge.className = "status-pill status-error";
  readOnlyBadge.textContent = translateStatus("error");
}

function healthStatusClass(status) {
  if (status === "ok") {
    return "status-pill status-ready";
  }
  if (status === "degraded") {
    return "status-pill status-warning";
  }
  return "status-pill status-error";
}

function keywordsStatusClass(status) {
  if (status === "ready") {
    return "status-pill status-ready";
  }
  return "status-pill status-error";
}

function normalizeKeyword(value) {
  return String(value || "").trim();
}

function sameKeyword(left, right) {
  return normalizeKeyword(left).toLowerCase() === normalizeKeyword(right).toLowerCase();
}

function hasKeyword(values, candidate) {
  return values.some((value) => sameKeyword(value, candidate));
}

function uniqueKeywords(values) {
  const unique = [];
  for (const value of values) {
    const keyword = normalizeKeyword(value);
    if (!keyword || hasKeyword(unique, keyword)) {
      continue;
    }
    unique.push(keyword);
  }
  return unique;
}

function setSupportingFeedback(tone, key, params = {}) {
  supportingFeedback = buildFeedback(tone, key, params);
}

function setSupportingFeedbackRaw(tone, rawText) {
  supportingFeedback = buildRawFeedback(tone, rawText);
}

function setCoreFeedback(tone, key, params = {}) {
  coreFeedback = buildFeedback(tone, key, params);
}

function setCoreFeedbackRaw(tone, rawText) {
  coreFeedback = buildRawFeedback(tone, rawText);
}

function setExcludeFeedback(tone, key, params = {}) {
  excludeFeedback = buildFeedback(tone, key, params);
}

function setExcludeFeedbackRaw(tone, rawText) {
  excludeFeedback = buildRawFeedback(tone, rawText);
}

function statusClass(status) {
  if (
    status === "success" ||
    status === "ready" ||
    status === "available" ||
    status === "finished"
  ) {
    return "status-pill status-ready";
  }
  if (status === "running") {
    return "status-pill status-warning";
  }
  if (status === "failed" || status === "error" || status === "config_error") {
    return "status-pill status-error";
  }
  return "status-pill status-neutral";
}

function booleanLabel(value, truthyKey, falsyKey) {
  return value ? t(truthyKey) : t(falsyKey);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function schedulePolling(delayMs) {
  if (pollingHandle !== null) {
    window.clearTimeout(pollingHandle);
  }
  pollingHandle = window.setTimeout(loadDashboard, delayMs);
}

refreshButton.addEventListener("click", () => {
  loadDashboard();
});

langKoButton.addEventListener("click", () => {
  setLanguage("ko");
});

langEnButton.addEventListener("click", () => {
  setLanguage("en");
});

collectButton.addEventListener("click", () => {
  triggerCollect();
});

exportButton.addEventListener("click", () => {
  triggerExport();
});

observeButton.addEventListener("click", () => {
  triggerObserve();
});

keywordsCoreAddButton.addEventListener("click", () => {
  addCoreKeyword();
});

keywordsCoreSaveButton.addEventListener("click", () => {
  saveCoreKeywords();
});

keywordsCoreInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  addCoreKeyword();
});

keywordsSupportingAddButton.addEventListener("click", () => {
  addSupportingKeyword();
});

keywordsSupportingSaveButton.addEventListener("click", () => {
  saveSupportingKeywords();
});

keywordsSupportingInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  addSupportingKeyword();
});

keywordsExcludeAddButton.addEventListener("click", () => {
  addExcludeKeyword();
});

keywordsExcludeSaveButton.addEventListener("click", () => {
  saveExcludeKeywords();
});

keywordsExcludeInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  addExcludeKeyword();
});

setLanguage(currentLanguage, { persist: false });
loadDashboard();

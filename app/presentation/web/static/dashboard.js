const statusUrl = document.body.dataset.statusUrl;
const keywordsUrl = document.body.dataset.keywordsUrl;
const keywordsCoreSaveUrl = document.body.dataset.keywordsCoreSaveUrl;
const keywordsSupportingSaveUrl = document.body.dataset.keywordsSupportingSaveUrl;
const keywordsExcludeSaveUrl = document.body.dataset.keywordsExcludeSaveUrl;
const healthUrl = document.body.dataset.healthUrl;
const collectUrl = document.body.dataset.collectUrl;
const exportUrl = document.body.dataset.exportUrl;
const observeUrl = document.body.dataset.observeUrl;
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
const recentActions = document.getElementById("recent-actions");
const launcherList = document.getElementById("launcher-list");
const dashboardTitle = document.getElementById("dashboard-title");
const dashboardSubtitle = document.getElementById("dashboard-subtitle");
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
let pollingHandle = null;
let currentKeywordsStatus = "loading";
let lastKeywordsPayload = null;
let coreDraftKeywords = [];
let coreDraftDirty = false;
let coreSaveInFlight = false;
let supportingDraftKeywords = [];
let supportingDraftDirty = false;
let supportingSaveInFlight = false;
let excludeDraftKeywords = [];
let excludeDraftDirty = false;
let excludeSaveInFlight = false;
let coreFeedback = {
  tone: "neutral",
  text: "Core keywords are saved into keywords.override.toml. Supporting and exclude keep using their own panels.",
};
let supportingFeedback = {
  tone: "neutral",
  text: "Supporting keywords are saved into keywords.override.toml. Core and exclude keep using their own panels.",
};
let excludeFeedback = {
  tone: "neutral",
  text: "Exclude keywords are saved into keywords.override.toml. Core and supporting keep using their own panels.",
};

async function loadStatus() {
  try {
    const response = await fetch(statusUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    renderDashboard(payload);
    return payload;
  } catch (error) {
    renderError(`Status fetch failed: ${error.message}`);
    schedulePolling(30000);
    return null;
  }
}

async function loadHealth() {
  try {
    const response = await fetch(healthUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    renderHealth(payload);
    return payload;
  } catch (error) {
    renderHealth({
      status: "error",
      app_name: "not available",
      server_time: "not available",
      settings_loaded: false,
      state_file_accessible: false,
      observation_history_exists: false,
    });
    return null;
  }
}

async function loadKeywords() {
  try {
    const response = await fetch(keywordsUrl, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    renderKeywords(payload);
    return payload;
  } catch (error) {
    renderKeywords({
      status: "error",
      override_path: "not available",
      override_exists: false,
      last_loaded_path: "not available",
      keyword_counts: { core: 0, supporting: 0, exclude: 0, total: 0 },
      keywords: { core: [], supporting: [], exclude: [] },
      error_message: "Keyword snapshot could not be loaded.",
    });
    return null;
  }
}

async function loadDashboard() {
  await Promise.allSettled([loadStatus(), loadHealth(), loadKeywords()]);
}

function renderDashboard(payload) {
  dashboardTitle.textContent = payload.dashboard_title;
  dashboardSubtitle.textContent = payload.dashboard_subtitle;
  updatedAt.textContent = payload.updated_at;
  errorBanner.classList.toggle("hidden", payload.status !== "error");
  errorBanner.textContent = payload.error_message || "";

  readOnlyBadge.textContent = payload.read_only ? "READ ONLY" : "COLLECT + EXPORT + OBSERVE ENABLED";
  readOnlyBadge.className = payload.status === "error"
    ? "status-pill status-error"
    : "status-pill status-ready";

  pathsGrid.innerHTML = "";
  for (const item of payload.paths || []) {
    const element = document.createElement("article");
    element.className = "path-item";
    element.innerHTML = `
      <span class="label">${escapeHtml(item.label)}</span>
      <code>${escapeHtml(item.value)}</code>
    `;
    pathsGrid.appendChild(element);
  }

  recentActions.innerHTML = "";
  for (const action of payload.recent_actions || []) {
    const panel = document.createElement("article");
    panel.className = "action-panel";
    panel.innerHTML = `
      <div class="action-panel-header">
        <h3 class="action-panel-title">${escapeHtml(action.title)}</h3>
        <span class="${statusClass(action.status)}">${escapeHtml(action.status)}</span>
      </div>
      <div class="summary-list">
        ${(action.items || []).map((item) => `
          <div class="summary-row">
            <span class="label">${escapeHtml(item.label)}</span>
            <span class="value">${escapeHtml(item.value)}</span>
          </div>
        `).join("")}
      </div>
    `;
    recentActions.appendChild(panel);
  }

  launcherList.innerHTML = "";
  for (const launcher of payload.launchers || []) {
    const element = document.createElement("article");
    element.className = "launcher-item";
    element.innerHTML = `
      <span class="label">${escapeHtml(launcher.label)}</span>
      <code>${escapeHtml(launcher.value)}</code>
    `;
    launcherList.appendChild(element);
  }

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

function renderHealth(payload) {
  const status = payload.status || "error";
  healthBadge.className = healthStatusClass(status);
  healthBadge.textContent = status;
  healthAppName.textContent = payload.app_name || "not available";
  healthServerTime.textContent = payload.server_time || "not available";
  healthSettingsLoaded.textContent = booleanLabel(payload.settings_loaded, "loaded", "not loaded");
  healthStateFileAccessible.textContent = booleanLabel(
    payload.state_file_accessible,
    "accessible",
    "not accessible",
  );
  healthObservationHistoryExists.textContent = booleanLabel(
    payload.observation_history_exists,
    "available",
    "missing",
  );
}

function renderKeywords(payload) {
  lastKeywordsPayload = payload;
  const status = payload.status || "error";
  const counts = payload.keyword_counts || {};
  const keywords = payload.keywords || {};
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
  keywordsStatusBadge.textContent = status;
  keywordsOverridePath.textContent = payload.override_path || "not available";
  keywordsOverrideExists.textContent = booleanLabel(
    payload.override_exists,
    "present",
    "missing",
  );
  keywordsLastLoadedPath.textContent = payload.last_loaded_path || "not available";
  keywordsTotalCount.textContent = String(counts.total || 0);
  keywordsCoreCount.textContent = String(
    coreDraftDirty ? coreDraftKeywords.length : (counts.core || 0),
  );
  keywordsSupportingCount.textContent = String(
    supportingDraftDirty ? supportingDraftKeywords.length : (counts.supporting || 0),
  );
  keywordsExcludeCount.textContent = String(
    excludeDraftDirty ? excludeDraftKeywords.length : (counts.exclude || 0),
  );

  if (status === "error" && payload.error_message) {
    keywordsMessage.textContent = payload.error_message;
  } else {
    keywordsMessage.textContent = "The dashboard shows the currently effective keyword set after config and override resolution.";
  }

  renderCoreKeywordEditor();
  renderSupportingKeywordEditor();
  renderExcludeKeywordEditor();
}

function renderCollectControl(payload) {
  const control = payload || defaultCollectControl();
  collectStatusBadge.className = statusClass(control.status);
  collectStatusBadge.textContent = control.status;
  collectButton.disabled = control.status === "running";

  if (control.status === "running") {
    collectMessage.textContent = "Collect is running in the background. Duplicate requests are blocked until it finishes.";
  } else if (control.status === "failed" && control.error_message) {
    collectMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    collectMessage.textContent = "Collect finished. The shared status snapshot has been refreshed.";
  } else {
    collectMessage.textContent = "Use the button once. The dashboard reuses the existing manual collect flow.";
  }

  renderMetricSummary(collectSummary, control.items || defaultCollectControl().items);
}

function renderExportControl(payload) {
  const control = payload || defaultExportControl();
  exportStatusBadge.className = statusClass(control.status);
  exportStatusBadge.textContent = control.status;
  exportButton.disabled = control.status === "running";

  if (control.status === "running") {
    exportMessage.textContent = "Export is running in the background. Duplicate export requests are blocked until it finishes.";
  } else if (control.status === "failed" && control.error_message) {
    exportMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    exportMessage.textContent = "Export finished. The latest exported file path has been refreshed.";
  } else {
    exportMessage.textContent = "Use the button once. The dashboard reuses the existing manual export flow.";
  }

  renderMetricSummary(exportSummary, control.items || defaultExportControl().items);
}

function renderObserveControl(payload) {
  const control = payload || defaultObserveControl();
  observeStatusBadge.className = statusClass(control.status);
  observeStatusBadge.textContent = control.status;
  observeButton.disabled = control.status === "running";

  if (control.status === "running") {
    observeMessage.textContent = "Observe is running in the background. Duplicate observe requests are blocked until it finishes.";
  } else if (control.status === "failed" && control.error_message) {
    observeMessage.textContent = control.error_message;
  } else if (control.status === "finished") {
    observeMessage.textContent = "Observe finished. The shared status snapshot has been refreshed with the latest observation paths.";
  } else {
    observeMessage.textContent = "Use the button once. The dashboard reuses the existing manual observe flow.";
  }

  renderMetricSummary(observeSummary, control.items || defaultObserveControl().items);
}

function renderMetricSummary(container, items) {
  container.innerHTML = "";
  for (const item of items || []) {
    const element = document.createElement("article");
    element.className = "collect-metric";
    element.innerHTML = `
      <span class="label">${escapeHtml(item.label)}</span>
      <span class="value">${escapeHtml(item.value)}</span>
    `;
    container.appendChild(element);
  }
}

function renderCoreKeywordEditor() {
  const editable = currentKeywordsStatus === "ready";
  const items = coreDraftKeywords;

  keywordsCoreInput.disabled = !editable || coreSaveInFlight;
  keywordsCoreAddButton.disabled = !editable || coreSaveInFlight;
  keywordsCoreSaveButton.disabled = (
    !editable
    || coreSaveInFlight
    || !coreDraftDirty
    || !coreDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsCoreList, items, {
    emptyText: "No core keywords in the current draft",
    removalDisabled: currentKeywordsStatus !== "ready" || coreSaveInFlight,
    onRemove: removeCoreKeyword,
  });
  renderCoreFeedback();
}

function renderSupportingKeywordEditor() {
  const editable = currentKeywordsStatus === "ready";
  const items = supportingDraftKeywords;

  keywordsSupportingInput.disabled = !editable || supportingSaveInFlight;
  keywordsSupportingAddButton.disabled = !editable || supportingSaveInFlight;
  keywordsSupportingSaveButton.disabled = (
    !editable
    || supportingSaveInFlight
    || !supportingDraftDirty
    || !supportingDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsSupportingList, items, {
    emptyText: "No supporting keywords in the current draft",
    removalDisabled: currentKeywordsStatus !== "ready" || supportingSaveInFlight,
    onRemove: removeSupportingKeyword,
  });
  renderSupportingFeedback();
}

function renderExcludeKeywordEditor() {
  const editable = currentKeywordsStatus === "ready";
  const items = excludeDraftKeywords;

  keywordsExcludeInput.disabled = !editable || excludeSaveInFlight;
  keywordsExcludeAddButton.disabled = !editable || excludeSaveInFlight;
  keywordsExcludeSaveButton.disabled = (
    !editable
    || excludeSaveInFlight
    || !excludeDraftDirty
    || !excludeDraftKeywords.length
  );

  renderEditableKeywordGroup(keywordsExcludeList, items, {
    emptyText: "No exclude keywords in the current draft",
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
        aria-label="Remove ${escapeHtml(item)}"
      >
        Remove
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
  let text = coreFeedback.text;

  if (currentKeywordsStatus !== "ready") {
    tone = "error";
    text = "Keyword snapshot is unavailable. Core keyword editing is disabled.";
  } else if (coreSaveInFlight) {
    tone = "neutral";
    text = "Saving core keywords to the override file...";
  }

  keywordsCoreMessage.className = `keyword-editor-message ${keywordFeedbackClass(tone)}`;
  keywordsCoreMessage.textContent = text;
}

function renderSupportingFeedback() {
  let tone = supportingFeedback.tone;
  let text = supportingFeedback.text;

  if (currentKeywordsStatus !== "ready") {
    tone = "error";
    text = "Keyword snapshot is unavailable. Supporting keyword editing is disabled.";
  } else if (supportingSaveInFlight) {
    tone = "neutral";
    text = "Saving supporting keywords to the override file...";
  }

  keywordsSupportingMessage.className = `keyword-editor-message ${keywordFeedbackClass(tone)}`;
  keywordsSupportingMessage.textContent = text;
}

function renderExcludeFeedback() {
  let tone = excludeFeedback.tone;
  let text = excludeFeedback.text;

  if (currentKeywordsStatus !== "ready") {
    tone = "error";
    text = "Keyword snapshot is unavailable. Exclude keyword editing is disabled.";
  } else if (excludeSaveInFlight) {
    tone = "neutral";
    text = "Saving exclude keywords to the override file...";
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
    setSupportingFeedback("error", "Keyword snapshot is unavailable, so supporting keywords cannot be edited right now.");
    renderSupportingKeywordEditor();
    return;
  }

  const keyword = normalizeKeyword(keywordsSupportingInput.value);
  if (!keyword) {
    setSupportingFeedback("error", "Enter a non-empty supporting keyword before adding it.");
    renderSupportingKeywordEditor();
    return;
  }

  if (hasKeyword(supportingDraftKeywords, keyword)) {
    setSupportingFeedback("warning", `"${keyword}" is already in the supporting keyword list.`);
    renderSupportingKeywordEditor();
    return;
  }

  supportingDraftKeywords = [...supportingDraftKeywords, keyword];
  supportingDraftDirty = true;
  keywordsSupportingInput.value = "";
  setSupportingFeedback("warning", "Unsaved supporting keyword changes are ready. Save to apply them to the override file.");
  renderSupportingKeywordEditor();
}

function addCoreKeyword() {
  if (currentKeywordsStatus !== "ready") {
    setCoreFeedback("error", "Keyword snapshot is unavailable, so core keywords cannot be edited right now.");
    renderCoreKeywordEditor();
    return;
  }

  const keyword = normalizeKeyword(keywordsCoreInput.value);
  if (!keyword) {
    setCoreFeedback("error", "Enter a non-empty core keyword before adding it.");
    renderCoreKeywordEditor();
    return;
  }

  if (hasKeyword(coreDraftKeywords, keyword)) {
    setCoreFeedback("warning", `"${keyword}" is already in the core keyword list.`);
    renderCoreKeywordEditor();
    return;
  }

  coreDraftKeywords = [...coreDraftKeywords, keyword];
  coreDraftDirty = true;
  keywordsCoreInput.value = "";
  setCoreFeedback("warning", "Unsaved core keyword changes are ready. Save to apply them to the override file.");
  renderCoreKeywordEditor();
}

function removeCoreKeyword(keyword) {
  coreDraftKeywords = coreDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  coreDraftDirty = true;
  setCoreFeedback("warning", "Unsaved core keyword changes are ready. Save to apply them to the override file.");
  renderCoreKeywordEditor();
}

async function saveCoreKeywords() {
  if (currentKeywordsStatus !== "ready") {
    setCoreFeedback("error", "Keyword snapshot is unavailable, so core keywords cannot be saved right now.");
    renderCoreKeywordEditor();
    return;
  }

  const normalizedKeywords = uniqueKeywords(coreDraftKeywords);
  if (!normalizedKeywords.length) {
    setCoreFeedback("error", "At least one core keyword must remain before saving.");
    renderCoreKeywordEditor();
    return;
  }

  coreDraftKeywords = normalizedKeywords;
  coreSaveInFlight = true;
  setCoreFeedback("neutral", "Saving core keywords to the override file...");
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
      throw new Error(payload.error_message || "Core keywords could not be saved.");
    }

    const snapshot = payload.keywords_snapshot || null;
    coreDraftDirty = false;
    const savedCoreKeywords = (((snapshot || {}).keywords || {}).core) || [];
    coreDraftKeywords = [...savedCoreKeywords];
    setCoreFeedback("success", payload.message || "Core keywords saved.");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setCoreFeedback("error", error.message);
  } finally {
    coreSaveInFlight = false;
    renderCoreKeywordEditor();
  }
}

function removeSupportingKeyword(keyword) {
  supportingDraftKeywords = supportingDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  supportingDraftDirty = true;
  setSupportingFeedback("warning", "Unsaved supporting keyword changes are ready. Save to apply them to the override file.");
  renderSupportingKeywordEditor();
}

async function saveSupportingKeywords() {
  if (currentKeywordsStatus !== "ready") {
    setSupportingFeedback("error", "Keyword snapshot is unavailable, so supporting keywords cannot be saved right now.");
    renderSupportingKeywordEditor();
    return;
  }

  const normalizedKeywords = uniqueKeywords(supportingDraftKeywords);
  if (!normalizedKeywords.length) {
    setSupportingFeedback("error", "At least one supporting keyword must remain before saving.");
    renderSupportingKeywordEditor();
    return;
  }

  supportingDraftKeywords = normalizedKeywords;
  supportingSaveInFlight = true;
  setSupportingFeedback("neutral", "Saving supporting keywords to the override file...");
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
      throw new Error(payload.error_message || "Supporting keywords could not be saved.");
    }

    const snapshot = payload.keywords_snapshot || null;
    supportingDraftDirty = false;
    const savedSupportingKeywords = (((snapshot || {}).keywords || {}).supporting) || [];
    supportingDraftKeywords = [...savedSupportingKeywords];
    setSupportingFeedback("success", payload.message || "Supporting keywords saved.");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setSupportingFeedback("error", error.message);
  } finally {
    supportingSaveInFlight = false;
    renderSupportingKeywordEditor();
  }
}

function addExcludeKeyword() {
  if (currentKeywordsStatus !== "ready") {
    setExcludeFeedback("error", "Keyword snapshot is unavailable, so exclude keywords cannot be edited right now.");
    renderExcludeKeywordEditor();
    return;
  }

  const keyword = normalizeKeyword(keywordsExcludeInput.value);
  if (!keyword) {
    setExcludeFeedback("error", "Enter a non-empty exclude keyword before adding it.");
    renderExcludeKeywordEditor();
    return;
  }

  if (hasKeyword(excludeDraftKeywords, keyword)) {
    setExcludeFeedback("warning", `"${keyword}" is already in the exclude keyword list.`);
    renderExcludeKeywordEditor();
    return;
  }

  excludeDraftKeywords = [...excludeDraftKeywords, keyword];
  excludeDraftDirty = true;
  keywordsExcludeInput.value = "";
  setExcludeFeedback("warning", "Unsaved exclude keyword changes are ready. Save to apply them to the override file.");
  renderExcludeKeywordEditor();
}

function removeExcludeKeyword(keyword) {
  excludeDraftKeywords = excludeDraftKeywords.filter((item) => !sameKeyword(item, keyword));
  excludeDraftDirty = true;
  setExcludeFeedback("warning", "Unsaved exclude keyword changes are ready. Save to apply them to the override file.");
  renderExcludeKeywordEditor();
}

async function saveExcludeKeywords() {
  if (currentKeywordsStatus !== "ready") {
    setExcludeFeedback("error", "Keyword snapshot is unavailable, so exclude keywords cannot be saved right now.");
    renderExcludeKeywordEditor();
    return;
  }

  const normalizedKeywords = uniqueKeywords(excludeDraftKeywords);
  if (!normalizedKeywords.length) {
    setExcludeFeedback("error", "At least one exclude keyword must remain before saving.");
    renderExcludeKeywordEditor();
    return;
  }

  excludeDraftKeywords = normalizedKeywords;
  excludeSaveInFlight = true;
  setExcludeFeedback("neutral", "Saving exclude keywords to the override file...");
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
      throw new Error(payload.error_message || "Exclude keywords could not be saved.");
    }

    const snapshot = payload.keywords_snapshot || null;
    excludeDraftDirty = false;
    const savedExcludeKeywords = (((snapshot || {}).keywords || {}).exclude) || [];
    excludeDraftKeywords = [...savedExcludeKeywords];
    setExcludeFeedback("success", payload.message || "Exclude keywords saved.");
    if (snapshot) {
      renderKeywords(snapshot);
    } else if (lastKeywordsPayload) {
      renderKeywords(lastKeywordsPayload);
    }
  } catch (error) {
    setExcludeFeedback("error", error.message);
  } finally {
    excludeSaveInFlight = false;
    renderExcludeKeywordEditor();
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
      error_message: `Collect request failed: ${error.message}`,
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
      error_message: `Export request failed: ${error.message}`,
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
      error_message: `Observe request failed: ${error.message}`,
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
  readOnlyBadge.textContent = "STATUS ERROR";
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

function setSupportingFeedback(tone, text) {
  supportingFeedback = { tone, text };
}

function setCoreFeedback(tone, text) {
  coreFeedback = { tone, text };
}

function setExcludeFeedback(tone, text) {
  excludeFeedback = { tone, text };
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

function booleanLabel(value, truthyLabel, falsyLabel) {
  return value ? truthyLabel : falsyLabel;
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

loadDashboard();

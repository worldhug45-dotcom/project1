FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /workspace

COPY app ./app
COPY config ./config
COPY scripts ./scripts
COPY tests/fixtures ./tests/fixtures
COPY README.md ./
COPY TASKS.md ./
COPY DECISIONS.md ./
COPY CHECKLIST.md ./

RUN mkdir -p data output doc logs

EXPOSE 8787

CMD ["python", "-m", "app.presentation.web.server", "--host", "0.0.0.0", "--port", "8787", "--config", "config/settings.docker.toml", "--history-path", "data/observations/bizinfo/collect_observations.json", "--raw-output-dir", "data/observations/bizinfo/raw", "--log-path", "doc/bizinfo_collect_observation_log.md", "--state-path", "data/operations/manual_run_state.json"]

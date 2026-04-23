"""Web dashboard server for internal operators."""

from __future__ import annotations

import argparse
import json
import mimetypes
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlparse

from app.application import (
    OperatorCollectService,
    OperatorExportService,
    OperatorObserveService,
)
from app.infrastructure.manual_run_gateway import (
    ManualRunCollectGateway,
    ManualRunExportGateway,
    ManualRunObserveGateway,
)
from app.infrastructure.settings import ConfigurationError, load_settings
from app.ops import (
    OperatorStatusSnapshot,
    build_unavailable_health_snapshot,
    build_unavailable_keywords_snapshot,
    build_unavailable_settings_snapshot,
    load_operator_health_snapshot,
    load_operator_keywords_snapshot,
    load_operator_settings_snapshot,
    load_operator_status_snapshot,
    save_operator_api_keys,
    save_operator_core_keywords,
    save_operator_exclude_keywords,
    save_operator_sources,
    save_operator_supporting_keywords,
)
from app.presentation.web.viewmodels import (
    build_dashboard_error_view_model,
    build_dashboard_view_model,
)


WEB_ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = WEB_ROOT / "templates" / "dashboard.html"
STATIC_ROOT = WEB_ROOT / "static"
DEFAULT_CONFIG_PATH = Path("config/settings.local.toml")
DEFAULT_HISTORY_PATH = Path("data/observations/bizinfo/collect_observations.json")
DEFAULT_RAW_OUTPUT_DIR = Path("data/observations/bizinfo/raw")
DEFAULT_LOG_PATH = Path("doc/bizinfo_collect_observation_log.md")
DEFAULT_STATE_PATH = Path("data/operations/manual_run_state.json")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


@dataclass(frozen=True, slots=True)
class DashboardServerSettings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    config_path: Path = DEFAULT_CONFIG_PATH
    history_path: Path = DEFAULT_HISTORY_PATH
    raw_output_dir: Path = DEFAULT_RAW_OUTPUT_DIR
    log_path: Path = DEFAULT_LOG_PATH
    state_path: Path = DEFAULT_STATE_PATH


@dataclass(frozen=True, slots=True)
class DashboardServerContext:
    settings: DashboardServerSettings
    status_loader: Callable[[], OperatorStatusSnapshot]
    collect_service: OperatorCollectService
    export_service: OperatorExportService
    observe_service: OperatorObserveService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project1_dashboard",
        description="Operator dashboard with shared status plus collect/export/observe control.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host binding.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port binding.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Settings file used for status resolution.",
    )
    parser.add_argument(
        "--history-path",
        type=Path,
        default=DEFAULT_HISTORY_PATH,
        help="Observation history JSON path.",
    )
    parser.add_argument(
        "--raw-output-dir",
        type=Path,
        default=DEFAULT_RAW_OUTPUT_DIR,
        help="Observation raw JSONL directory.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Observation Markdown report path.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Manual runner state JSON path.",
    )
    return parser


def create_server(
    settings: DashboardServerSettings,
    *,
    context: DashboardServerContext | None = None,
) -> ThreadingHTTPServer:
    server_context = context or _build_context(settings)
    handler = partial(DashboardRequestHandler, context=server_context)
    return ThreadingHTTPServer((settings.host, settings.port), handler)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = DashboardServerSettings(
        host=args.host,
        port=args.port,
        config_path=args.config,
        history_path=args.history_path,
        raw_output_dir=args.raw_output_dir,
        log_path=args.log_path,
        state_path=args.state_path,
    )
    server = create_server(settings)
    server_address = server.server_address
    host = server_address[0]
    port = server_address[1]
    display_host = host.decode("utf-8") if isinstance(host, bytes) else host
    print(
        "Project1 dashboard listening at "
        f"http://{display_host}:{port} "
        f"(config={settings.config_path})"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Project1 dashboard stopped.")
    finally:
        server.server_close()
    return 0


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves the operator dashboard shell."""

    def __init__(self, *args, context: DashboardServerContext, **kwargs) -> None:
        self.context = context
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_dashboard_html(page="dashboard")
            return
        if parsed.path == "/settings":
            self._serve_dashboard_html(page="settings")
            return
        if parsed.path == "/api/status":
            self._serve_status_json()
            return
        if parsed.path == "/api/keywords":
            self._serve_keywords_json()
            return
        if parsed.path == "/api/settings":
            self._serve_settings_json()
            return
        if parsed.path == "/health":
            self._serve_health_json()
            return
        if parsed.path.startswith("/artifacts/"):
            self._serve_artifact(parsed)
            return
        if parsed.path.startswith("/static/"):
            self._serve_static(parsed.path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        parsed = urlparse(self.path)
        if parsed.path == "/api/keywords/core":
            self._handle_core_keywords_save()
            return
        if parsed.path == "/api/keywords/supporting":
            self._handle_supporting_keywords_save()
            return
        if parsed.path == "/api/keywords/exclude":
            self._handle_exclude_keywords_save()
            return
        if parsed.path == "/api/settings/sources":
            self._handle_settings_sources_save()
            return
        if parsed.path == "/api/settings/api-keys":
            self._handle_settings_api_keys_save()
            return
        if parsed.path == "/actions/collect":
            self._handle_collect_action()
            return
        if parsed.path == "/actions/export":
            self._handle_export_action()
            return
        if parsed.path == "/actions/observe":
            self._handle_observe_action()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - framework name
        return

    def _serve_dashboard_html(self, *, page: str) -> None:
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
        html = html.replace("__STATUS_API_URL__", "/api/status")
        html = html.replace("__KEYWORDS_API_URL__", "/api/keywords")
        html = html.replace("__SETTINGS_API_URL__", "/api/settings")
        html = html.replace(
            "__KEYWORDS_CORE_SAVE_URL__",
            "/api/keywords/core",
        )
        html = html.replace(
            "__KEYWORDS_SUPPORTING_SAVE_URL__",
            "/api/keywords/supporting",
        )
        html = html.replace(
            "__KEYWORDS_EXCLUDE_SAVE_URL__",
            "/api/keywords/exclude",
        )
        html = html.replace("__HEALTH_API_URL__", "/health")
        html = html.replace("__SETTINGS_SOURCES_SAVE_URL__", "/api/settings/sources")
        html = html.replace("__SETTINGS_API_KEYS_SAVE_URL__", "/api/settings/api-keys")
        html = html.replace("__COLLECT_ACTION_URL__", "/actions/collect")
        html = html.replace("__EXPORT_ACTION_URL__", "/actions/export")
        html = html.replace("__OBSERVE_ACTION_URL__", "/actions/observe")
        html = html.replace("__CURRENT_PAGE__", page)
        html = html.replace(
            "__DASHBOARD_ACTIVE__",
            "is-active" if page == "dashboard" else "",
        )
        html = html.replace(
            "__SETTINGS_ACTIVE__",
            "is-active" if page == "settings" else "",
        )
        self._send_bytes_response(
            HTTPStatus.OK,
            "text/html; charset=utf-8",
            html.encode("utf-8"),
        )

    def _serve_status_json(self) -> None:
        try:
            snapshot = self.context.status_loader()
            payload = build_dashboard_view_model(
                snapshot,
                collect_control=self.context.collect_service.get_state(),
                export_control=self.context.export_service.get_state(),
                observe_control=self.context.observe_service.get_state(),
            )
            status_code = HTTPStatus.OK
        except ConfigurationError as exc:
            payload = build_dashboard_error_view_model(str(exc))
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR

        self._send_json_response(status_code, payload)

    def _serve_health_json(self) -> None:
        try:
            payload = load_operator_health_snapshot(
                config_path=self.context.settings.config_path,
                history_path=self.context.settings.history_path,
                state_path=self.context.settings.state_path,
            ).to_dict()
        except Exception:
            payload = build_unavailable_health_snapshot(self.context.settings.config_path).to_dict()

        status_code = (
            HTTPStatus.OK
            if payload["status"] in {"ok", "degraded"}
            else HTTPStatus.SERVICE_UNAVAILABLE
        )
        self._send_json_response(status_code, payload)

    def _serve_keywords_json(self) -> None:
        try:
            payload = load_operator_keywords_snapshot(
                config_path=self.context.settings.config_path,
            ).to_dict()
            status_code = HTTPStatus.OK
        except ConfigurationError as exc:
            payload = build_unavailable_keywords_snapshot(
                self.context.settings.config_path,
                str(exc),
            ).to_dict()
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception:
            payload = build_unavailable_keywords_snapshot(
                self.context.settings.config_path,
                "Keyword snapshot could not be loaded.",
            ).to_dict()
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR

        self._send_json_response(status_code, payload)

    def _serve_settings_json(self) -> None:
        try:
            payload = load_operator_settings_snapshot(
                config_path=self.context.settings.config_path,
            ).to_dict()
            status_code = HTTPStatus.OK
        except ConfigurationError as exc:
            payload = build_unavailable_settings_snapshot(
                self.context.settings.config_path,
                str(exc),
            ).to_dict()
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception:
            payload = build_unavailable_settings_snapshot(
                self.context.settings.config_path,
                "Settings snapshot could not be loaded.",
            ).to_dict()
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR

        self._send_json_response(status_code, payload)

    def _handle_collect_action(self) -> None:
        started, state = self.context.collect_service.start_collect()
        status_code = HTTPStatus.ACCEPTED if started else HTTPStatus.OK
        self._send_json_response(
            status_code,
            {
                "started": started,
                "collect_control": state.to_dict(),
            },
        )

    def _handle_export_action(self) -> None:
        started, state = self.context.export_service.start_export()
        status_code = HTTPStatus.ACCEPTED if started else HTTPStatus.OK
        self._send_json_response(
            status_code,
            {
                "started": started,
                "export_control": state.to_dict(),
            },
        )

    def _handle_observe_action(self) -> None:
        started, state = self.context.observe_service.start_observe()
        status_code = HTTPStatus.ACCEPTED if started else HTTPStatus.OK
        self._send_json_response(
            status_code,
            {
                "started": started,
                "observe_control": state.to_dict(),
            },
        )

    def _handle_supporting_keywords_save(self) -> None:
        try:
            payload = self._read_json_request_body()
            supporting_keywords = payload.get("supporting_keywords")
            if not isinstance(supporting_keywords, list):
                raise ConfigurationError("supporting_keywords must be provided as an array.")

            snapshot = save_operator_supporting_keywords(
                config_path=self.context.settings.config_path,
                supporting_keywords=supporting_keywords,
            )
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": "Request body must be valid JSON.",
                },
            )
            return
        except ConfigurationError as exc:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": str(exc),
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "saved": False,
                    "error_message": "Supporting keywords could not be saved.",
                },
            )
            return

        self._send_json_response(
            HTTPStatus.OK,
            {
                "saved": True,
                "message": "Supporting keywords saved.",
                "keywords_snapshot": snapshot.to_dict(),
            },
        )

    def _handle_core_keywords_save(self) -> None:
        try:
            payload = self._read_json_request_body()
            core_keywords = payload.get("core_keywords")
            if not isinstance(core_keywords, list):
                raise ConfigurationError("core_keywords must be provided as an array.")

            snapshot = save_operator_core_keywords(
                config_path=self.context.settings.config_path,
                core_keywords=core_keywords,
            )
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": "Request body must be valid JSON.",
                },
            )
            return
        except ConfigurationError as exc:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": str(exc),
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "saved": False,
                    "error_message": "Core keywords could not be saved.",
                },
            )
            return

        self._send_json_response(
            HTTPStatus.OK,
            {
                "saved": True,
                "message": "Core keywords saved.",
                "keywords_snapshot": snapshot.to_dict(),
            },
        )

    def _handle_exclude_keywords_save(self) -> None:
        try:
            payload = self._read_json_request_body()
            exclude_keywords = payload.get("exclude_keywords")
            if not isinstance(exclude_keywords, list):
                raise ConfigurationError("exclude_keywords must be provided as an array.")

            snapshot = save_operator_exclude_keywords(
                config_path=self.context.settings.config_path,
                exclude_keywords=exclude_keywords,
            )
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": "Request body must be valid JSON.",
                },
            )
            return
        except ConfigurationError as exc:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": str(exc),
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "saved": False,
                    "error_message": "Exclude keywords could not be saved.",
                },
            )
            return

        self._send_json_response(
            HTTPStatus.OK,
            {
                "saved": True,
                "message": "Exclude keywords saved.",
                "keywords_snapshot": snapshot.to_dict(),
            },
        )

    def _handle_settings_sources_save(self) -> None:
        try:
            payload = self._read_json_request_body()
            sources_payload = payload.get("sources")
            source_mode = payload.get("source_mode")
            extra_sources = payload.get("extra_sources", [])
            if not isinstance(sources_payload, dict):
                raise ConfigurationError("sources must be provided as an object.")
            if source_mode is not None and not isinstance(source_mode, str):
                raise ConfigurationError("source_mode must be provided as a string.")
            if not isinstance(extra_sources, list):
                raise ConfigurationError("extra_sources must be provided as an array.")

            snapshot = save_operator_sources(
                config_path=self.context.settings.config_path,
                source_overrides=sources_payload,
                source_mode=source_mode,
                extra_sources=extra_sources,
            )
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": "Request body must be valid JSON.",
                },
            )
            return
        except ConfigurationError as exc:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": str(exc),
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "saved": False,
                    "error_message": "Source settings could not be saved.",
                },
            )
            return

        self._send_json_response(
            HTTPStatus.OK,
            {
                "saved": True,
                "message": "Source settings saved.",
                "settings_snapshot": snapshot.to_dict(),
            },
        )

    def _handle_settings_api_keys_save(self) -> None:
        try:
            payload = self._read_json_request_body()
            bizinfo_api_key = payload.get("bizinfo_api_key")
            g2b_api_key = payload.get("g2b_api_key")
            if bizinfo_api_key is not None and not isinstance(bizinfo_api_key, str):
                raise ConfigurationError("bizinfo_api_key must be provided as a string.")
            if g2b_api_key is not None and not isinstance(g2b_api_key, str):
                raise ConfigurationError("g2b_api_key must be provided as a string.")

            snapshot = save_operator_api_keys(
                config_path=self.context.settings.config_path,
                bizinfo_api_key=bizinfo_api_key,
                g2b_api_key=g2b_api_key,
            )
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": "Request body must be valid JSON.",
                },
            )
            return
        except ConfigurationError as exc:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "saved": False,
                    "error_message": str(exc),
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "saved": False,
                    "error_message": "API key settings could not be saved.",
                },
            )
            return

        self._send_json_response(
            HTTPStatus.OK,
            {
                "saved": True,
                "message": "API key settings saved.",
                "settings_snapshot": snapshot.to_dict(),
            },
        )

    def _serve_static(self, request_path: str) -> None:
        relative_path = PurePosixPath(request_path.removeprefix("/static/"))
        asset_path = (STATIC_ROOT / Path(relative_path)).resolve()
        static_root = STATIC_ROOT.resolve()
        if static_root not in asset_path.parents and asset_path != static_root:
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return
        if not asset_path.exists() or not asset_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_type, _encoding = mimetypes.guess_type(asset_path.name)
        self._send_bytes_response(
            HTTPStatus.OK,
            content_type or "application/octet-stream",
            asset_path.read_bytes(),
        )

    def _serve_artifact(self, parsed) -> None:
        download = parse_qs(parsed.query).get("download", ["0"])[0].lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        try:
            target_path = self._resolve_artifact_target(parsed.path)
        except ConfigurationError:
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return

        if not target_path.exists() or not target_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_type, _encoding = mimetypes.guess_type(target_path.name)
        extra_headers = {}
        if download:
            extra_headers["Content-Disposition"] = f'attachment; filename="{target_path.name}"'

        self._send_bytes_response(
            HTTPStatus.OK,
            content_type or "application/octet-stream",
            target_path.read_bytes(),
            extra_headers=extra_headers,
        )

    def _resolve_artifact_target(self, request_path: str) -> Path:
        if request_path == "/artifacts/report":
            return self.context.settings.log_path

        if request_path.startswith("/artifacts/export/"):
            relative_path = unquote(request_path.removeprefix("/artifacts/export/"))
            export_root = self._load_export_output_dir()
            return self._resolve_relative_artifact_path(export_root, relative_path)

        if request_path.startswith("/artifacts/raw/"):
            relative_path = unquote(request_path.removeprefix("/artifacts/raw/"))
            return self._resolve_relative_artifact_path(
                self.context.settings.raw_output_dir,
                relative_path,
            )

        raise ConfigurationError("Artifact route is not allowed.")

    def _resolve_relative_artifact_path(self, root: Path, relative_path: str) -> Path:
        normalized_relative = PurePosixPath(relative_path)
        if not normalized_relative.parts or normalized_relative.is_absolute():
            raise ConfigurationError("Artifact path is required.")

        root_resolved = root.resolve()
        candidate = (root_resolved / Path(normalized_relative)).resolve()
        if root_resolved not in candidate.parents and candidate != root_resolved:
            raise ConfigurationError("Artifact path escapes the allowed root.")
        return candidate

    def _load_export_output_dir(self) -> Path:
        settings = load_settings(
            self.context.settings.config_path,
            cli_overrides={"action": "export"},
        )
        return settings.export.output_dir

    def _send_json_response(
        self,
        status: HTTPStatus,
        payload: dict[str, object],
    ) -> None:
        self._send_bytes_response(
            status,
            "application/json; charset=utf-8",
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

    def _read_json_request_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ConfigurationError("JSON payload must be an object.")
        return payload

    def _send_bytes_response(
        self,
        status: HTTPStatus,
        content_type: str,
        payload: bytes,
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)


def _build_context(settings: DashboardServerSettings) -> DashboardServerContext:
    status_loader = partial(
        load_operator_status_snapshot,
        config_path=settings.config_path,
        history_path=settings.history_path,
        raw_output_dir=settings.raw_output_dir,
        log_path=settings.log_path,
        state_path=settings.state_path,
    )
    gateway = ManualRunCollectGateway(
        config_path=settings.config_path,
        state_path=settings.state_path,
    )
    export_gateway = ManualRunExportGateway(
        config_path=settings.config_path,
        state_path=settings.state_path,
    )
    observe_gateway = ManualRunObserveGateway(
        config_path=settings.config_path,
        history_path=settings.history_path,
        raw_output_dir=settings.raw_output_dir,
        log_path=settings.log_path,
        state_path=settings.state_path,
    )
    collect_service = OperatorCollectService(
        status_loader=status_loader,
        runner=gateway.run_collect,
    )
    export_service = OperatorExportService(
        status_loader=status_loader,
        runner=export_gateway.run_export,
    )
    observe_service = OperatorObserveService(
        status_loader=status_loader,
        runner=observe_gateway.run_observe,
    )
    return DashboardServerContext(
        settings=settings,
        status_loader=status_loader,
        collect_service=collect_service,
        export_service=export_service,
        observe_service=observe_service,
    )


if __name__ == "__main__":
    raise SystemExit(main())

"""Infrastructure gateway that reuses the existing manual_run collect path."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app.application.operator_dashboard import (
    CollectExecutionResult,
    ExportExecutionResult,
    ObserveExecutionResult,
)
from app.infrastructure.local_env import build_runtime_environ


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ManualRunCollectGateway:
    """Execute collect by reusing the existing manual_run CLI flow."""

    config_path: Path
    state_path: Path

    def run_collect(self) -> CollectExecutionResult:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "manual_run.py"),
            "collect",
            "--config",
            str(self.config_path),
            "--state-path",
            str(self.state_path),
        ]
        child_environ = build_runtime_environ(os.environ.copy(), config_path=self.config_path)
        child_environ["PYTHONIOENCODING"] = "utf-8"
        child_environ["PYTHONUTF8"] = "1"
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=child_environ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return CollectExecutionResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True, slots=True)
class ManualRunExportGateway:
    """Execute export by reusing the existing manual_run CLI flow."""

    config_path: Path
    state_path: Path

    def run_export(self) -> ExportExecutionResult:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "manual_run.py"),
            "export",
            "--config",
            str(self.config_path),
            "--state-path",
            str(self.state_path),
        ]
        child_environ = build_runtime_environ(os.environ.copy(), config_path=self.config_path)
        child_environ["PYTHONIOENCODING"] = "utf-8"
        child_environ["PYTHONUTF8"] = "1"
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=child_environ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return ExportExecutionResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True, slots=True)
class ManualRunObserveGateway:
    """Execute observe by reusing the existing manual_run CLI flow."""

    config_path: Path
    history_path: Path
    raw_output_dir: Path
    log_path: Path
    state_path: Path

    def run_observe(self) -> ObserveExecutionResult:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "manual_run.py"),
            "observe",
            "--config",
            str(self.config_path),
            "--history-path",
            str(self.history_path),
            "--raw-output-dir",
            str(self.raw_output_dir),
            "--log-path",
            str(self.log_path),
            "--state-path",
            str(self.state_path),
        ]
        child_environ = build_runtime_environ(os.environ.copy(), config_path=self.config_path)
        child_environ["PYTHONIOENCODING"] = "utf-8"
        child_environ["PYTHONUTF8"] = "1"
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=child_environ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return ObserveExecutionResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

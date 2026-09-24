#!/usr/bin/env python3
"""Run Pi in JSON event mode and persist eval evidence."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Optional

from skill_eval_utils import IsolatedArm


SENSITIVE_NAMES = {
    ".credentials.json",
    "auth.json",
    "credentials.json",
    "settings.local.json",
}

# Upstream provider failures that clear up on their own (opencode-go intermittently
# returns 400 "reasoning_effort is not allowed" for an otherwise valid request).
# Timeouts and local exit codes without these markers are NOT retried: a slow or
# broken run retried at 10-20 minutes per attempt would double the round's cost.
TRANSIENT_MARKERS = (
    "upstream request failed",
    "400:",
    "429",
    "502",
    "503",
    "504",
    "econnreset",
    "rate limit",
    "overloaded",
    "temporarily unavailable",
)
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 5


@dataclass(frozen=True)
class PiRunResult:
    raw: str
    events: list[dict]
    output: str
    provider: Optional[str]
    model: Optional[str]
    usage: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    files_read: list[str]
    files_modified: list[str]
    commands: list[str]
    errors: list[str]
    fatal_error: Optional[str]
    attempts: int = 1

    def transcript_summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for call in self.tool_calls:
            name = str(call.get("name", "unknown"))
            counts[name] = counts.get(name, 0) + 1
        return {
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage,
            "tool_calls": counts,
            "files_read": self.files_read,
            "files_modified": self.files_modified,
            "commands": self.commands,
            "errors": self.errors,
            "fatal_error": self.fatal_error,
            "output": self.output,
        }


def _number(value: Any) -> float | int:
    return value if isinstance(value, (int, float)) else 0


def _sum_usage(assistant_messages: list[dict]) -> dict[str, Any]:
    usage_keys = (
        "input",
        "output",
        "cacheRead",
        "cacheWrite",
        "reasoning",
        "totalTokens",
    )
    cost_keys = ("input", "output", "cacheRead", "cacheWrite", "total")
    usage = {key: 0 for key in usage_keys}
    cost = {key: 0 for key in cost_keys}
    for message in assistant_messages:
        raw_usage = message.get("usage") or {}
        for key in usage_keys:
            usage[key] += _number(raw_usage.get(key))
        raw_cost = raw_usage.get("cost") or {}
        for key in cost_keys:
            cost[key] += _number(raw_cost.get(key))
    usage["cost"] = cost
    return usage


def _result_excerpt(value: Any, limit: int = 500) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            text = repr(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _collect_tool_calls(events: list[dict]) -> tuple[list[dict], list[str], list[str], list[str]]:
    calls: list[dict] = []
    by_id: dict[str, dict] = {}
    files_read: list[str] = []
    files_modified: list[str] = []
    commands: list[str] = []
    errors: list[str] = []

    for event in events:
        event_type = event.get("type")
        if event_type == "tool_execution_start":
            call_id = str(event.get("toolCallId", ""))
            name = str(event.get("toolName", "unknown"))
            args = event.get("args") or {}
            call = {
                "id": call_id,
                "name": name,
                "args": args,
                "isError": False,
                "result": None,
            }
            calls.append(call)
            if call_id:
                by_id[call_id] = call
            if name == "read" and isinstance(args.get("path"), str):
                files_read.append(args["path"])
            elif name in {"edit", "write", "apply_patch"}:
                path = args.get("path") or args.get("file_path")
                if isinstance(path, str):
                    files_modified.append(path)
            elif name == "bash" and isinstance(args.get("command"), str):
                commands.append(args["command"])
        elif event_type == "tool_execution_end":
            call_id = str(event.get("toolCallId", ""))
            call = by_id.get(call_id)
            if call is None:
                call = {
                    "id": call_id,
                    "name": "unknown",
                    "args": {},
                    "isError": False,
                    "result": None,
                }
                calls.append(call)
                if call_id:
                    by_id[call_id] = call
            call["isError"] = bool(event.get("isError"))
            call["result"] = _result_excerpt(event.get("result"))
            if call["isError"]:
                errors.append(f"{call['name']}: {call['result'] or 'tool error'}")

    return calls, files_read, files_modified, commands, errors


def parse_pi_events(raw: str) -> PiRunResult:
    events = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"pi JSON event stream has invalid JSON at line {line_number}: {exc}"
            ) from exc
        if not isinstance(event, dict):
            raise RuntimeError(f"pi JSON event at line {line_number} is not an object")
        events.append(event)

    if not events:
        raise RuntimeError("pi JSON event stream was empty")

    assistant_messages = [
        event.get("message") or {}
        for event in events
        if event.get("type") == "message_end"
        and (event.get("message") or {}).get("role") == "assistant"
    ]
    if not assistant_messages:
        raise RuntimeError("pi JSON event stream contained no assistant message")

    final_message = assistant_messages[-1]
    text_blocks = [
        block.get("text", "")
        for block in final_message.get("content") or []
        if block.get("type") == "text"
    ]
    output = "\n".join(text for text in text_blocks if text).strip()
    tool_calls, files_read, files_modified, commands, tool_errors = _collect_tool_calls(
        events
    )

    errors = list(tool_errors)
    fatal_error = None
    if final_message.get("stopReason") == "error":
        fatal_error = str(final_message.get("errorMessage") or "assistant error")
        errors.append(fatal_error)

    return PiRunResult(
        raw=raw,
        events=events,
        output=output,
        provider=final_message.get("provider"),
        model=final_message.get("model"),
        usage=_sum_usage(assistant_messages),
        tool_calls=tool_calls,
        files_read=sorted(set(files_read)),
        files_modified=sorted(set(files_modified)),
        commands=commands,
        errors=errors,
        fatal_error=fatal_error,
    )


def require_success(result: PiRunResult) -> None:
    if result.fatal_error:
        raise RuntimeError(f"pi run failed: {result.fatal_error}")


def run_setup(
    commands: list[str],
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
) -> None:
    for command in commands:
        try:
            completed = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=dict(env),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"eval setup timed out after {timeout}s: {command}") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[-500:]
            raise RuntimeError(
                f"eval setup failed ({completed.returncode}): {command}: {detail}"
            )


def is_transient(message: str) -> bool:
    """True when an error matches a known self-clearing upstream failure."""
    lowered = message.lower()
    return any(marker in lowered for marker in TRANSIENT_MARKERS)


def run_pi(
    provider: str,
    model: str,
    args: list[str],
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
) -> PiRunResult:
    """Run pi once per attempt, retrying transient upstream failures with backoff.

    Non-transient failures (timeouts, local exits, malformed streams) raise
    immediately; a provider 400/429/5xx that survives RETRY_ATTEMPTS raises too,
    so real failures still surface as run errors instead of vanishing.
    """
    command = [
        "pi",
        "--mode",
        "json",
        "--no-session",
        "--provider",
        provider,
        "--model",
        model,
        *args,
    ]
    attempt = 0
    while True:
        attempt += 1
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=dict(env),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"pi call timed out after {timeout}s") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[-500:]
            failure = RuntimeError(f"pi exited {completed.returncode}: {detail}")
            if attempt < RETRY_ATTEMPTS and is_transient(detail):
                time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)
                continue
            raise failure
        try:
            result = parse_pi_events(completed.stdout)
        except RuntimeError as exc:
            if attempt < RETRY_ATTEMPTS and is_transient(str(exc)):
                time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)
                continue
            raise
        if (
            result.fatal_error
            and attempt < RETRY_ATTEMPTS
            and is_transient(result.fatal_error)
        ):
            time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)
            continue
        return replace(result, attempts=attempt)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_tree(root: Path) -> dict[str, Any]:
    root = Path(root)
    files = []
    symlinks = []
    directories = []
    if not root.exists():
        return {"root": str(root), "files": files, "symlinks": symlinks}

    for current, dirnames, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        rel_root = current_path.relative_to(root)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in SENSITIVE_NAMES and not (rel_root / name).is_symlink()
        )
        for name in dirnames:
            path = current_path / name
            rel = (rel_root / name).as_posix()
            if path.is_symlink():
                symlinks.append({"path": rel, "target": os.readlink(path)})
            else:
                directories.append(rel)
        for name in sorted(filenames):
            if name in SENSITIVE_NAMES or name.endswith(".pyc"):
                continue
            path = current_path / name
            rel = (rel_root / name).as_posix()
            if path.is_symlink():
                symlinks.append({"path": rel, "target": os.readlink(path)})
            elif path.is_file():
                files.append(
                    {
                        "path": rel,
                        "size": path.stat().st_size,
                        "sha256": _file_sha256(path),
                    }
                )
    return {
        "root": str(root),
        "directories": sorted(directories),
        "files": sorted(files, key=lambda item: item["path"]),
        "symlinks": sorted(symlinks, key=lambda item: item["path"]),
    }


def environment_manifest(arm: IsolatedArm) -> dict[str, Any]:
    return {
        "workspace": manifest_tree(arm.workdir),
        "home": manifest_tree(arm.home),
        "profile": manifest_tree(arm.profile_dir),
    }


def write_run_evidence(directory: Path, result: PiRunResult, arm: IsolatedArm) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "events.jsonl").write_text(result.raw)
    (directory / "transcript.json").write_text(
        json.dumps(result.transcript_summary(), indent=2, sort_keys=True) + "\n"
    )
    (directory / "environment.json").write_text(
        json.dumps(environment_manifest(arm), indent=2, sort_keys=True) + "\n"
    )

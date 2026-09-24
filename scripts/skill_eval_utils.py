#!/usr/bin/env python3
"""Isolation and fingerprint helpers shared by the skill evaluation runners.

Every target/control/judge invocation gets its own workspace, HOME, XDG
directories, and pi profile. Model calls may therefore mutate their arm
without affecting any other arm.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional


EVAL_PROTOCOL_VERSION = 1
IGNORED_HASH_NAMES = {".git", ".DS_Store", "__pycache__", "node_modules"}


@dataclass(frozen=True)
class IsolatedArm:
    """Paths and environment for one independently disposable agent run."""

    name: str
    root: Path
    workdir: Path
    home: Path
    profiles_root: Path
    profile_dir: Path
    profile_name: str


def _safe_remove(path: Path) -> None:
    """Remove a generated run directory, refusing filesystem roots."""
    if path == Path(path.anchor):
        raise ValueError(f"refusing to remove filesystem root: {path}")
    if path.exists():
        shutil.rmtree(path)


def normalize_fixture_spec(value) -> dict[str, str]:
    if isinstance(value, str):
        source = value
        destination = Path(value).name
    elif isinstance(value, dict):
        source = value.get("source")
        destination = value.get("dest")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("fixture object requires a non-empty 'source'")
        if not isinstance(destination, str) or not destination.strip():
            raise ValueError("fixture object requires a non-empty 'dest'")
    else:
        raise ValueError(f"invalid fixture entry: {value!r}")

    source_path = Path(source)
    destination_path = Path(destination)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise ValueError(f"fixture source must stay inside the skill: {source}")
    if destination_path.is_absolute() or ".." in destination_path.parts:
        raise ValueError(f"fixture destination must stay inside the arm: {destination}")
    return {"source": source, "dest": destination}


def _copy_fixture(source_dir: Path, fixture, workdir: Path) -> None:
    spec = normalize_fixture_spec(fixture)
    source = source_dir / spec["source"]
    if not source.exists():
        raise FileNotFoundError(f"fixture missing: {spec['source']}")

    destination = workdir / spec["dest"]
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def prepare_isolated_arms(
    base_dir: Path,
    source_dir: Path,
    files: Iterable[str],
    names: Iterable[str],
    profile_name: str,
) -> dict[str, IsolatedArm]:
    """Create fresh, identically-staged but mutually isolated arms.

    ``base_dir`` is removed first so repeated runs cannot inherit stale files.
    Each arm receives its own workspace, HOME, XDG roots, and profile path.
    """
    _safe_remove(base_dir)
    files = list(files)
    arms: dict[str, IsolatedArm] = {}
    for name in names:
        root = base_dir / name
        workdir = root / "work"
        home = root / "home"
        profiles_root = root / "profiles"
        for directory in (
            workdir,
            home,
            profiles_root,
            root / "xdg-cache",
            root / "xdg-config",
            root / "xdg-state",
        ):
            directory.mkdir(parents=True, exist_ok=True)

        for rel in files:
            _copy_fixture(source_dir, rel, workdir)

        arms[name] = IsolatedArm(
            name=name,
            root=root,
            workdir=workdir,
            home=home,
            profiles_root=profiles_root,
            profile_dir=profiles_root / profile_name,
            profile_name=profile_name,
        )
    return arms


def clean_base_environment(
    environment: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    """Return an environment with user-level pi/XDG paths removed."""
    env = dict(os.environ if environment is None else environment)
    real_home = Path(env.get("HOME") or Path.home())
    profile_base = env.get("EVAL_PROFILE_BASE_DIR")
    env["PI_PROFILE_BASE_DIR"] = str(
        Path(profile_base).expanduser()
        if profile_base
        else real_home / ".pi" / "agent"
    )
    for key in (
        "HOME",
        "PI_CODING_AGENT_DIR",
        "PI_PROFILES_ROOT",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_STATE_HOME",
    ):
        env.pop(key, None)
    return env


def create_isolated_profile(
    arm: IsolatedArm,
    base_env: Mapping[str, str],
) -> dict[str, str]:
    """Create this arm's pi profile and return its invocation environment."""
    creation_env = dict(base_env)
    creation_env.update(
        HOME=str(arm.home),
        PI_PROFILES_ROOT=str(arm.profiles_root),
        XDG_CACHE_HOME=str(arm.root / "xdg-cache"),
        XDG_CONFIG_HOME=str(arm.root / "xdg-config"),
        XDG_STATE_HOME=str(arm.root / "xdg-state"),
    )
    completed = subprocess.run(
        ["pi-profile", "create", arm.profile_name],
        check=False,
        capture_output=True,
        text=True,
        env=creation_env,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-500:]
        raise RuntimeError(
            f"pi-profile create failed for {arm.name} "
            f"(exit {completed.returncode}): {detail}"
        )
    if not arm.profile_dir.is_dir():
        raise RuntimeError(
            f"pi-profile reported success but profile is missing: {arm.profile_dir}"
        )

    run_env = dict(creation_env)
    run_env["PI_CODING_AGENT_DIR"] = str(arm.profile_dir)
    return run_env


def install_skill_copies(
    profile_dir: Path,
    skills_root: Path,
    exclude: Optional[set[str]] = None,
) -> None:
    """Copy the catalog into a profile, optionally omitting target skills."""
    excluded = exclude or set()
    profile_skills = profile_dir / "skills"
    if profile_skills.exists():
        shutil.rmtree(profile_skills)
    profile_skills.mkdir(parents=True)
    for source in sorted(skills_root.iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        destination = profile_skills / source.name
        if source.name in excluded:
            if destination.exists() or destination.is_symlink():
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            continue
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        shutil.copytree(source, destination)


def canonical_json_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_json(value) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def hash_path(path: Path, excluded_dirs: Optional[set[str]] = None) -> str:
    """Hash a file, symlink, or deterministic directory tree by content."""
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()

    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8"))
        return digest.hexdigest()
    if path.is_file():
        digest.update(b"file\0")
        digest.update(path.read_bytes())
        return digest.hexdigest()
    if not path.is_dir():
        raise ValueError(f"unsupported path type: {path}")

    excluded = excluded_dirs or set()
    digest.update(b"directory\0")
    for root, dirnames, filenames in os.walk(path, followlinks=False):
        rel_root = Path(root).relative_to(path)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in IGNORED_HASH_NAMES and name not in excluded
        )
        for name in sorted(filenames):
            if name in IGNORED_HASH_NAMES or name.endswith(".pyc"):
                continue
            item = Path(root) / name
            rel = rel_root / name
            digest.update(str(rel.as_posix()).encode("utf-8"))
            digest.update(b"\0")
            if item.is_symlink():
                digest.update(b"symlink\0")
                digest.update(os.readlink(item).encode("utf-8"))
            else:
                digest.update(b"file\0")
                digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def hash_skill_definition(skill_dir: Path) -> str:
    # Eval cases and fixtures do not ship inside the runtime skill. Hash them
    # separately so a change to case B does not invalidate case A.
    return hash_path(skill_dir, excluded_dirs={"evals"})


def _hash_profile_file(path: Path) -> str:
    if path.is_symlink():
        target = Path(os.readlink(path))
        if not target.is_absolute():
            target = (path.parent / target).resolve()
        if target.exists():
            return hash_path(target)
        return hash_path(path)
    return hash_path(path)


def hash_profile_runtime(profile_dir: Path) -> str:
    """Hash result-affecting profile state without reading credentials.

    Authentication is deliberately excluded. Settings, shared instructions,
    trust state, local extension directories, and local extension paths named
    by settings are included.
    """
    profile_dir = Path(profile_dir)
    files = {}
    for name in ("settings.json", "AGENTS.md", "trust.json"):
        path = profile_dir / name
        if path.exists() or path.is_symlink():
            files[name] = _hash_profile_file(path)

    directories = {}
    for name in ("extensions", "npm"):
        path = profile_dir / name
        if path.is_dir():
            directories[name] = _hash_profile_file(path)

    extension_refs = []
    settings_path = profile_dir / "settings.json"
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            settings = {}
        for value in settings.get("extensions", []):
            if not isinstance(value, str):
                extension_refs.append({"value": value, "sha256": None})
                continue
            path = Path(value).expanduser()
            extension_refs.append(
                {
                    "value": value,
                    "sha256": hash_path(path) if path.exists() else None,
                }
            )
    return sha256_json(
        {
            "files": files,
            "directories": directories,
            "extension_refs": extension_refs,
        }
    )


def hash_named_paths(paths: Mapping[str, Path]) -> str:
    return sha256_json(
        {name: hash_path(Path(path)) for name, path in sorted(paths.items())}
    )


def hash_fixtures(
    source_dir: Path,
    files: Iterable,
) -> list[dict[str, str]]:
    fixtures = [normalize_fixture_spec(value) for value in files]
    return [
        {
            "source": fixture["source"],
            "dest": fixture["dest"],
            "sha256": hash_path(source_dir / fixture["source"]),
        }
        for fixture in sorted(fixtures, key=lambda item: item["dest"])
    ]


def _build_record(
    *,
    skill: str,
    case_id: str,
    content: dict,
    runner_files: Mapping[str, Path],
    config: Mapping,
    loaded_skills: Optional[list[str]] = None,
) -> dict:
    content_fingerprint = sha256_json(content)
    runner_fingerprint = hash_named_paths(runner_files)
    config_fingerprint = sha256_json(config)
    combined = sha256_json(
        {
            "protocol_version": EVAL_PROTOCOL_VERSION,
            "content": content_fingerprint,
            "runner": runner_fingerprint,
            "config": config_fingerprint,
        }
    )
    return {
        "skill": skill,
        "case_id": case_id,
        "loaded_skills": sorted(loaded_skills or []),
        "config": dict(config),
        "fingerprints": {
            "content": content_fingerprint,
            "runner": runner_fingerprint,
            "config": config_fingerprint,
            "combined": combined,
        },
    }


def build_compliance_record(
    skill: str,
    skill_dir: Path,
    eval_spec: Mapping,
    loaded_skill_dirs: Mapping[str, Path],
    runner_files: Mapping[str, Path],
    config: Mapping,
) -> dict:
    content = {
        "skill_definition": hash_skill_definition(skill_dir),
        "loaded_skill_definitions": {
            name: hash_skill_definition(path)
            for name, path in sorted(loaded_skill_dirs.items())
        },
        "eval": {
            "spec": dict(eval_spec),
            "fixtures": hash_fixtures(skill_dir, eval_spec.get("files") or []),
        },
    }
    return _build_record(
        skill=skill,
        case_id=eval_spec["id"],
        content=content,
        runner_files=runner_files,
        config=config,
        loaded_skills=loaded_skill_dirs.keys(),
    )


def build_trigger_record(
    skill: str,
    skills_root: Path,
    probe_spec: Mapping,
    runner_files: Mapping[str, Path],
    config: Mapping,
) -> dict:
    catalog = {
        source.name: hash_skill_definition(source)
        for source in sorted(skills_root.iterdir())
        if source.is_dir() and (source / "SKILL.md").is_file()
    }
    content = {
        "catalog": catalog,
        "probe": {
            "spec": dict(probe_spec),
            "fixtures": hash_fixtures(
                skills_root / skill, probe_spec.get("files") or []
            ),
        },
    }
    return _build_record(
        skill=skill,
        case_id=probe_spec["id"],
        content=content,
        runner_files=runner_files,
        config=config,
    )


def default_runner_files(repo_root: Path, runner: str) -> dict[str, Path]:
    shared = {
        "eval_scoring.py": repo_root / "scripts" / "eval_scoring.py",
        "pi_eval_client.py": repo_root / "scripts" / "pi_eval_client.py",
        "skill_eval_utils.py": repo_root / "scripts" / "skill_eval_utils.py",
    }
    if runner == "compliance":
        primary = repo_root / "scripts" / "run-skill-evals.py"
    elif runner == "trigger":
        primary = repo_root / "scripts" / "run-trigger-probes.py"
    else:
        raise ValueError(f"unknown eval runner: {runner}")
    return {
        **shared,
        Path(primary).name: primary,
    }


def write_fingerprint_manifest(
    path: Path,
    runner: str,
    records: Mapping[str, Mapping],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": EVAL_PROTOCOL_VERSION,
                "runner": runner,
                "records": dict(sorted(records.items())),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def measure_profile_runtime(
    base_dir: Path,
    base_env: Mapping[str, str],
    profile_name: str = "eval",
) -> str:
    """Create a disposable profile and hash its effective runtime surface."""
    base_dir = Path(base_dir)
    arm = prepare_isolated_arms(
        base_dir,
        base_dir.parent,
        files=[],
        names=("profile",),
        profile_name=profile_name,
    )["profile"]
    create_isolated_profile(arm, base_env)
    return hash_profile_runtime(arm.profile_dir)


def command_version(command: str) -> str:
    try:
        completed = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not read {command} version: {exc}") from exc
    if completed.returncode != 0:
        raise RuntimeError(
            f"{command} --version exited {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()[-200:]}"
        )
    return (completed.stdout or completed.stderr).strip()

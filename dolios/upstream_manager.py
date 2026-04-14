"""Upstream source management for Dolios.

Tracks and syncs upstream repositories used by Dolios integration layers.
Also supports syncing AI-DLC rule details from awslabs/aidlc-workflows.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dolios.io import save_yaml, utc_now_iso

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpstreamSpec:
    """Source repository metadata."""

    name: str
    url: str
    path: Path


CORE_UPSTREAMS: tuple[UpstreamSpec, ...] = (
    UpstreamSpec(
        name="hermes-agent",
        url="https://github.com/NousResearch/hermes-agent.git",
        path=Path("vendor/hermes-agent"),
    ),
    UpstreamSpec(
        name="nemoclaw",
        url="https://github.com/NVIDIA/NemoClaw.git",
        path=Path("vendor/nemoclaw"),
    ),
    UpstreamSpec(
        name="hermes-agent-self-evolution",
        url="https://github.com/NousResearch/hermes-agent-self-evolution.git",
        path=Path("vendor/hermes-agent-self-evolution"),
    ),
)

AIDLC_UPSTREAM = UpstreamSpec(
    name="aidlc-workflows",
    url="https://github.com/awslabs/aidlc-workflows.git",
    path=Path("vendor/aidlc-workflows"),
)


def parse_ls_remote_head(output: str) -> str:
    """Parse `git ls-remote <repo> HEAD` output and return the SHA."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise ValueError("No ls-remote output")

    first = lines[0]
    parts = first.split()
    if len(parts) != 2 or parts[1] != "HEAD":
        raise ValueError(f"Unexpected ls-remote output: {first}")

    return parts[0]


class UpstreamManager:
    """Manage upstream dependency repos and synchronization state."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.vendor_dir = project_dir / "vendor"

    def get_specs(self, include_aidlc: bool = False) -> list[UpstreamSpec]:
        """Return upstream specs to operate on."""
        specs = list(CORE_UPSTREAMS)
        if include_aidlc:
            specs.append(AIDLC_UPSTREAM)
        return specs

    def status(
        self,
        include_aidlc: bool = False,
        refresh_remote: bool = False,
    ) -> list[dict[str, Any]]:
        """Return upstream status summary for local and optional remote refs."""
        items: list[dict[str, Any]] = []

        for spec in self.get_specs(include_aidlc=include_aidlc):
            repo_path = self._repo_path(spec)
            local_sha = self._local_head(repo_path)

            remote_sha: str | None = None
            if refresh_remote:
                try:
                    remote_sha = self._remote_head(spec)
                except (subprocess.CalledProcessError, ValueError):
                    remote_sha = None

            items.append(
                {
                    "name": spec.name,
                    "path": str(spec.path),
                    "exists": (repo_path / ".git").exists(),
                    "local_sha": local_sha,
                    "remote_sha": remote_sha,
                }
            )

        return items

    def sync(
        self,
        include_aidlc: bool = False,
        sync_aidlc_rules: bool = True,
    ) -> tuple[Path, dict[str, Any]]:
        """Sync selected upstream repos to latest remote HEAD and write manifest."""
        records = [self.sync_repo(spec) for spec in self.get_specs(include_aidlc=include_aidlc)]

        manifest: dict[str, Any] = {
            "generated_at": utc_now_iso(),
            "repos": records,
        }

        if include_aidlc and sync_aidlc_rules:
            manifest["aidlc_rules"] = self.sync_aidlc_rule_details()

        self.vendor_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.vendor_dir / "upstream-manifest.yaml"
        save_yaml(manifest_path, manifest)
        logger.info(f"Upstream manifest updated: {manifest_path}")
        return manifest_path, manifest

    def sync_repo(self, spec: UpstreamSpec) -> dict[str, Any]:
        """Clone/fetch one repo and detach to latest remote HEAD SHA."""
        repo_path = self._repo_path(spec)
        before = self._local_head(repo_path)

        if (repo_path / ".git").exists():
            self._run(["git", "fetch", "origin", "--prune"], cwd=repo_path)
        else:
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            self._run(["git", "clone", spec.url, str(repo_path)])

        remote_sha = self._remote_head(spec)
        self._run(["git", "fetch", "origin", remote_sha], cwd=repo_path)
        self._run(["git", "checkout", "--detach", remote_sha], cwd=repo_path)

        after = self._local_head(repo_path)
        if not after:
            raise RuntimeError(f"Failed to resolve local HEAD for {spec.name}")

        return {
            "name": spec.name,
            "url": spec.url,
            "path": str(spec.path),
            "previous_sha": before,
            "remote_head": remote_sha,
            "synced_sha": after,
            "changed": before != after,
        }

    def sync_aidlc_rule_details(self) -> dict[str, Any]:
        """Sync latest aws-aidlc-rule-details into .aidlc-rule-details."""
        source_repo = self._repo_path(AIDLC_UPSTREAM)
        source_root = source_repo / "aidlc-rules" / "aws-aidlc-rule-details"
        if not source_root.exists():
            raise FileNotFoundError(
                "aidlc-workflows not found. Run upstream sync with --include-aidlc first."
            )

        target_root = self.project_dir / ".aidlc-rule-details"
        target_root.mkdir(parents=True, exist_ok=True)

        files_synced = 0
        for source_file in sorted(source_root.rglob("*.md")):
            rel = source_file.relative_to(source_root)
            target_file = target_root / rel
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(source_file.read_text())
            files_synced += 1

        version_path = source_repo / "aidlc-rules" / "VERSION"
        version = version_path.read_text().strip() if version_path.exists() else ""
        source_sha = self._local_head(source_repo)

        metadata = {
            "synced_at": utc_now_iso(),
            "source_repo": AIDLC_UPSTREAM.url,
            "source_sha": source_sha,
            "version": version,
            "files_synced": files_synced,
            "source_root": str(source_root),
        }
        save_yaml(target_root / "upstream-sync.yaml", metadata)

        logger.info(f"Synced {files_synced} AI-DLC rule files into {target_root}")
        return metadata

    def _repo_path(self, spec: UpstreamSpec) -> Path:
        return self.project_dir / spec.path

    def _remote_head(self, spec: UpstreamSpec) -> str:
        out = self._run(["git", "ls-remote", spec.url, "HEAD"])
        return parse_ls_remote_head(out)

    def _local_head(self, repo_path: Path) -> str | None:
        if not (repo_path / ".git").exists():
            return None
        try:
            return self._run(["git", "rev-parse", "HEAD"], cwd=repo_path).strip()
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def _run(args: list[str], cwd: Path | None = None) -> str:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()

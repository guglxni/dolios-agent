"""Dolios configuration management.

Handles loading, validating, and merging config from:
1. Default values
2. ~/.dolios/config.yaml
3. ./dolios.yaml (project-level)
4. Environment variables (DOLIOS_ prefix)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _dolios_home() -> Path:
    return Path(os.environ.get("DOLIOS_HOME", Path.home() / ".dolios"))


def _parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


@dataclass
class SandboxConfig:
    """NemoClaw sandbox configuration."""

    enabled: bool = True
    sandbox_name: str = "dolios-default"
    blueprint_version: str = "0.1.0"
    policy_file: str = "policies/dolios-default.yaml"
    openshell_path: str | None = None
    policy_tier: str = "balanced"  # restricted | balanced | open


@dataclass
class InferenceConfig:
    """Multi-provider inference routing configuration."""

    default_provider: str = "openrouter"
    default_model: str = "nous/hermes-3-llama-3.1-405b"
    max_cost_per_1k_tokens: float = 0.01
    providers: dict[str, dict] = field(
        default_factory=lambda: {
            "nvidia": {
                "base_url": "https://integrate.api.nvidia.com/v1",
                "model": "nvidia/nemotron-3-super-120b-a12b",
                "api_key_env": "NVIDIA_API_KEY",
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "model": "nous/hermes-3-llama-3.1-405b",
                "api_key_env": "OPENROUTER_API_KEY",
            },
            "nous": {
                "base_url": "https://portal.nousresearch.com/v1",
                "model": "hermes-3-405b",
                "api_key_env": "NOUS_API_KEY",
            },
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o",
                "api_key_env": "OPENAI_API_KEY",
            },
            "local": {
                "base_url": "http://localhost:11434/v1",
                "model": "hermes3:latest",
                "api_key_env": "",
            },
        }
    )


@dataclass
class EvolutionConfig:
    """Self-evolution pipeline configuration."""

    enabled: bool = True
    traces_dir: str = "~/.dolios/traces"
    optimizer: str = "gepa"  # gepa | miprov2
    auto_pr: bool = False  # require human review by default
    max_skill_size_kb: int = 15
    max_tool_desc_chars: int = 500


@dataclass
class AuditConfig:
    """Append-only audit trail configuration."""

    enabled: bool = True
    log_path: str = "~/.dolios/audit.jsonl"
    max_size_mb: int = 100


@dataclass
class WorkflowConfig:
    """DAG workflow policy configuration."""

    enabled: bool = True
    policy_file: str = "policies/workflow.yaml"


@dataclass
class DLPConfig:
    """Outbound DLP scanner configuration."""

    enabled: bool = True


@dataclass
class DoliosConfig:
    """Top-level Dolios configuration."""

    home: Path = field(default_factory=_dolios_home)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    dlp: DLPConfig = field(default_factory=DLPConfig)
    brand_voice: str = "brand/SOUL.md"
    aidlc_enabled: bool = True
    aidlc_require_phase_approval: bool = False
    log_level: str = "INFO"

    @classmethod
    def load(cls, project_dir: Path | None = None) -> DoliosConfig:
        """Load config from defaults → home dir → project dir → env vars."""
        config = cls()

        # Load from ~/.dolios/config.yaml
        home_config = config.home / "config.yaml"
        if home_config.exists():
            _merge_yaml(config, home_config)

        # Load from project-level dolios.yaml
        if project_dir:
            project_config = project_dir / "dolios.yaml"
            if project_config.exists():
                _merge_yaml(config, project_config)

        # Env var overrides
        if env_provider := os.environ.get("DOLIOS_INFERENCE_PROVIDER"):
            config.inference.default_provider = env_provider
        if env_model := os.environ.get("DOLIOS_INFERENCE_MODEL"):
            config.inference.default_model = env_model
        if os.environ.get("DOLIOS_SANDBOX_DISABLED", "").lower() in ("1", "true", "yes"):
            config.sandbox.enabled = False
        if env_tier := os.environ.get("DOLIOS_SANDBOX_TIER"):
            config.sandbox.policy_tier = env_tier
        if env_aidlc_enabled := os.environ.get("DOLIOS_AIDLC_ENABLED"):
            parsed = _parse_bool(env_aidlc_enabled)
            if parsed is not None:
                config.aidlc_enabled = parsed
        if env_aidlc_approval := os.environ.get("DOLIOS_AIDLC_REQUIRE_APPROVAL"):
            parsed = _parse_bool(env_aidlc_approval)
            if parsed is not None:
                config.aidlc_require_phase_approval = parsed
        if env_log := os.environ.get("DOLIOS_LOG_LEVEL"):
            config.log_level = env_log
        if env_audit_enabled := os.environ.get("DOLIOS_AUDIT_ENABLED"):
            parsed = _parse_bool(env_audit_enabled)
            if parsed is not None:
                config.audit.enabled = parsed

        return config


def _merge_yaml(config: DoliosConfig, path: Path) -> None:
    """Merge a YAML file into config, overriding matching fields."""
    from dolios.io import load_yaml

    data = load_yaml(path, default={})

    sections = {
        "sandbox": config.sandbox,
        "inference": config.inference,
        "evolution": config.evolution,
        "audit": config.audit,
        "workflow": config.workflow,
        "dlp": config.dlp,
    }
    for name, obj in sections.items():
        if section_data := data.get(name):
            for k, v in section_data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)

    for key in ("brand_voice", "aidlc_enabled", "aidlc_require_phase_approval", "log_level"):
        if key in data:
            setattr(config, key, data[key])

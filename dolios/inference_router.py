"""Inference Router — multi-provider model routing through sandbox gateway.

Selects the optimal inference provider based on:
1. Task type → capability matching
2. Cost constraint → budget filtering
3. Policy → allowed providers in sandbox
4. User preference → explicit override

When running inside a NemoClaw sandbox, all inference calls are intercepted
by the OpenShell gateway and routed to the configured provider. This router
determines WHICH provider to configure.

Integration with Hermes Agent:
- Sets OPENAI_API_BASE and OPENAI_API_KEY env vars (Hermes uses OpenAI-compatible clients)
- Can import agent.model_metadata from vendor for model capability data
- Generates NemoClaw inference profile entries for blueprint
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dolios.config import DoliosConfig
    from dolios.security.vault import CredentialVault

logger = logging.getLogger(__name__)


class TaskType(StrEnum):
    """Types of tasks for inference routing."""

    GENERAL = "general"
    CODE = "code"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SIMPLE = "simple"


# Task type → preferred model characteristics
TASK_PROFILES: dict[str, dict[str, Any]] = {
    TaskType.GENERAL: {"min_context": 8192, "prefer": ["speed", "reasoning"]},
    TaskType.CODE: {"min_context": 32768, "prefer": ["code_quality", "context"]},
    TaskType.CREATIVE: {"min_context": 8192, "prefer": ["creativity"]},
    TaskType.ANALYSIS: {"min_context": 65536, "prefer": ["reasoning", "context"]},
    TaskType.SIMPLE: {"min_context": 4096, "prefer": ["speed", "cost"]},
}

# Provider capability scores (0-1, higher is better)
# These will be refined by the self-evolution pipeline over time
PROVIDER_CAPABILITIES: dict[str, dict[str, float]] = {
    "nvidia": {
        "speed": 0.8,
        "code_quality": 0.85,
        "creativity": 0.7,
        "reasoning": 0.9,
        "context": 0.8,
        "cost": 0.6,
    },
    "openrouter": {
        "speed": 0.7,
        "code_quality": 0.9,
        "creativity": 0.85,
        "reasoning": 0.9,
        "context": 0.9,
        "cost": 0.5,
    },
    "nous": {
        "speed": 0.7,
        "code_quality": 0.85,
        "creativity": 0.8,
        "reasoning": 0.85,
        "context": 0.85,
        "cost": 0.7,
    },
    "openai": {
        "speed": 0.9,
        "code_quality": 0.9,
        "creativity": 0.85,
        "reasoning": 0.9,
        "context": 0.85,
        "cost": 0.3,
    },
    "local": {
        "speed": 0.5,
        "code_quality": 0.6,
        "creativity": 0.5,
        "reasoning": 0.6,
        "context": 0.7,
        "cost": 1.0,
    },
}


@dataclass
class InferenceRoute:
    """Resolved inference routing decision."""

    provider: str
    model: str
    base_url: str
    api_key: str
    score: float
    reason: str

    def __repr__(self) -> str:
        """Redact api_key from repr to prevent accidental logging."""
        key_display = (
            f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        )
        return (
            f"InferenceRoute(provider={self.provider!r}, model={self.model!r}, "
            f"base_url={self.base_url!r}, api_key='{key_display}', "
            f"score={self.score}, reason={self.reason!r})"
        )


class InferenceRouter:
    """Routes inference requests to the optimal provider."""

    def __init__(self, config: DoliosConfig, vault: CredentialVault | None = None):
        self.config = config
        self._vault = vault
        self._configured = False
        self._available_providers: list[str] = []

    def configure(self) -> None:
        """Validate provider configs and API keys."""
        available = []
        for name, provider in self.config.inference.providers.items():
            api_key_env = provider.get("api_key_env", "")
            if not api_key_env or os.environ.get(api_key_env):
                available.append(name)
            else:
                logger.debug(f"Provider {name} unavailable: {api_key_env} not set")

        if not available:
            logger.warning("No inference providers available — check API keys")

        self._available_providers = available
        self._configured = True
        logger.info(f"Available providers: {', '.join(available)}")

    def route(
        self,
        task_type: str | TaskType = TaskType.GENERAL,
        preferred_provider: str | None = None,
    ) -> InferenceRoute:
        """Select the optimal provider for a task."""
        if not self._configured:
            self.configure()

        # User override
        if preferred_provider and preferred_provider in self._available_providers:
            return self._build_route(preferred_provider, "user preference")

        # Score each available provider
        profile = TASK_PROFILES.get(task_type, TASK_PROFILES["general"])
        preferred_traits = profile["prefer"]

        best_provider = None
        best_score = -1.0

        for provider_name in self._available_providers:
            caps = PROVIDER_CAPABILITIES.get(provider_name, {})
            # CQ-L4: Guard against empty preferred_traits to prevent ZeroDivisionError
            if not preferred_traits:
                score = 0.5
            else:
                score = sum(caps.get(trait, 0.5) for trait in preferred_traits) / len(
                    preferred_traits
                )

            if score > best_score:
                best_score = score
                best_provider = provider_name

        if not best_provider:
            best_provider = self.config.inference.default_provider
            best_score = 0.0

        return self._build_route(
            best_provider,
            f"best match for {task_type} (score: {best_score:.2f})",
        )

    def _build_route(self, provider_name: str, reason: str) -> InferenceRoute:
        provider = self.config.inference.providers.get(provider_name, {})
        api_key_env = provider.get("api_key_env", "")
        # Prefer vault if available, fall back to os.environ for backward compat
        if api_key_env and self._vault and self._vault.has(api_key_env):
            api_key = self._vault.inject(api_key_env)
        elif api_key_env:
            api_key = os.environ.get(api_key_env, "")
        else:
            api_key = ""
        return InferenceRoute(
            provider=provider_name,
            model=provider.get("model", self.config.inference.default_model),
            base_url=provider.get("base_url", ""),
            api_key=api_key,
            score=0.0,
            reason=reason,
        )

    def apply_to_env(self, route: InferenceRoute | None = None) -> None:
        """Set environment variables for Hermes Agent to use this route.

        Hermes Agent uses OpenAI-compatible env vars:
        - OPENAI_API_BASE / OPENAI_BASE_URL
        - OPENAI_API_KEY
        """
        route = route or self.route()

        os.environ["OPENAI_API_BASE"] = route.base_url
        os.environ["OPENAI_BASE_URL"] = route.base_url
        if route.api_key:
            os.environ["OPENAI_API_KEY"] = route.api_key
        os.environ["DEFAULT_MODEL"] = route.model

        logger.info(f"Env configured: {route.provider} → {route.model}")

    def to_blueprint_profile(self, route: InferenceRoute | None = None) -> dict[str, Any]:
        """Convert a route to NemoClaw blueprint inference profile format."""
        route = route or self.route()
        provider = self.config.inference.providers.get(route.provider, {})

        return {
            "provider_type": "nvidia" if route.provider == "nvidia" else "openai",
            "provider_name": f"dolios-{route.provider}",
            "endpoint": route.base_url,
            "model": route.model,
            "credential_env": provider.get("api_key_env", ""),
        }

    def list_providers(self) -> list[dict[str, Any]]:
        """List all configured providers with availability status."""
        if not self._configured:
            self.configure()

        result = []
        for name, provider in self.config.inference.providers.items():
            result.append(
                {
                    "name": name,
                    "model": provider.get("model"),
                    "available": name in self._available_providers,
                    "base_url": provider.get("base_url"),
                }
            )
        return result

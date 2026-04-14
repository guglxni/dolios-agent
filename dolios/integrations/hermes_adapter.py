"""Hermes runtime adapter.

Provides a Dolios-owned seam for the Hermes Agent core loop.
"""

from __future__ import annotations

import importlib.util
import json
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from dolios.vendor_path import ensure_vendor_on_path

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


OPTIONAL_TOOL_IMPORT_MODULES = {
    "tools.web_tools": "firecrawl",
    "tools.image_generation_tool": "fal_client",
}


logger = logging.getLogger(__name__)


class HermesRuntimeAdapter:
    """Adapter around vendor/hermes-agent run_agent.AIAgent."""

    @staticmethod
    def _is_optional_tool_import_warning(message: str) -> bool:
        if not message.startswith("Could not import tool module "):
            return False

        return any(module in message for module in OPTIONAL_TOOL_IMPORT_MODULES)

    @staticmethod
    def optional_dependency_status() -> dict[str, bool]:
        """Return optional Hermes tool dependency availability."""
        return {
            dependency: importlib.util.find_spec(dependency) is not None
            for dependency in OPTIONAL_TOOL_IMPORT_MODULES.values()
        }

    @contextmanager
    def _suppress_optional_tool_import_warnings(self) -> Iterator[None]:
        """Suppress known non-critical Hermes optional tool import warnings.

        Hermes discovers all tool modules at import time. Some tools are optional
        and may be intentionally unavailable in production, so suppress only the
        known optional import warnings while preserving all other warnings.
        """

        class OptionalImportFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                return not HermesRuntimeAdapter._is_optional_tool_import_warning(
                    record.getMessage()
                )

        model_tools_logger = logging.getLogger("model_tools")
        warning_filter = OptionalImportFilter()
        model_tools_logger.addFilter(warning_filter)

        try:
            yield
        finally:
            model_tools_logger.removeFilter(warning_filter)

    def create_agent(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        policy_guard: Callable[[str, dict[str, Any]], tuple[bool, str]] | None = None,
        max_iterations: int = 90,
        platform: str = "cli",
        skip_context_files: bool = False,
        skip_memory: bool = False,
    ) -> Any:
        """Create a Hermes AIAgent instance from the latest synced vendor repo."""
        ensure_vendor_on_path()
        if policy_guard is not None:
            self._install_tool_guard(policy_guard)

        with self._suppress_optional_tool_import_warnings():
            from run_agent import AIAgent

        return AIAgent(
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_iterations=max_iterations,
            platform=platform,
            skip_context_files=skip_context_files,
            skip_memory=skip_memory,
        )

    def _install_tool_guard(
        self,
        guard: Callable[[str, dict[str, Any]], tuple[bool, str]],
    ) -> None:
        """Wrap Hermes handle_function_call with a Dolios guard callback."""
        ensure_vendor_on_path()
        with self._suppress_optional_tool_import_warnings():
            import model_tools
            import run_agent

        if getattr(run_agent, "_dolios_tool_guard_installed", False):
            return

        original = run_agent.handle_function_call

        def wrapped_handle_function_call(
            function_name: str,
            function_args: Any,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            parsed_args = self._coerce_args(function_args)
            allowed, reason = guard(function_name, parsed_args)
            if not allowed:
                return f"Blocked by Dolios policy guard: {reason}"

            return original(function_name, function_args, *args, **kwargs)

        run_agent.handle_function_call = wrapped_handle_function_call
        model_tools.handle_function_call = wrapped_handle_function_call
        run_agent._dolios_tool_guard_installed = True

    @staticmethod
    def _coerce_args(raw_args: Any) -> dict[str, Any]:
        if isinstance(raw_args, dict):
            return raw_args

        if isinstance(raw_args, str):
            try:
                parsed = json.loads(raw_args)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}

        return {}

    def compatibility_snapshot(self) -> dict[str, bool]:
        """Report whether expected Hermes symbols are available."""
        ensure_vendor_on_path()

        status = {
            "AIAgent": False,
            "handle_function_call": False,
            "build_context_files_prompt": False,
        }

        try:
            with self._suppress_optional_tool_import_warnings():
                from run_agent import AIAgent  # noqa: F401

            status["AIAgent"] = True
        except ImportError:
            return status

        try:
            with self._suppress_optional_tool_import_warnings():
                from model_tools import handle_function_call  # noqa: F401

            status["handle_function_call"] = True
        except ImportError:
            pass

        try:
            from agent.prompt_builder import build_context_files_prompt  # noqa: F401

            status["build_context_files_prompt"] = True
        except ImportError:
            pass

        return status

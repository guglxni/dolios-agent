"""DAG-based workflow policy enforcement for tool call ordering.

Tools can declare prerequisites in policies/workflow.yaml.  Before a tool
is dispatched, the WorkflowPolicy checks that all required predecessor
tools have completed with the required status.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from dolios.io import load_yaml

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class ToolStatus(StrEnum):
    """Execution status of a tool within a session."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkflowPolicy:
    """Enforces tool ordering via a DAG declared in workflow.yaml."""

    def __init__(self, config: DoliosConfig) -> None:
        self._enabled = config.workflow.enabled
        policy_path = Path(config.workflow.policy_file)
        self._rules: dict[str, list[dict[str, str]]] = {}
        self._sessions: dict[str, dict[str, ToolStatus]] = {}
        self._load(policy_path)

    def _load(self, path: Path) -> None:
        data = load_yaml(path)
        if data is None:
            logger.debug("No workflow policy at %s — no ordering constraints", path)
            return

        for entry in data.get("policies", []):
            tool = entry.get("tool", "")
            requires = entry.get("requires", [])
            if tool:
                self._rules[tool] = requires

        self._check_cycles()

    def _check_cycles(self) -> None:
        """Raise ValueError if the dependency graph contains cycles."""
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node: str) -> None:
            if node in in_stack:
                raise ValueError(
                    f"Circular dependency detected in workflow policy involving tool '{node}'"
                )
            if node in visited:
                return
            in_stack.add(node)
            for req in self._rules.get(node, []):
                dep = req.get("tool", "")
                if dep:
                    dfs(dep)
            in_stack.remove(node)
            visited.add(node)

        for tool_name in self._rules:
            dfs(tool_name)

    def check(self, session_id: str, tool_name: str) -> tuple[bool, str]:
        """Check whether *tool_name* is allowed to run in *session_id*."""
        if not self._enabled:
            return True, ""

        requirements = self._rules.get(tool_name)
        if not requirements:
            return True, ""

        session_state = self._sessions.get(session_id, {})

        for req in requirements:
            dep_tool = req.get("tool", "")
            required_status = req.get("status", "success")
            dep_state = session_state.get(dep_tool)

            if dep_state is None:
                return (
                    False,
                    f"Tool '{tool_name}' requires '{dep_tool}' to run first "
                    f"(status={required_status})",
                )

            if required_status == "success" and dep_state != ToolStatus.SUCCESS:
                return (
                    False,
                    f"Tool '{tool_name}' requires '{dep_tool}' to have succeeded "
                    f"(current: {dep_state})",
                )

        return True, ""

    def record_outcome(self, session_id: str, tool_name: str, *, success: bool) -> None:
        """Record tool execution outcome for workflow state tracking."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {}
        self._sessions[session_id][tool_name] = (
            ToolStatus.SUCCESS if success else ToolStatus.FAILED
        )

    def reset_session(self, session_id: str) -> None:
        """Clear workflow state for a session."""
        self._sessions.pop(session_id, None)

"""Trace Collector — logs execution traces for the self-evolution pipeline.

Captures agent execution traces (tool calls, results, timing, errors) and
persists them to ~/.dolios/traces/ for analysis by the evolution pipeline.

Traces feed into:
1. DSPy/GEPA for skill optimization (understanding WHY things fail)
2. Atropos RL environments for trajectory-based training
3. Evolution fitness evaluation
"""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Types of events that can occur in an execution trace."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    INFERENCE = "inference"
    ERROR = "error"
    PHASE_CHANGE = "phase_change"


class Outcome(StrEnum):
    """Possible outcomes of an execution trace."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TraceEvent:
    """A single event in an execution trace."""

    timestamp: str
    event_type: str  # tool_call, tool_result, inference, error, phase_change
    data: dict = field(default_factory=dict)
    duration_ms: float = 0.0


MAX_TRACE_EVENTS = 10_000  # Prevent unbounded memory growth in long sessions


@dataclass
class ExecutionTrace:
    """Complete execution trace for a task."""

    trace_id: str
    session_id: str
    task_description: str
    started_at: str
    events: list[TraceEvent] = field(default_factory=list)
    outcome: str = "in_progress"  # success, failure, partial, in_progress
    skills_used: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    total_duration_ms: float = 0.0
    inference_calls: int = 0
    error_count: int = 0


MAX_TRACE_FILES = 1000  # Prevent unbounded disk growth


class TraceCollector:
    """Collects and persists execution traces for the evolution pipeline."""

    def __init__(self, config: DoliosConfig):
        self.config = config
        self.traces_dir = Path(config.evolution.traces_dir).expanduser()
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self._active_traces: dict[str, ExecutionTrace] = {}
        self._rotate_traces()

    def start_trace(self, trace_id: str, session_id: str, task: str) -> ExecutionTrace:
        """Begin a new execution trace."""
        trace = ExecutionTrace(
            trace_id=trace_id,
            session_id=session_id,
            task_description=task,
            started_at=datetime.now(UTC).isoformat(),
        )
        self._active_traces[trace_id] = trace
        logger.debug(f"Trace started: {trace_id}")
        return trace

    def add_event(
        self,
        trace_id: str,
        event_type: str,
        data: dict | None = None,
        duration_ms: float = 0.0,
    ) -> None:
        """Add an event to an active trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            logger.warning(f"No active trace: {trace_id}")
            return

        event = TraceEvent(
            timestamp=datetime.now(UTC).isoformat(),
            event_type=event_type,
            data=data or {},
            duration_ms=duration_ms,
        )
        if len(trace.events) >= MAX_TRACE_EVENTS:
            # CQ-L1: FIFO eviction — drop oldest 10% for predictable behavior
            drop_count = MAX_TRACE_EVENTS // 10
            logger.warning(
                "Trace %s hit %d events — dropping oldest %d",
                trace_id,
                MAX_TRACE_EVENTS,
                drop_count,
            )
            trace.events = trace.events[drop_count:]
        trace.events.append(event)

        # Update counters
        if event_type == "tool_call":
            tool_name = (data or {}).get("tool", "")
            if tool_name and tool_name not in trace.tools_used:
                trace.tools_used.append(tool_name)
        elif event_type == "inference":
            trace.inference_calls += 1
        elif event_type == "error":
            trace.error_count += 1

    def end_trace(self, trace_id: str, outcome: str = "success") -> Path | None:
        """End a trace and persist it to disk."""
        trace = self._active_traces.pop(trace_id, None)
        if not trace:
            logger.warning(f"No active trace to end: {trace_id}")
            return None

        trace.outcome = outcome

        # Calculate total duration
        start_time = datetime.fromisoformat(trace.started_at)
        trace.total_duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        # Persist to disk using atomic write
        from dolios.io import save_json

        date_prefix = datetime.now(UTC).strftime("%Y-%m-%d")
        trace_path = self.traces_dir / f"{date_prefix}_{trace_id}.json"
        save_json(trace_path, asdict(trace))

        logger.debug(f"Trace saved: {trace_path}")
        return trace_path

    def list_traces(self, limit: int = 50) -> list[dict]:
        """List recent traces with summary info."""
        trace_files = sorted(self.traces_dir.glob("*.json"), reverse=True)[:limit]
        summaries = []

        for path in trace_files:
            with open(path) as f:
                trace = json.load(f)
            summaries.append(
                {
                    "trace_id": trace["trace_id"],
                    "task": trace["task_description"][:80],
                    "outcome": trace["outcome"],
                    "duration_ms": trace["total_duration_ms"],
                    "tools_used": len(trace["tools_used"]),
                    "errors": trace["error_count"],
                }
            )

        return summaries

    def _rotate_traces(self) -> None:
        """Delete oldest trace files when exceeding MAX_TRACE_FILES.

        Prevents unbounded disk growth (OWASP LLM10: Unbounded Consumption).
        """
        trace_files = sorted(self.traces_dir.glob("*.json"))
        excess = len(trace_files) - MAX_TRACE_FILES
        if excess > 0:
            for old_file in trace_files[:excess]:
                with suppress(OSError):
                    old_file.unlink()
            logger.info(f"Rotated {excess} old trace files (keeping {MAX_TRACE_FILES})")

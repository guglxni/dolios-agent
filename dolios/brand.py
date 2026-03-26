"""Brand Layer — applies Dolios identity on top of Hermes Agent's personality system.

Loads SOUL.md, context files, and voice guidelines to configure the agent's
personality, communication style, and behavioral principles.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dolios.config import DoliosConfig

logger = logging.getLogger(__name__)


class BrandLayer:
    """Manages Dolios brand identity and personality injection."""

    def __init__(self, config: DoliosConfig, project_dir: Path):
        self.config = config
        self.project_dir = project_dir
        self.brand_dir = project_dir / "brand"

    def get_soul_content(self) -> str:
        """Load SOUL.md content for personality injection.

        Validates that the path stays within the project directory
        to prevent path traversal attacks via brand_voice config.
        """
        soul_path = (self.project_dir / self.config.brand_voice).resolve()

        # Prevent path traversal (e.g., brand_voice: "../../etc/passwd")
        if not str(soul_path).startswith(str(self.project_dir.resolve())):
            logger.warning(
                f"SECURITY: brand_voice path '{self.config.brand_voice}' "
                f"escapes project directory — using default"
            )
            return self._default_soul()

        if soul_path.exists():
            return soul_path.read_text()

        logger.warning(f"SOUL.md not found at {soul_path}, using default")
        return self._default_soul()

    def get_context_files(self) -> list[Path]:
        """Return all brand context files to load into the agent."""
        files = []
        if self.brand_dir.exists():
            for f in self.brand_dir.iterdir():
                if f.suffix == ".md" and f.is_file():
                    files.append(f)
        return sorted(files)

    def get_voice_guidelines(self) -> dict[str, list[str]]:
        """Parse voice guidelines into structured do/don't lists."""
        guidelines_path = self.brand_dir / "voice_guidelines.md"
        if not guidelines_path.exists():
            return {"do": [], "dont": []}

        content = guidelines_path.read_text()
        do_items: list[str] = []
        dont_items: list[str] = []
        current_section: list[str] | None = None

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.lower() == "## do":
                current_section = do_items
            elif stripped.lower() == "## don't":
                current_section = dont_items
            elif stripped.startswith("- ") and current_section is not None:
                current_section.append(stripped[2:])

        return {"do": do_items, "dont": dont_items}

    @staticmethod
    def _default_soul() -> str:
        return (
            "You are Dolios, an autonomous AI agent. "
            "You are precise, technical, and direct. "
            "You scheme, execute, and deliver."
        )

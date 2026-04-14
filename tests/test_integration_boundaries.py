"""Boundary tests to keep vendor-touch logic behind Dolios integration seams."""

from pathlib import Path


def test_cli_uses_evolution_adapter_seam() -> None:
    content = Path("dolios/cli.py").read_text()
    assert "from evolution.dolios_targets import" not in content
    assert "EvolutionRuntimeAdapter" in content


def test_orchestrator_has_no_vendor_path_bootstrap() -> None:
    content = Path("dolios/orchestrator.py").read_text()
    assert "ensure_vendor_on_path(" not in content


def test_legacy_evolution_module_is_shim() -> None:
    content = Path("evolution/dolios_targets.py").read_text()
    assert "Compatibility shim" in content
    assert "from dolios.integrations.evolution_vendor import" in content

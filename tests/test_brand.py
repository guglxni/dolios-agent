"""Tests for dolios.brand."""

from pathlib import Path

from dolios.brand import BrandLayer
from dolios.config import DoliosConfig


def test_get_soul_content():
    config = DoliosConfig()
    project_dir = Path(__file__).parent.parent
    brand = BrandLayer(config, project_dir)

    soul = brand.get_soul_content()
    assert "Dolios" in soul
    assert "Crafty Agent" in soul


def test_get_soul_fallback(tmp_path):
    config = DoliosConfig()
    config.brand_voice = "nonexistent.md"
    brand = BrandLayer(config, tmp_path)

    soul = brand.get_soul_content()
    assert "Dolios" in soul  # Should return default


def test_get_context_files():
    config = DoliosConfig()
    project_dir = Path(__file__).parent.parent
    brand = BrandLayer(config, project_dir)

    files = brand.get_context_files()
    names = [f.name for f in files]
    assert "SOUL.md" in names
    assert "context.md" in names
    assert "voice_guidelines.md" in names


def test_get_voice_guidelines():
    config = DoliosConfig()
    project_dir = Path(__file__).parent.parent
    brand = BrandLayer(config, project_dir)

    guidelines = brand.get_voice_guidelines()
    assert len(guidelines["do"]) > 0
    assert len(guidelines["dont"]) > 0

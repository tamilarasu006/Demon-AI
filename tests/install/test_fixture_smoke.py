"""Smoke test that the tmp_DEMON_home fixture works."""

from __future__ import annotations

from pathlib import Path

from DEMON.core import config as config_mod


def test_fixture_redirects_default_config_dir(tmp_DEMON_home: Path) -> None:
    assert config_mod.DEFAULT_CONFIG_DIR == tmp_DEMON_home
    assert tmp_DEMON_home.exists()
    assert (tmp_DEMON_home / ".state").exists()
    assert (tmp_DEMON_home / ".state" / "models").exists()


def test_fixture_redirects_config_path(tmp_DEMON_home: Path) -> None:
    assert config_mod.DEFAULT_CONFIG_PATH == tmp_DEMON_home / "config.toml"

# test/config/test_config.py
"""
Canonical configuration object.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


from galleria.config import Config, MissingConfigError
from galleria.config import OUTPUT_DIR


def make_config(tmp_path: Path, **overrides) -> Config:
    """Build a valid Config, overriding only what a test cares about.

    Supplies both manifest paths so a test exercising output
    resolution does not restate the manifest rule.
    """
    paths = (tmp_path / "original.json", tmp_path / "display.json")
    defaults = {"original_manifest": paths[0], "display_manifest": paths[1]}
    return Config.from_overrides(**{**defaults, **overrides})


class TestConfigFromOverrides:
    """Overrides layer over program defaults."""

    def test_override_wins_over_default(self, tmp_path):
        """An explicit output directory replaces the default."""
        cfg = make_config(tmp_path, output_dir=(path := tmp_path / "foobar"))
        assert cfg.output_dir == path

    def test_unspecified_value_falls_through_to_default(self, tmp_path):
        """An output directory absent from the overrides comes from
        the default layer."""
        assert make_config(tmp_path).output_dir == OUTPUT_DIR

    def test_required_paths_are_carried_verbatim(self, tmp_path):
        """Both manifest paths come only from the overrides, since the
        default layer holds none."""
        orig, disp = tmp_path / "orig.json", tmp_path / "disp.json"
        result = Config.from_overrides(original_manifest=orig, display_manifest=disp)
        assert result.original_manifest == orig
        assert result.display_manifest == disp


class TestConfigImmutability:
    """The object is frozen once constructed."""

    def test_rejects_mutation(self, tmp_path):
        """Reassigning a field raises, so no stage can alter
        configuration mid-build."""
        orig, disp = tmp_path / "orig.json", tmp_path / "disp.json"
        cfg = Config.from_overrides(original_manifest=orig, display_manifest=disp)
        with pytest.raises(FrozenInstanceError):
            cfg.original_manifest = tmp_path / "foobar"  # type: ignore


class TestConfigMissingValues:
    """A build needs at least one manifest to read."""

    def test_no_manifests_raises(self):
        """Neither variant supplied leaves nothing to build from."""
        with pytest.raises(MissingConfigError):
            Config.from_overrides()

    def test_one_manifest_is_sufficient(self, tmp_path):
        """A single variant is a valid build; the absent one stays
        None."""
        path = tmp_path / "display.json"
        cfg = Config.from_overrides(display_manifest=path)
        assert cfg.display_manifest == path
        assert cfg.original_manifest is None

    def test_error_carries_a_message(self):
        """A bare raise leaves the caller nothing to report."""
        with pytest.raises(MissingConfigError) as exc:
            Config.from_overrides()
        assert str(exc.value)

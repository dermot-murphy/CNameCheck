"""
Tests for per-directory config override discovery (issue #193).

Tests cover:
  - resolve_per_dir_config: no override, single override, chain, root: true
  - _walk_per_dir_configs: ordering and root: true stop
  - Cache reuse
  - CLI --per-dir-config integration
"""
import os
import sys
import copy
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness import (  # noqa: E402
    resolve_per_dir_config,
    _walk_per_dir_configs,
    _PER_DIR_CONFIG_NAME,
    cfg_only,
    run,
    rules,
)

import yaml  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(directory: Path, data: dict) -> None:
    """Write a .cstylecheck.yml into *directory*."""
    (directory / _PER_DIR_CONFIG_NAME).write_text(
        yaml.dump(data), encoding="utf-8"
    )


# Minimal root config used across tests
_ROOT_CFG = cfg_only(
    misc={
        "line_length": {"enabled": True, "severity": "error", "max": 80},
    }
)


# ---------------------------------------------------------------------------
# _walk_per_dir_configs
# ---------------------------------------------------------------------------

class TestWalkPerDirConfigs:
    def test_no_configs_returns_empty(self, tmp_path):
        result = _walk_per_dir_configs(tmp_path)
        assert result == []

    def test_single_config_in_dir(self, tmp_path):
        _write_yaml(tmp_path, {"misc": {"line_length": {"max": 100}}})
        result = _walk_per_dir_configs(tmp_path)
        assert len(result) == 1
        assert result[0]["misc"]["line_length"]["max"] == 100

    def test_two_levels_outermost_first(self, tmp_path):
        outer = tmp_path
        inner = tmp_path / "sub"
        inner.mkdir()
        _write_yaml(outer, {"misc": {"line_length": {"max": 100}}})
        _write_yaml(inner, {"misc": {"line_length": {"max": 120}}})
        result = _walk_per_dir_configs(inner)
        assert len(result) == 2
        # outermost first
        assert result[0]["misc"]["line_length"]["max"] == 100
        assert result[1]["misc"]["line_length"]["max"] == 120

    def test_root_true_stops_walk(self, tmp_path):
        outer = tmp_path
        middle = tmp_path / "mid"
        inner = middle / "inner"
        inner.mkdir(parents=True)
        # outer config — should NOT be included because middle has root: true
        _write_yaml(outer, {"misc": {"line_length": {"max": 80}}})
        # middle config with root: true — stops here
        _write_yaml(middle, {"root": True, "misc": {"line_length": {"max": 100}}})
        # inner config — closest to file
        _write_yaml(inner, {"misc": {"line_length": {"max": 120}}})
        result = _walk_per_dir_configs(inner)
        # Should include middle (with root: true) and inner, but NOT outer
        assert len(result) == 2
        maxs = [r["misc"]["line_length"]["max"] for r in result]
        assert 80 not in maxs
        assert 100 in maxs
        assert 120 in maxs

    def test_unreadable_config_is_skipped(self, tmp_path):
        outer = tmp_path
        inner = tmp_path / "sub"
        inner.mkdir()
        _write_yaml(outer, {"misc": {"line_length": {"max": 100}}})
        # Write invalid YAML
        (inner / _PER_DIR_CONFIG_NAME).write_text(
            ": invalid: yaml: [unclosed", encoding="utf-8"
        )
        result = _walk_per_dir_configs(inner)
        # Only outer config is valid
        assert len(result) == 1
        assert result[0]["misc"]["line_length"]["max"] == 100


# ---------------------------------------------------------------------------
# resolve_per_dir_config
# ---------------------------------------------------------------------------

class TestResolvePerDirConfig:
    def test_no_override_returns_root_cfg(self, tmp_path):
        fake_file = tmp_path / "src" / "foo.c"
        fake_file.parent.mkdir(parents=True)
        fake_file.touch()
        cache: dict = {}
        result = resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        assert result is _ROOT_CFG

    def test_single_override_is_merged(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        _write_yaml(src_dir, {"misc": {"line_length": {"max": 120}}})
        fake_file = src_dir / "foo.c"
        fake_file.touch()
        cache: dict = {}
        result = resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        # Override should raise the max
        assert result["misc"]["line_length"]["max"] == 120
        # Other keys from root should still be present
        assert result["misc"]["line_length"]["enabled"] is True

    def test_override_does_not_mutate_root_cfg(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        _write_yaml(src_dir, {"misc": {"line_length": {"max": 200}}})
        fake_file = src_dir / "foo.c"
        fake_file.touch()
        root_copy = copy.deepcopy(_ROOT_CFG)
        cache: dict = {}
        resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        assert _ROOT_CFG == root_copy

    def test_root_key_not_in_merged_result(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        _write_yaml(src_dir, {"root": True, "misc": {"line_length": {"max": 100}}})
        fake_file = src_dir / "foo.c"
        fake_file.touch()
        cache: dict = {}
        result = resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        assert "root" not in result

    def test_cache_hit_returns_same_object(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        _write_yaml(src_dir, {"misc": {"line_length": {"max": 100}}})
        file1 = src_dir / "foo.c"
        file2 = src_dir / "bar.c"
        file1.touch()
        file2.touch()
        cache: dict = {}
        result1 = resolve_per_dir_config(str(file1), _ROOT_CFG, cache)
        result2 = resolve_per_dir_config(str(file2), _ROOT_CFG, cache)
        assert result1 is result2  # exact same object from cache

    def test_chain_innermost_wins(self, tmp_path):
        outer = tmp_path
        inner = tmp_path / "sub"
        inner.mkdir()
        _write_yaml(outer, {"misc": {"line_length": {"max": 100}}})
        _write_yaml(inner, {"misc": {"line_length": {"max": 150}}})
        fake_file = inner / "foo.c"
        fake_file.touch()
        cache: dict = {}
        result = resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        # Inner (150) should win over outer (100)
        assert result["misc"]["line_length"]["max"] == 150

    def test_chain_outer_applies_when_no_inner_key(self, tmp_path):
        outer = tmp_path
        inner = tmp_path / "sub"
        inner.mkdir()
        # Outer adds a completely new section (functions override)
        _write_yaml(outer, {"functions": {"enabled": False}})
        # Inner only overrides line_length
        _write_yaml(inner, {"misc": {"line_length": {"max": 120}}})
        fake_file = inner / "foo.c"
        fake_file.touch()
        root = cfg_only(
            misc={"line_length": {"enabled": True, "severity": "error", "max": 80}},
            functions={"enabled": True, "severity": "error", "case": "lower_snake"},
        )
        cache: dict = {}
        result = resolve_per_dir_config(str(fake_file), root, cache)
        # Outer disabled functions, inner didn't touch it
        assert result["functions"]["enabled"] is False
        # Inner raised line_length
        assert result["misc"]["line_length"]["max"] == 120

    def test_empty_cache_populated_after_call(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        fake_file = src_dir / "foo.c"
        fake_file.touch()
        cache: dict = {}
        resolve_per_dir_config(str(fake_file), _ROOT_CFG, cache)
        assert len(cache) == 1

    def test_separate_dirs_each_cached(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        _write_yaml(dir_a, {"misc": {"line_length": {"max": 100}}})
        _write_yaml(dir_b, {"misc": {"line_length": {"max": 120}}})
        fa = dir_a / "foo.c"
        fb = dir_b / "bar.c"
        fa.touch()
        fb.touch()
        cache: dict = {}
        res_a = resolve_per_dir_config(str(fa), _ROOT_CFG, cache)
        res_b = resolve_per_dir_config(str(fb), _ROOT_CFG, cache)
        assert res_a["misc"]["line_length"]["max"] == 100
        assert res_b["misc"]["line_length"]["max"] == 120
        assert len(cache) == 2


# ---------------------------------------------------------------------------
# CLI integration — --per-dir-config flag
# ---------------------------------------------------------------------------

class TestPerDirConfigCLI:
    """Integration test via CLI main()."""

    def test_flag_applies_override(self, tmp_path, monkeypatch):
        import cstylecheck as _mod

        # Write a minimal rules.yml (root config) — all rules off
        root_cfg_data = cfg_only(
            misc={"line_length": {"enabled": True, "severity": "error", "max": 40}},
        )
        import yaml as _yaml
        rules_yml = tmp_path / "rules.yml"
        rules_yml.write_text(_yaml.dump(root_cfg_data), encoding="utf-8")

        # Write per-dir override relaxing line_length to 200
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        _write_yaml(src_dir, {"misc": {"line_length": {"max": 200}}})

        # Write a short source file (50 chars per line — OK for 200, bad for 40)
        src_file = src_dir / "test_module.c"
        src_file.write_text("x" * 50 + "\n", encoding="utf-8")

        orig_argv = sys.argv[:]
        try:
            # Without --per-dir-config: should flag line_length violation
            sys.argv = [
                "cstylecheck",
                str(src_file),
                "--config", str(rules_yml),
            ]
            monkeypatch.chdir(tmp_path)
            rc = _mod.main()
            assert rc == 1  # 50-char line violates max=40

            # With --per-dir-config: max relaxed to 200, no violation
            sys.argv = [
                "cstylecheck",
                str(src_file),
                "--config", str(rules_yml),
                "--per-dir-config",
            ]
            rc = _mod.main()
            assert rc == 0  # 50-char line is fine at max=200
        finally:
            sys.argv = orig_argv

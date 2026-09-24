from __future__ import annotations

from crosshair_overlay.config import (
    Settings,
    default_config_path,
    load_settings,
    save_settings,
)


def test_round_trip(tmp_path):
    path = tmp_path / "config.json"
    settings = Settings(color="#FF00FF", length=20, t_shape=True, monitor=1)
    save_settings(settings, path)
    assert load_settings(path) == settings


def test_missing_file_returns_defaults(tmp_path):
    assert load_settings(tmp_path / "does-not-exist.json") == Settings()


def test_invalid_json_returns_defaults(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{ not valid json", encoding="utf-8")
    assert load_settings(path) == Settings()


def test_unknown_keys_are_ignored():
    settings = Settings.from_dict({"color": "#123456", "totally_unknown": 42})
    assert settings.color == "#123456"
    assert settings == Settings(color="#123456")


def test_default_path_points_at_config_json():
    path = default_config_path()
    assert path.name == "config.json"
    assert path.parent.name == "crosshair-overlay"

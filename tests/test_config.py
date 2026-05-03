"""Settings + env loading."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_defaults_load_without_env(monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "ADMIN_API_TOKEN", "CHUNK_SIZE", "CHUNK_OVERLAP"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.chunk_size == 900
    assert s.chunk_overlap == 150
    assert s.cors_origin_list == ["*"]


def test_overlap_must_be_smaller_than_size(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "200")
    monkeypatch.setenv("CHUNK_OVERLAP", "300")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_cors_origin_list_parses_csv(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com, https://b.com ,https://c.com")
    s = Settings(_env_file=None)
    assert s.cors_origin_list == ["https://a.com", "https://b.com", "https://c.com"]

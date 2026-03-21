"""Tests for application configuration."""

import os
from unittest.mock import patch

import pytest

from backend.config import Settings, get_settings


def test_settings_defaults():
    """Settings have expected defaults when env and dotenv are unused."""
    with patch.dict(os.environ, {}, clear=True):
        get_settings.cache_clear()
        try:
            settings = Settings(_env_file=None)
            assert settings.boldsign_api_host == "https://api.boldsign.com"
            assert settings.rate_limit == "100/minute"
            assert settings.api_title == "SlateUp Funding API"
            assert settings.api_version == "1.0.0"
            assert settings.debug is False
        finally:
            get_settings.cache_clear()


def test_settings_from_env():
    """Settings load from environment variables."""
    with patch.dict(
        os.environ,
        {
            "BOLDSIGN_API_KEY": "env-key",
            "BOLDSIGN_API_HOST": "https://custom.api.test",
            "DEBUG": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        try:
            settings = Settings(_env_file=None)
            assert settings.boldsign_api_key == "env-key"
            assert settings.boldsign_api_host == "https://custom.api.test"
            assert settings.debug is True
        finally:
            get_settings.cache_clear()


def test_get_settings_cached():
    """get_settings returns cached instance."""
    get_settings.cache_clear()
    try:
        a = get_settings()
        b = get_settings()
        assert a is b
    finally:
        get_settings.cache_clear()

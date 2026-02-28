"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Reset environment variables for each test."""
    # Clear any environment variables that might affect tests
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

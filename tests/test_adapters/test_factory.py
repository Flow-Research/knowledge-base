"""Tests for model adapter factory."""

import pytest

from scripts.adapters import (
    AnthropicAdapter,
    DeepSeekAdapter,
    ModelFactory,
    OllamaAdapter,
    OpenAIAdapter,
)


class TestModelFactory:
    """Test ModelFactory."""

    def test_create_anthropic_adapter(self):
        """Test creating Anthropic adapter."""
        adapter = ModelFactory.create("anthropic", api_key="test-key")
        assert isinstance(adapter, AnthropicAdapter)
        assert adapter.get_name() == "anthropic:claude-sonnet-4-20250514"

    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter."""
        adapter = ModelFactory.create("openai", api_key="test-key")
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.get_name() == "openai:gpt-5.2"

    def test_create_deepseek_adapter(self):
        """Test creating DeepSeek adapter."""
        adapter = ModelFactory.create("deepseek", api_key="test-key")
        assert isinstance(adapter, DeepSeekAdapter)
        assert adapter.get_name() == "deepseek:deepseek-chat"

    def test_create_ollama_adapter(self):
        """Test creating Ollama adapter."""
        adapter = ModelFactory.create("ollama")
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.get_name() == "ollama:llama3"

    def test_create_unknown_provider(self):
        """Test error on unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ModelFactory.create("unknown-provider")

    def test_list_providers(self):
        """Test listing available providers."""
        providers = ModelFactory.list_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "deepseek" in providers
        assert "ollama" in providers

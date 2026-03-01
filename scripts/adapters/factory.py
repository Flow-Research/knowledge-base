"""Model factory for creating LLM adapters."""


from .anthropic import AnthropicAdapter
from .base import BaseModelAdapter
from .openai import (
    DeepSeekAdapter,
    GLMAdapter,
    GroqAdapter,
    KimiAdapter,
    MinimaxAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)


class ModelFactory:
    """Factory for creating model adapters."""

    _adapters: dict[str, type[BaseModelAdapter]] = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "deepseek": DeepSeekAdapter,
        "ollama": OllamaAdapter,
        "glm": GLMAdapter,
        "kimi": KimiAdapter,
        "minimax": MinimaxAdapter,
        "openrouter": OpenRouterAdapter,  # 25+ free models
        "groq": GroqAdapter,              # ultra-fast free tier
    }

    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseModelAdapter:
        """Create a model adapter for the specified provider.

        Args:
            provider: Provider name (e.g., "anthropic", "openai", "deepseek")
            **kwargs: Provider-specific configuration

        Returns:
            BaseModelAdapter instance

        Raises:
            ValueError: If provider is unknown

        Example:
            >>> factory = ModelFactory()
            >>> adapter = factory.create("anthropic", api_key="sk-...", model="claude-sonnet-4")
        """
        adapter_class = cls._adapters.get(provider.lower())
        if not adapter_class:
            available = list(cls._adapters.keys())
            raise ValueError(
                f"Unknown provider: {provider}. Available providers: {available}"
            )
        return adapter_class(**kwargs)

    @classmethod
    def register(cls, name: str, adapter_class: type[BaseModelAdapter]) -> None:
        """Register a new adapter.

        This allows extending the factory with custom adapters.

        Args:
            name: Provider name
            adapter_class: Adapter class (must inherit from BaseModelAdapter)

        Example:
            >>> class CustomAdapter(BaseModelAdapter):
            ...     pass
            >>> ModelFactory.register("custom", CustomAdapter)
        """
        cls._adapters[name.lower()] = adapter_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of registered providers.

        Returns:
            List of provider names
        """
        return list(cls._adapters.keys())

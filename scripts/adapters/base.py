"""Base model adapter interface for LLM integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationRequest:
    """Request for content generation from an LLM."""

    prompt: str
    max_tokens: int
    temperature: float
    system_prompt: Optional[str] = None


@dataclass
class GenerationResponse:
    """Response from LLM content generation."""

    content: str
    model: str
    usage: dict  # input_tokens, output_tokens


class BaseModelAdapter(ABC):
    """Abstract base class for all model adapters."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using the LLM.

        Args:
            request: GenerationRequest with prompt and settings

        Returns:
            GenerationResponse with generated content and metadata

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the identifier for this model adapter.

        Returns:
            String identifier like "anthropic:claude-sonnet-4-20250514"
        """
        pass

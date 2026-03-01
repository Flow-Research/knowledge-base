"""Anthropic (Claude) model adapter."""


from anthropic import Anthropic

from .base import BaseModelAdapter, GenerationRequest, GenerationResponse


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        prompt_caching: bool = True,
    ):
        """Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key
            model: Model identifier (default: claude-sonnet-4-20250514)
            prompt_caching: Enable prompt caching for cost savings
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.prompt_caching = prompt_caching

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using Claude.

        Args:
            request: GenerationRequest with prompt and settings

        Returns:
            GenerationResponse with generated content

        Raises:
            anthropic.APIError: If API call fails
        """
        # Prepare messages
        messages = [{"role": "user", "content": request.prompt}]

        # Build API call parameters
        params = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }

        # Add system prompt if provided
        if request.system_prompt:
            params["system"] = request.system_prompt

        # Make API call
        response = self.client.messages.create(**params)

        # Extract content
        content = response.content[0].text if response.content else ""

        # Extract usage information
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        """Get adapter identifier."""
        return f"anthropic:{self.model}"

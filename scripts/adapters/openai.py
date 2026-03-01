"""OpenAI model adapter."""

from openai import OpenAI

from .base import BaseModelAdapter, GenerationRequest, GenerationResponse


class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI GPT models."""

    def __init__(self, api_key: str, model: str = "gpt-5.2"):
        """Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            model: Model identifier (default: gpt-5.2)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using OpenAI.

        Args:
            request: GenerationRequest with prompt and settings

        Returns:
            GenerationResponse with generated content

        Raises:
            openai.APIError: If API call fails
        """
        # Prepare messages
        messages = []

        # Add system prompt if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.append({"role": "user", "content": request.prompt})

        # Make API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Extract content
        content = response.choices[0].message.content if response.choices else ""

        # Extract usage information
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        """Get adapter identifier."""
        return f"openai:{self.model}"


class DeepSeekAdapter(BaseModelAdapter):
    """Adapter for DeepSeek models (via OpenAI-compatible API)."""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """Initialize DeepSeek adapter.

        Args:
            api_key: DeepSeek API key
            model: Model identifier (default: deepseek-chat)
        """
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using DeepSeek.

        Args:
            request: GenerationRequest with prompt and settings

        Returns:
            GenerationResponse with generated content

        Raises:
            openai.APIError: If API call fails
        """
        # Prepare messages
        messages = []

        # Add system prompt if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.append({"role": "user", "content": request.prompt})

        # Make API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Extract content
        content = response.choices[0].message.content if response.choices else ""

        # Extract usage information
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        """Get adapter identifier."""
        return f"deepseek:{self.model}"


class OllamaAdapter(BaseModelAdapter):
    """Adapter for local Ollama models."""

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3"
    ):
        """Initialize Ollama adapter.

        Args:
            base_url: Ollama server URL
            model: Model identifier (default: llama3)
        """
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using Ollama.

        Args:
            request: GenerationRequest with prompt and settings

        Returns:
            GenerationResponse with generated content
        """
        # Prepare messages
        messages = []

        # Add system prompt if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.append({"role": "user", "content": request.prompt})

        # Make API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Extract content
        content = response.choices[0].message.content if response.choices else ""

        # Extract usage information (Ollama may not provide this)
        usage = {
            "input_tokens": response.usage.prompt_tokens
            if response.usage and hasattr(response.usage, "prompt_tokens")
            else 0,
            "output_tokens": response.usage.completion_tokens
            if response.usage and hasattr(response.usage, "completion_tokens")
            else 0,
        }

        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        """Get adapter identifier."""
        return f"ollama:{self.model}"


class GLMAdapter(BaseModelAdapter):
    """Adapter for GLM models (Zhipu AI) via OpenAI-compatible API."""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        return f"glm:{self.model}"


class KimiAdapter(BaseModelAdapter):
    """Adapter for Kimi models (Moonshot AI) via OpenAI-compatible API."""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self, api_key: str, model: str = "moonshot-v1-8k"):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        return f"kimi:{self.model}"


class MinimaxAdapter(BaseModelAdapter):
    """Adapter for Minimax models via OpenAI-compatible API."""

    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(self, api_key: str, model: str = "abab6.5s-chat"):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        return f"minimax:{self.model}"


class OpenRouterAdapter(BaseModelAdapter):
    """Adapter for OpenRouter - access 25+ free models."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.3-70b-instruct:free"):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        return f"openrouter:{self.model}"


class GroqAdapter(BaseModelAdapter):
    """Adapter for Groq - ultra-fast free tier."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return GenerationResponse(content=content, model=self.model, usage=usage)

    def get_name(self) -> str:
        return f"groq:{self.model}"


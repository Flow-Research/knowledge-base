"""Configuration management for knowledge base agent."""

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager for agent."""

    def __init__(self, config_path: str = "scripts/config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation path.

        Args:
            key_path: Dot-separated path (e.g., "ai.model")
            default: Default value if not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("ai.model")
            "claude-sonnet-4-20250514"
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_sources(self, enabled_only: bool = True) -> list[dict]:
        """Get discovery sources.

        Args:
            enabled_only: Only return enabled sources

        Returns:
            List of source configurations
        """
        sources = self.get("sources", [])

        if enabled_only:
            sources = [s for s in sources if s.get("enabled", True)]

        return sources

    def get_ai_config(self) -> dict:
        """Get AI configuration.

        Returns:
            AI configuration dict
        """
        ai_config = self.get("ai", {})

        # Load API key from environment
        api_key_env = ai_config.get("api_key_env")
        if api_key_env:
            ai_config["api_key"] = os.getenv(api_key_env)
            if not ai_config["api_key"]:
                raise ValueError(
                    f"API key not found in environment variable: {api_key_env}"
                )

        return ai_config

    def get_github_config(self) -> dict:
        """Get GitHub configuration.

        Returns:
            GitHub configuration dict
        """
        github_config = self.get("github", {})

        # Load GitHub token from environment
        github_config["token"] = os.getenv("GITHUB_TOKEN")
        if not github_config["token"]:
            raise ValueError("GITHUB_TOKEN not found in environment")

        return github_config

    def get_quality_config(self) -> dict:
        """Get content quality configuration.

        Returns:
            Quality configuration dict
        """
        return self.get("quality", {})

    def get_deduplication_config(self) -> dict:
        """Get deduplication configuration.

        Returns:
            Deduplication configuration dict
        """
        return self.get("deduplication", {})

    def get_retry_config(self) -> dict:
        """Get retry configuration.

        Returns:
            Retry configuration dict
        """
        return self.get("retry", {})

    def get_state_config(self) -> dict:
        """Get state storage configuration.

        Returns:
            State configuration dict
        """
        return self.get("state", {})

    def validate(self) -> list[str]:
        """Validate configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required sections
        required_sections = ["agent", "sources", "ai", "github"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")

        # Validate AI config
        ai_config = self.get("ai", {})
        if "provider" not in ai_config:
            errors.append("Missing ai.provider")
        if "model" not in ai_config:
            errors.append("Missing ai.model")
        if "api_key_env" not in ai_config:
            errors.append("Missing ai.api_key_env")

        # Validate GitHub config
        github_config = self.get("github", {})
        if "owner" not in github_config:
            errors.append("Missing github.owner")
        if "repo" not in github_config:
            errors.append("Missing github.repo")

        # Validate sources
        sources = self.get("sources", [])
        if not sources:
            errors.append("No sources configured")

        for idx, source in enumerate(sources):
            if "id" not in source:
                errors.append(f"Source {idx}: missing 'id'")
            if "type" not in source:
                errors.append(f"Source {idx}: missing 'type'")
            if "domain" not in source:
                errors.append(f"Source {idx}: missing 'domain'")
            if "level" not in source:
                errors.append(f"Source {idx}: missing 'level'")

        return errors

    def save(self, output_path: str | None = None) -> None:
        """Save configuration to file.

        Args:
            output_path: Optional path to save (defaults to original path)
        """
        path = Path(output_path) if output_path else self.config_path

        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"Config(path={self.config_path})"

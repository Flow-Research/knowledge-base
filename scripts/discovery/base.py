"""Base discoverer interface for content sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiscoveredItem:
    """Represents a discovered content item."""

    # Required fields
    title: str
    url: str
    source_type: str  # "github", "arxiv", "hn", etc.
    discovered_at: datetime

    # Metadata
    description: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    tags: list[str] = None
    body: str | None = None

    # Source-specific metadata
    metadata: dict = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class BaseDiscoverer(ABC):
    """Abstract base class for content discoverers."""

    def __init__(self, source_id: str, config: dict):
        """Initialize discoverer.

        Args:
            source_id: Unique identifier for this source
            config: Source configuration from config.yaml
        """
        self.source_id = source_id
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def discover(self, last_processed_id: str | None = None) -> list[DiscoveredItem]:
        """Discover new content from the source.

        Args:
            last_processed_id: ID of last processed item (for incremental discovery)

        Returns:
            List of discovered items

        Raises:
            Exception: If discovery fails
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """Get the source type identifier.

        Returns:
            Source type like "github", "arxiv", "hn"
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this discoverer is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled

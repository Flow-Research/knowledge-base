"""arXiv content discoverer."""

import time
from datetime import datetime
from typing import Optional

import feedparser

from .base import BaseDiscoverer, DiscoveredItem


class ArxivDiscoverer(BaseDiscoverer):
    """Discovers academic papers from arXiv."""

    API_URL = "http://export.arxiv.org/api/query"

    def __init__(self, source_id: str, config: dict):
        """Initialize arXiv discoverer.

        Args:
            source_id: Unique identifier for this source
            config: Source configuration
        """
        super().__init__(source_id, config)
        self.query_config = config.get("query", {})
        self.categories = self.query_config.get("categories", [])
        self.max_results = self.query_config.get("max_results", 10)
        self.sort_by = self.query_config.get("sort_by", "submittedDate")
        self.sort_order = self.query_config.get("sort_order", "descending")
        self.keywords = config.get("keywords", [])

    def discover(self, last_processed_id: Optional[str] = None) -> list[DiscoveredItem]:
        """Discover new papers from arXiv.

        Args:
            last_processed_id: Last processed arXiv ID

        Returns:
            List of discovered papers
        """
        discovered = []

        for category in self.categories:
            try:
                items = self._discover_category(category, last_processed_id)
                discovered.extend(items)
                
                # Respect arXiv rate limit (1 req/sec recommended)
                time.sleep(1)
                
            except Exception as e:
                # Log error and continue with next category
                print(f"Error discovering from arXiv category {category}: {e}")
                continue

        return discovered

    def _discover_category(
        self, category: str, last_processed_id: Optional[str]
    ) -> list[DiscoveredItem]:
        """Discover papers from a single category.

        Args:
            category: arXiv category (e.g., "cs.AI")
            last_processed_id: Last processed paper ID

        Returns:
            List of discovered papers
        """
        # Build search query
        search_query = f"cat:{category}"
        
        # Add keyword filters if specified
        if self.keywords:
            keyword_query = " OR ".join(f'all:"{kw}"' for kw in self.keywords)
            search_query = f"({search_query}) AND ({keyword_query})"

        # Build API URL
        params = {
            "search_query": search_query,
            "max_results": self.max_results,
            "sortBy": self.sort_by,
            "sortOrder": self.sort_order,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.API_URL}?{query_string}"

        # Fetch and parse feed
        feed = feedparser.parse(url)
        
        items = []
        for entry in feed.entries:
            # Extract arXiv ID
            arxiv_id = entry.id.split("/abs/")[-1]
            
            # Stop if we've reached the last processed paper
            if last_processed_id and arxiv_id == last_processed_id:
                break

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed"):
                published_at = datetime(*entry.published_parsed[:6])

            # Extract authors
            authors = []
            if hasattr(entry, "authors"):
                authors = [author.name for author in entry.authors]
            author = authors[0] if authors else None

            # Extract categories/tags
            tags = []
            if hasattr(entry, "tags"):
                tags = [tag.term for tag in entry.tags]

            item = DiscoveredItem(
                title=entry.title,
                url=entry.link,
                source_type="arxiv",
                discovered_at=datetime.now(),
                description=self._truncate(entry.summary, 500),
                author=author,
                published_at=published_at,
                tags=tags,
                body=entry.summary,
                metadata={
                    "arxiv_id": arxiv_id,
                    "category": category,
                    "authors": authors,
                    "primary_category": entry.arxiv_primary_category.term
                    if hasattr(entry, "arxiv_primary_category")
                    else category,
                },
            )
            items.append(item)

        return items

    def _truncate(self, text: Optional[str], max_length: int) -> Optional[str]:
        """Truncate text to max length.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text or None
        """
        if not text:
            return None
        return text[:max_length] + "..." if len(text) > max_length else text

    def get_source_type(self) -> str:
        """Get source type identifier."""
        return "arxiv"

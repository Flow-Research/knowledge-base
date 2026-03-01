"""Content generator for creating markdown files with YAML frontmatter."""

import re
from datetime import UTC, datetime

import bleach
import yaml

from scripts.adapters import BaseModelAdapter, GenerationRequest
from scripts.discovery import DiscoveredItem

from .prompts import (
    CONTENT_GENERATION_TEMPLATE,
    DESCRIPTION_GENERATION_TEMPLATE,
    SYSTEM_PROMPT,
    TAGS_GENERATION_TEMPLATE,
)


class ContentGenerator:
    """Generates structured markdown content from discovered items."""

    # Allowed HTML tags for sanitization
    ALLOWED_TAGS = [
        "p",
        "br",
        "strong",
        "em",
        "code",
        "pre",
        "a",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
    ]
    ALLOWED_ATTRIBUTES = {"a": ["href", "title"], "code": ["class"]}

    def __init__(
        self,
        model_adapter: BaseModelAdapter,
        max_tokens: int = 4000,
        temperature: float = 0.3,
    ):
        """Initialize content generator.

        Args:
            model_adapter: LLM adapter for content generation
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
        """
        self.model = model_adapter
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(
        self, item: DiscoveredItem, domain: str, level: str, category: str
    ) -> dict:
        """Generate content from discovered item.

        Args:
            item: Discovered content item
            domain: Content domain (ai, blockchain, protocol)
            level: Difficulty level (beginner, intermediate, master)
            category: Content category (article, tool, resource, etc.)

        Returns:
            Dict with 'frontmatter' and 'content' keys

        Raises:
            Exception: If generation fails
        """
        # Generate main content
        content = self._generate_content(item, domain, level, category)

        # Sanitize content
        content = self._sanitize_content(content)

        # Generate metadata
        description = self._generate_description(item.title, content)
        tags = self._generate_tags(item.title, description, content)

        # Calculate credibility score
        credibility_score = self._calculate_credibility_score(item)

        # Build frontmatter
        frontmatter = self._build_frontmatter(
            item, domain, level, category, description, tags, credibility_score
        )

        return {"frontmatter": frontmatter, "content": content}

    def _generate_content(
        self, item: DiscoveredItem, domain: str, level: str, category: str
    ) -> str:
        """Generate markdown content using LLM.

        Args:
            item: Discovered item
            domain: Content domain
            level: Difficulty level
            category: Content category

        Returns:
            Generated markdown content
        """
        prompt = CONTENT_GENERATION_TEMPLATE.format(
            title=item.title,
            url=item.url,
            source_type=item.source_type,
            description=item.description or "N/A",
            published_at=item.published_at.strftime("%Y-%m-%d")
            if item.published_at
            else "Unknown",
            body=item.body or item.description or "",
            domain=domain,
            level=level,
            category=category,
        )

        request = GenerationRequest(
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system_prompt=SYSTEM_PROMPT,
        )

        response = self.model.generate(request)
        return response.content

    def _generate_description(self, title: str, content: str) -> str:
        """Generate description from content.

        Args:
            title: Content title
            content: Full content

        Returns:
            Generated description
        """
        # Use first 1000 chars as preview
        content_preview = content[:1000]

        prompt = DESCRIPTION_GENERATION_TEMPLATE.format(
            title=title, content_preview=content_preview
        )

        request = GenerationRequest(
            prompt=prompt, max_tokens=150, temperature=0.3, system_prompt=None
        )

        response = self.model.generate(request)
        description = response.content.strip()

        # Ensure max 500 chars
        return description[:500] if len(description) > 500 else description

    def _generate_tags(self, title: str, description: str, content: str) -> list[str]:
        """Generate tags from content.

        Args:
            title: Content title
            description: Content description
            content: Full content

        Returns:
            List of tags
        """
        content_preview = content[:1000]

        prompt = TAGS_GENERATION_TEMPLATE.format(
            title=title, description=description, content_preview=content_preview
        )

        request = GenerationRequest(
            prompt=prompt, max_tokens=100, temperature=0.3, system_prompt=None
        )

        response = self.model.generate(request)

        # Parse comma-separated tags
        tags_text = response.content.strip()
        tags = [tag.strip() for tag in tags_text.split(",")]

        # Clean and limit to 10 tags
        tags = [tag for tag in tags if tag and len(tag) < 50][:10]

        return tags

    def _sanitize_content(self, content: str) -> str:
        """Sanitize markdown content.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        # Remove script tags and event handlers
        clean = bleach.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            strip=True,
        )

        # Validate URLs are HTTPS
        clean = self._validate_urls(clean)

        return clean

    def _validate_urls(self, content: str) -> str:
        """Validate that all URLs in content are HTTPS.

        Args:
            content: Content with URLs

        Returns:
            Content with validated URLs
        """
        # Find all markdown links
        url_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        def replace_url(match):
            text = match.group(1)
            url = match.group(2)

            # Skip if already https or relative link
            if url.startswith("https://") or url.startswith("/") or url.startswith("#"):
                return match.group(0)

            # Upgrade http to https
            if url.startswith("http://"):
                url = url.replace("http://", "https://")

            return f"[{text}]({url})"

        return re.sub(url_pattern, replace_url, content)

    def _calculate_credibility_score(self, item: DiscoveredItem) -> int:
        """Calculate credibility score for content.

        Args:
            item: Discovered item

        Returns:
            Score from 1-10
        """
        score = 0.0

        # Source reputation (40%)
        if item.source_type == "arxiv":
            score += 4
        elif item.source_type == "github":
            stars = item.metadata.get("stars", 0)
            if stars > 10000:
                score += 4
            elif stars > 1000:
                score += 3
            else:
                score += 2
        else:
            score += 2

        # Recency (30%)
        if item.published_at:
            now = datetime.now(UTC)
            # If published_at is naive, assume UTC
            pub_date = item.published_at if item.published_at.tzinfo else item.published_at.replace(tzinfo=UTC)
            days_old = (now - pub_date).days
            if days_old < 30:
                score += 3
            elif days_old < 180:
                score += 2
            elif days_old < 365:
                score += 1
            else:
                score += 0.5
        else:
            score += 1  # Default if no date

        # Content completeness (20%)
        body_length = len(item.body or "")
        if body_length >= 1500:
            score += 2
        elif body_length >= 1000:
            score += 1.5
        elif body_length >= 500:
            score += 1
        else:
            score += 0.5

        # Has metadata (10%)
        if item.metadata:
            score += 1

        return min(round(score), 10)

    def _build_frontmatter(
        self,
        item: DiscoveredItem,
        domain: str,
        level: str,
        category: str,
        description: str,
        tags: list[str],
        credibility_score: int,
    ) -> dict:
        """Build YAML frontmatter dict.

        Args:
            item: Discovered item
            domain: Content domain
            level: Difficulty level
            category: Content category
            description: Generated description
            tags: Generated tags
            credibility_score: Calculated score

        Returns:
            Frontmatter dictionary
        """
        frontmatter = {
            # Required fields
            "title": item.title,
            "domain": domain,
            "level": level,
            "category": category,
            "tags": tags,
            # Metadata fields
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "sources": [
                {
                    "url": item.url,
                    "title": item.title,
                    "accessed_at": item.discovered_at.isoformat(),
                }
            ],
            "ai_reviewed": True,
            "human_reviewed": False,
            "status": "pending-review",
            # Optional fields
            "description": description,
            "author": "knowledge-base-agent",
            "credibility_score": credibility_score,
        }

        # Add source author if available
        if item.author:
            frontmatter["source_author"] = item.author

        # Add published date if available
        if item.published_at:
            frontmatter["source_published_at"] = item.published_at.isoformat()

        return frontmatter

    def format_output(self, generated: dict) -> str:
        """Format frontmatter and content as markdown file.

        Args:
            generated: Dict with 'frontmatter' and 'content' keys

        Returns:
            Complete markdown file content
        """
        # Convert frontmatter to YAML
        frontmatter_yaml = yaml.dump(
            generated["frontmatter"], default_flow_style=False, allow_unicode=True
        )

        # Combine with content
        output = f"---\n{frontmatter_yaml}---\n\n{generated['content']}"

        return output

"""GitHub content discoverer."""

import time
from datetime import datetime
from typing import Optional

from github import Github
from github.GithubException import GithubException, RateLimitExceededException

from .base import BaseDiscoverer, DiscoveredItem


class GitHubDiscoverer(BaseDiscoverer):
    """Discovers content from GitHub repositories."""

    def __init__(self, source_id: str, config: dict, github_token: str):
        """Initialize GitHub discoverer.

        Args:
            source_id: Unique identifier for this source
            config: Source configuration
            github_token: GitHub API token
        """
        super().__init__(source_id, config)
        self.client = Github(github_token)
        self.query_config = config.get("query", {})
        self.repos = self.query_config.get("repos", [])
        self.event_types = self.query_config.get("event_types", ["release"])
        self.keywords = config.get("keywords", [])

    def discover(self, last_processed_id: Optional[str] = None) -> list[DiscoveredItem]:
        """Discover new releases and tags from GitHub repositories.

        Args:
            last_processed_id: Last processed release/tag ID

        Returns:
            List of discovered GitHub items
        """
        discovered = []

        for repo_name in self.repos:
            try:
                items = self._discover_repo(repo_name, last_processed_id)
                discovered.extend(items)
                
                # Respect rate limits
                time.sleep(0.5)
                
            except RateLimitExceededException:
                # Wait for rate limit reset
                rate_limit = self.client.get_rate_limit()
                reset_time = rate_limit.core.reset
                wait_time = (reset_time - datetime.now()).total_seconds()
                if wait_time > 0:
                    time.sleep(min(wait_time, 60))  # Max 1 minute wait
                continue
                
            except GithubException as e:
                # Log error and continue with next repo
                print(f"Error discovering from {repo_name}: {e}")
                continue

        return discovered

    def _discover_repo(
        self, repo_name: str, last_processed_id: Optional[str]
    ) -> list[DiscoveredItem]:
        """Discover items from a single repository.

        Args:
            repo_name: Repository name (e.g., "openai/openai-python")
            last_processed_id: Last processed item ID

        Returns:
            List of discovered items
        """
        items = []
        repo = self.client.get_repo(repo_name)

        # Discover releases
        if "release" in self.event_types:
            for release in repo.get_releases():
                # Stop if we've reached the last processed release
                if last_processed_id and release.tag_name == last_processed_id:
                    break

                # Filter by keywords if specified
                if self.keywords and not self._matches_keywords(
                    release.title, release.body
                ):
                    continue

                item = DiscoveredItem(
                    title=release.title or release.tag_name,
                    url=release.html_url,
                    source_type="github",
                    discovered_at=datetime.now(),
                    description=self._truncate(release.body, 500),
                    author=release.author.login if release.author else None,
                    published_at=release.published_at,
                    tags=self._extract_tags(release.body),
                    body=release.body,
                    metadata={
                        "repo": repo_name,
                        "tag_name": release.tag_name,
                        "prerelease": release.prerelease,
                        "stars": repo.stargazers_count,
                        "event_type": "release",
                    },
                )
                items.append(item)

        # Discover tags (if not covered by releases)
        if "tag" in self.event_types:
            for tag in repo.get_tags():
                # Stop if we've reached the last processed tag
                if last_processed_id and tag.name == last_processed_id:
                    break

                # Get commit for tag
                commit = tag.commit
                
                item = DiscoveredItem(
                    title=f"{repo_name} - {tag.name}",
                    url=f"https://github.com/{repo_name}/releases/tag/{tag.name}",
                    source_type="github",
                    discovered_at=datetime.now(),
                    description=self._truncate(commit.commit.message, 500),
                    author=commit.commit.author.name if commit.commit.author else None,
                    published_at=commit.commit.author.date if commit.commit.author else None,
                    tags=[],
                    body=commit.commit.message,
                    metadata={
                        "repo": repo_name,
                        "tag_name": tag.name,
                        "stars": repo.stargazers_count,
                        "event_type": "tag",
                    },
                )
                items.append(item)

        return items

    def _matches_keywords(self, title: str, body: str) -> bool:
        """Check if title or body matches any keywords.

        Args:
            title: Release title
            body: Release body

        Returns:
            True if matches any keyword
        """
        if not self.keywords:
            return True

        content = f"{title} {body}".lower()
        return any(keyword.lower() in content for keyword in self.keywords)

    def _extract_tags(self, body: Optional[str]) -> list[str]:
        """Extract tags from release body.

        Args:
            body: Release body text

        Returns:
            List of tags
        """
        # Simple tag extraction - could be enhanced
        tags = []
        if body:
            # Look for common patterns like #tag or [tag]
            import re
            
            hashtags = re.findall(r"#(\w+)", body)
            tags.extend(hashtags[:5])  # Limit to 5 tags
            
        return tags

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
        return "github"

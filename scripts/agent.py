"""Main orchestrator for knowledge base agent."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.adapters import ModelFactory
from scripts.config import Config
from scripts.discovery import ArxivDiscoverer, DiscoveredItem, GitHubDiscoverer
from scripts.generation import ContentGenerator
from scripts.github_ops import ContentOps, PRManager
from scripts.utils import DeduplicationManager, RateLimiter, StructuredLogger


class KnowledgeBaseAgent:
    """Main orchestrator for content discovery and generation."""

    def __init__(self, config_path: str = "scripts/config.yaml"):
        """Initialize agent.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)

        # Validate configuration
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {errors}")

        # Initialize logger
        log_level = self.config.get("agent.log_level", "INFO")
        self.logger = StructuredLogger(name="knowledge-base-agent", level=log_level)

        # Initialize components
        self._init_components()

        # Load state
        self.state = self._load_state()

        self.logger.info("Agent initialized", version=self.config.get("agent.version"))

    def _init_components(self):
        """Initialize agent components."""
        # Initialize AI adapter
        ai_config = self.config.get_ai_config()
        self.model = ModelFactory.create(
            provider=ai_config["provider"],
            api_key=ai_config["api_key"],
            model=ai_config.get("model", "claude-sonnet-4-20250514"),
        )

        # Initialize content generator
        self.generator = ContentGenerator(
            model_adapter=self.model,
            max_tokens=ai_config.get("max_tokens", 4000),
            temperature=ai_config.get("temperature", 0.3),
        )

        # Initialize GitHub ops
        github_config = self.config.get_github_config()
        self.content_ops = ContentOps(
            github_token=github_config["token"],
            owner=github_config["owner"],
            repo=github_config["repo"],
        )
        self.pr_manager = PRManager(
            github_token=github_config["token"],
            owner=github_config["owner"],
            repo=github_config["repo"],
        )

        # Initialize deduplication
        dedup_config = self.config.get_deduplication_config()
        self.dedup = DeduplicationManager(
            storage_path=dedup_config.get("storage", ".agent-state/deduplication_hashes.json")
        )

        # Initialize rate limiter
        rate_limit_config = ai_config.get("rate_limit", {})
        self.rate_limiter = RateLimiter(
            requests_per_minute=rate_limit_config.get("requests_per_minute", 50),
            tokens_per_minute=rate_limit_config.get("tokens_per_minute", 150000),
        )

    def _load_state(self) -> dict:
        """Load agent state from file.

        Returns:
            State dictionary
        """
        state_config = self.config.get_state_config()
        state_path = Path(state_config.get("storage_path", ".agent-state/state.json"))

        if not state_path.exists():
            return {
                "last_run": None,
                "sources": {},
            }

        try:
            with open(state_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error("Failed to load state", error=str(e))
            return {"last_run": None, "sources": {}}

    def _save_state(self):
        """Save agent state to file."""
        state_config = self.config.get_state_config()
        state_path = Path(state_config.get("storage_path", ".agent-state/state.json"))

        # Ensure directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # Update last run time
        self.state["last_run"] = datetime.now().isoformat()

        # Write state
        with open(state_path, "w") as f:
            json.dump(self.state, f, indent=2)

    def run(self):
        """Run the agent workflow."""
        self.logger.info("Agent run started")

        try:
            # Discover content
            discovered_items = self._discover_content()
            self.logger.info("Discovery complete", item_count=len(discovered_items))

            # Generate and publish content
            results = self._process_items(discovered_items)

            # Save state
            self._save_state()

            # Log summary
            self._log_summary(results)

            self.logger.info("Agent run completed")

        except Exception as e:
            self.logger.error("Agent run failed", error=str(e))
            raise

    def _discover_content(self) -> list[DiscoveredItem]:
        """Discover content from all sources.

        Returns:
            List of discovered items
        """
        all_items = []
        sources = self.config.get_sources(enabled_only=True)

        github_token = self.config.get_github_config()["token"]

        for source_config in sources:
            source_id = source_config["id"]
            source_type = source_config["type"]

            self.logger.info("Discovering from source", source_id=source_id, source_type=source_type)

            try:
                # Get last processed ID for this source
                last_processed_id = self.state["sources"].get(source_id, {}).get(
                    "last_processed_id"
                )

                # Create discoverer
                if source_type == "github":
                    discoverer = GitHubDiscoverer(source_id, source_config, github_token)
                elif source_type == "arxiv":
                    discoverer = ArxivDiscoverer(source_id, source_config)
                else:
                    self.logger.warning("Unknown source type", source_type=source_type)
                    continue

                # Discover items
                items = discoverer.discover(last_processed_id)

                if items:
                    # Update state with latest ID
                    latest_id = self._get_latest_id(items, source_type)
                    self.state["sources"][source_id] = {
                        "last_processed_id": latest_id,
                        "last_processed_date": datetime.now().isoformat(),
                    }

                    # Add source config to items
                    for item in items:
                        item.metadata["source_id"] = source_id
                        item.metadata["domain"] = source_config["domain"]
                        item.metadata["level"] = source_config["level"]

                    all_items.extend(items)

                self.logger.info("Discovered items", source_id=source_id, count=len(items))

            except Exception as e:
                self.logger.error("Discovery failed", source_id=source_id, error=str(e))
                continue

        return all_items

    def _get_latest_id(self, items: list[DiscoveredItem], source_type: str) -> Optional[str]:
        """Get latest item ID for state tracking.

        Args:
            items: List of discovered items
            source_type: Source type

        Returns:
            Latest item ID or None
        """
        if not items:
            return None

        if source_type == "github":
            return items[0].metadata.get("tag_name")
        elif source_type == "arxiv":
            return items[0].metadata.get("arxiv_id")

        return None

    def _process_items(self, items: list[DiscoveredItem]) -> dict:
        """Process discovered items.

        Args:
            items: List of discovered items

        Returns:
            Results dictionary
        """
        results = {
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "duplicates": 0,
        }

        for item in items:
            try:
                result = self._process_item(item)
                results[result] += 1
            except Exception as e:
                self.logger.error("Item processing failed", title=item.title, error=str(e))
                results["failed"] += 1
                continue

        return results

    def _process_item(self, item: DiscoveredItem) -> str:
        """Process a single discovered item.

        Args:
            item: Discovered item

        Returns:
            Result status: "succeeded", "failed", "skipped", "duplicates"
        """
        # Check for duplicates
        is_duplicate, existing_path = self.dedup.is_duplicate(
            item.title, item.body or item.description or ""
        )

        if is_duplicate:
            self.logger.info(
                "Duplicate detected",
                title=item.title,
                existing_path=existing_path,
            )
            return "duplicates"

        # Extract metadata
        domain = item.metadata.get("domain", "ai")
        level = item.metadata.get("level", "intermediate")
        category = "article"  # Default category

        # Rate limiting
        self.rate_limiter.wait_if_needed(estimated_tokens=4000)

        # Generate content
        self.logger.info("Generating content", title=item.title)
        generated = self.generator.generate(item, domain, level, category)

        # Format as markdown
        markdown_content = self.generator.format_output(generated)

        # Create slug and file path
        slug = self.content_ops.generate_slug(item.title)
        file_path = self.content_ops.generate_file_path(domain, level, category, slug)

        # Create branch
        branch_name = self.content_ops.generate_branch_name(domain, level, slug)
        self.content_ops.create_branch(branch_name)

        # Commit content
        commit_message = f"Add {category}: {item.title}"
        self.content_ops.commit_file(file_path, markdown_content, commit_message, branch_name)

        # Create PR
        pr_metadata = {
            "title": item.title,
            "domain": domain,
            "level": level,
            "category": category,
            "source_url": item.url,
            "credibility_score": generated["frontmatter"].get("credibility_score", 0),
            "description": generated["frontmatter"].get("description", ""),
            "tags": generated["frontmatter"].get("tags", []),
        }

        github_config = self.config.get_github_config()
        pr_number = self.pr_manager.create_content_pr(
            branch_name,
            pr_metadata,
            labels=github_config.get("pr_labels", []),
            reviewers=github_config.get("reviewers", []),
        )

        self.logger.info(
            "Content published",
            title=item.title,
            pr_number=pr_number,
            branch=branch_name,
        )

        # Add to deduplication
        self.dedup.add_hash(item.title, item.body or "", domain, level, file_path)

        return "succeeded"

    def _log_summary(self, results: dict):
        """Log run summary.

        Args:
            results: Results dictionary
        """
        self.logger.info(
            "Run summary",
            succeeded=results["succeeded"],
            failed=results["failed"],
            skipped=results["skipped"],
            duplicates=results["duplicates"],
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Agent")
    parser.add_argument(
        "--config", default="scripts/config.yaml", help="Path to configuration file"
    )
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")

    args = parser.parse_args()

    # Initialize and run agent
    agent = KnowledgeBaseAgent(config_path=args.config)
    agent.run()


if __name__ == "__main__":
    main()

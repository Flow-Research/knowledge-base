"""Main orchestrator for knowledge base agent."""

import json
import time
from datetime import datetime
from pathlib import Path

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
            with open(state_path) as f:
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

    def run(self, dry_run=False, no_pr=False, source_filter=None, verbose=False):
        """Run the agent workflow.

        Args:
            dry_run: If True, don't make any changes
            no_pr: If True, generate content but skip PR creation
            source_filter: Only run this source ID
            verbose: Enable verbose logging
        """
        self.dry_run = dry_run
        self.no_pr = no_pr
        self.verbose = verbose

        self.logger.info("Agent run started", dry_run=dry_run, no_pr=no_pr)

        try:
            # Discover content
            discovered_items = self._discover_content(source_filter)
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
    def _discover_content(self, source_filter=None) -> list[DiscoveredItem]:
        """Discover content from all sources.

        Args:
            source_filter: Only run this source ID (optional)

        Returns:
            List of discovered items
        """
        all_items = []
        sources = self.config.get_sources(enabled_only=True)

        # Filter sources if specified
        if source_filter:
            sources = [s for s in sources if s["id"] == source_filter]
            if not sources:
                self.logger.warning("Source not found", source_id=source_filter)
                return []

        github_token = self.config.get_github_config()["token"]

        for i, source_config in enumerate(sources):
            source_id = source_config["id"]
            source_type = source_config["type"]

            self.logger.info(
                "Discovering from source",
                source_id=source_id,
                source_type=source_type,
                progress=f"{i+1}/{len(sources)}"
            )

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

                # Discover items with progress
                self.logger.debug("Starting discovery...", source_id=source_id)
                items = discoverer.discover(last_processed_id)
                self.logger.info(
                    "Discovery complete",
                    source_id=source_id,
                    items_found=len(items)
                )

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

            except Exception as e:
                self.logger.error("Discovery failed", source_id=source_id, error=str(e))
                continue

        return all_items

    def _get_latest_id(self, items: list[DiscoveredItem], source_type: str) -> str | None:
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

        self.logger.info("Processing items", total=len(items))

        for i, item in enumerate(items):
            self.logger.debug(
                "Processing item",
                progress=f"{i+1}/{len(items)}",
                title=item.title[:50]
            )
            try:
                result = self._process_item(item)
                results[result] += 1
                self.logger.info(
                    "Item processed",
                    status=result,
                    progress=f"{i+1}/{len(items)}"
                )
            except Exception as e:
                self.logger.error("Item processing failed", title=item.title[:50], error=str(e))
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
        category = "articles"  # Default category

        # Dry run check
        if hasattr(self, 'dry_run') and self.dry_run:
            self.logger.info(
                "[DRY-RUN] Would process item",
                title=item.title[:50],
                domain=domain,
                level=level
            )
            return "skipped"

        # Rate limiting
        self.rate_limiter.wait_if_needed(estimated_tokens=4000)

        # Generate content
        self.logger.info("Generating content", title=item.title[:50])
        generated = self.generator.generate(item, domain, level, category)

        # Format as markdown
        markdown_content = self.generator.format_output(generated)

        # Create slug and file path
        slug = self.content_ops.generate_slug(item.title)
        file_path = self.content_ops.generate_file_path(domain, level, category, slug)

        if hasattr(self, 'verbose') and self.verbose:
            self.logger.info(
                "Generated content details",
                file_path=file_path,
                word_count=len(markdown_content.split())
            )

        # No-PR check: skip branch/commit/PR creation
        if hasattr(self, 'no_pr') and self.no_pr:
            self.logger.info(
                "[NO-PR] Content generated (not creating PR)",
                title=item.title[:50],
                file_path=file_path
            )
            # Save to local file for inspection
            output_dir = Path(".agent-state/generated")
            output_dir.mkdir(parents=True, exist_ok=True)
            local_path = output_dir / f"{slug}.md"
            local_path.write_text(markdown_content)
            self.logger.info("Saved locally", path=str(local_path))
            return "succeeded"

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


def test_github_connection():
    """Test GitHub API connection."""
    import os

    from github import Github

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        return

    print("Testing GitHub API connection...")
    client = Github(token)

    # Check rate limit
    print("\nChecking rate limit...")
    rate = client.get_rate_limit()
    print(f"Remaining: {rate.core.remaining}/{rate.core.limit}")

    if rate.core.remaining < 10:
        print("WARNING: Low API quota!")

    # Test fetching a repo
    print("\nFetching openai/openai-python...")
    start = time.time()
    repo = client.get_repo("openai/openai-python")
    print(f"Got repo in {time.time()-start:.1f}s")

    # Test fetching releases
    print("\nFetching releases...")
    start = time.time()
    releases = list(repo.get_releases())[:3]
    print(f"Got {len(releases)} releases in {time.time()-start:.1f}s")

    for r in releases:
        print(f"  - {r.tag_name}: {r.title[:50]}..." if r.title else f"  - {r.tag_name}")

    print("\n✅ GitHub API connection successful!")


def test_arxiv_connection():
    """Test arXiv API connection."""
    from .discovery import ArxivDiscoverer

    print("Testing arXiv API connection...")

    config = {
        "id": "test",
        "query": {"categories": ["cs.AI"], "max_results": 3},
        "keywords": []
    }

    start = time.time()
    discoverer = ArxivDiscoverer("test", config)
    items = discoverer.discover()
    print(f"Found {len(items)} papers in {time.time()-start:.1f}s")

    for item in items[:3]:
        print(f"  - {item.title[:60]}...")

    print("\n✅ arXiv API connection successful!")


def test_ai_connection():
    """Test AI model connection."""
    import os

    from .adapters import GenerationRequest, ModelFactory

    print("Testing AI model connection...")

    # Check for API key
    provider = os.environ.get("AI_PROVIDER", "openai")
    key_env = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(key_env)

    if not api_key:
        print(f"ERROR: {key_env} not set")
        return

    # Create adapter
    adapter = ModelFactory.create(
        provider=provider,
        api_key=api_key,
        model="claude-sonnet-4-20250514" if provider == "anthropic" else "gpt-5.2"
    )

    # Test generation
    print(f"\nTesting {adapter.get_name()}...")
    request = GenerationRequest(
        prompt="What is 2+2? Answer with just the number.",
        max_tokens=10,
        temperature=0
    )

    start = time.time()
    response = adapter.generate(request)
    print(f"Response in {time.time()-start:.1f}s: {response.content.strip()}")
    print(f"Tokens used: {response.usage}")

    print("\n✅ AI model connection successful!")



def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Agent")
    parser.add_argument(
        "--config", default="scripts/config.yaml", help="Path to configuration file"
    )
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes)")
    parser.add_argument("--no-pr", action="store_true", help="Generate content but skip PR creation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--source", help="Run specific source only (e.g., github_ai_releases)")
    parser.add_argument("--test-github", action="store_true", help="Test GitHub API connection")
    parser.add_argument("--test-arxiv", action="store_true", help="Test arXiv API connection")
    parser.add_argument("--test-ai", action="store_true", help="Test AI model connection")

    args = parser.parse_args()

    # Handle test modes
    if args.test_github:
        test_github_connection()
        return
    if args.test_arxiv:
        test_arxiv_connection()
        return
    if args.test_ai:
        test_ai_connection()
        return

    # Initialize and run agent
    agent = KnowledgeBaseAgent(config_path=args.config)

    # Set verbose mode
    if args.verbose:
        agent.logger.setLevel("DEBUG")

    # Run with options
    agent.run(
        dry_run=args.dry_run,
        no_pr=args.no_pr,
        source_filter=args.source,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()

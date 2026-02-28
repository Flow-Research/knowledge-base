"""Tests for content generator."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from scripts.adapters import GenerationResponse
from scripts.discovery import DiscoveredItem
from scripts.generation import ContentGenerator


class TestContentGenerator:
    """Test ContentGenerator."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock model adapter."""
        adapter = MagicMock()
        adapter.generate.return_value = GenerationResponse(
            content="# Test Article\\n\\nThis is a test article.",
            model="test-model",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        return adapter

    @pytest.fixture
    def sample_item(self):
        """Create sample discovered item."""
        return DiscoveredItem(
            title="Test Article",
            url="https://example.com/article",
            source_type="github",
            discovered_at=datetime.now(),
            description="A test article description",
            author="Test Author",
            published_at=datetime.now(),
            tags=["test", "python"],
            body="This is the full body of the test article.",
            metadata={"stars": 5000, "source_id": "test-source"},
        )

    def test_generate_content(self, mock_adapter, sample_item):
        """Test content generation."""
        generator = ContentGenerator(mock_adapter)

        result = generator.generate(sample_item, "ai", "beginner", "article")

        assert "frontmatter" in result
        assert "content" in result

        frontmatter = result["frontmatter"]
        assert frontmatter["title"] == "Test Article"
        assert frontmatter["domain"] == "ai"
        assert frontmatter["level"] == "beginner"
        assert frontmatter["category"] == "article"
        assert frontmatter["status"] == "pending-review"

    def test_calculate_credibility_score_arxiv(self, mock_adapter):
        """Test credibility score for arXiv source."""
        generator = ContentGenerator(mock_adapter)

        item = DiscoveredItem(
            title="Research Paper",
            url="https://arxiv.org/abs/1234.5678",
            source_type="arxiv",
            discovered_at=datetime.now(),
            published_at=datetime.now(),
            body="A" * 1500,  # Long body
            metadata={},
        )

        score = generator._calculate_credibility_score(item)
        # arxiv (4) + recent (3) + content completeness (2) + metadata (1) = 10
        assert score >= 8  # Should be high for recent arxiv with good content

    def test_calculate_credibility_score_github_popular(self, mock_adapter):
        """Test credibility score for popular GitHub repo."""
        generator = ContentGenerator(mock_adapter)

        item = DiscoveredItem(
            title="Popular Release",
            url="https://github.com/org/repo",
            source_type="github",
            discovered_at=datetime.now(),
            published_at=datetime.now(),
            body="A" * 1500,
            metadata={"stars": 15000},
        )

        score = generator._calculate_credibility_score(item)
        assert score >= 8  # High stars + recent + good content

    def test_format_output(self, mock_adapter):
        """Test markdown output formatting."""
        generator = ContentGenerator(mock_adapter)

        generated = {
            "frontmatter": {
                "title": "Test",
                "domain": "ai",
                "level": "beginner",
            },
            "content": "# Test\\n\\nContent here.",
        }

        output = generator.format_output(generated)

        assert output.startswith("---\\n")
        assert "title: Test" in output
        assert "domain: ai" in output
        assert "# Test" in output

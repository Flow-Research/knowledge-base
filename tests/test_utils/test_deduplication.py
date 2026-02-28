"""Tests for deduplication manager."""

import tempfile
from pathlib import Path

import pytest

from scripts.utils import DeduplicationManager


class TestDeduplicationManager:
    """Test DeduplicationManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_generate_hash(self, temp_storage):
        """Test hash generation."""
        manager = DeduplicationManager(temp_storage)

        hash1 = manager.generate_hash("Test Title", "Test body content")
        hash2 = manager.generate_hash("Test Title", "Test body content")

        # Same input should produce same hash
        assert hash1 == hash2

        # Different input should produce different hash
        hash3 = manager.generate_hash("Different Title", "Test body content")
        assert hash1 != hash3

    def test_is_duplicate_new_content(self, temp_storage):
        """Test duplicate check for new content."""
        manager = DeduplicationManager(temp_storage)

        is_duplicate, path = manager.is_duplicate("New Title", "New body")
        assert not is_duplicate
        assert path is None

    def test_add_and_check_duplicate(self, temp_storage):
        """Test adding hash and checking for duplicates."""
        manager = DeduplicationManager(temp_storage)

        # Add content
        content_hash = manager.add_hash(
            title="Test Article",
            body="This is the test article body content",
            domain="ai",
            level="beginner",
            file_path="content/ai/beginner/articles/test.md",
        )

        assert content_hash is not None

        # Check for duplicate
        is_duplicate, path = manager.is_duplicate(
            "Test Article", "This is the test article body content"
        )

        assert is_duplicate
        assert path == "content/ai/beginner/articles/test.md"

    def test_get_stats(self, temp_storage):
        """Test getting deduplication statistics."""
        manager = DeduplicationManager(temp_storage)

        # Add some hashes
        manager.add_hash("Article 1", "Body 1", "ai", "beginner", "path1.md")
        manager.add_hash("Article 2", "Body 2", "ai", "intermediate", "path2.md")
        manager.add_hash("Article 3", "Body 3", "blockchain", "master", "path3.md")

        stats = manager.get_stats()

        assert stats["total_hashes"] == 3
        assert stats["by_domain"]["ai"] == 2
        assert stats["by_domain"]["blockchain"] == 1
        assert stats["by_level"]["beginner"] == 1
        assert stats["by_level"]["intermediate"] == 1
        assert stats["by_level"]["master"] == 1

    def test_remove_hash(self, temp_storage):
        """Test removing hash."""
        manager = DeduplicationManager(temp_storage)

        # Add content
        content_hash = manager.add_hash(
            "Test", "Body", "ai", "beginner", "test.md"
        )

        # Remove hash
        removed = manager.remove_hash(content_hash)
        assert removed

        # Check it's gone
        is_duplicate, _ = manager.is_duplicate("Test", "Body")
        assert not is_duplicate

    def test_clear_all(self, temp_storage):
        """Test clearing all hashes."""
        manager = DeduplicationManager(temp_storage)

        # Add some hashes
        manager.add_hash("Article 1", "Body 1", "ai", "beginner", "path1.md")
        manager.add_hash("Article 2", "Body 2", "ai", "intermediate", "path2.md")

        # Clear all
        manager.clear_all()

        stats = manager.get_stats()
        assert stats["total_hashes"] == 0

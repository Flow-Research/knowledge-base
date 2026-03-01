"""Content deduplication using SHA-256 hashing."""

import hashlib
import json
from datetime import datetime
from pathlib import Path


class DeduplicationManager:
    """Manages content deduplication using hash-based detection."""

    def __init__(self, storage_path: str = ".agent-state/deduplication_hashes.json"):
        """Initialize deduplication manager.

        Args:
            storage_path: Path to hash storage file
        """
        self.storage_path = Path(storage_path)
        self.hashes = self._load_hashes()

    def _load_hashes(self) -> dict:
        """Load existing hashes from storage.

        Returns:
            Dict of hashes and metadata
        """
        if not self.storage_path.exists():
            return {"hashes": {}, "last_updated": None, "total_hashes": 0}

        try:
            with open(self.storage_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading hashes: {e}")
            return {"hashes": {}, "last_updated": None, "total_hashes": 0}

    def _save_hashes(self) -> None:
        """Save hashes to storage."""
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Update metadata
        self.hashes["last_updated"] = datetime.now().isoformat()
        self.hashes["total_hashes"] = len(self.hashes["hashes"])

        # Write to file
        with open(self.storage_path, "w") as f:
            json.dump(self.hashes, f, indent=2)

    def generate_hash(self, title: str, body_preview: str) -> str:
        """Generate SHA-256 hash from title and body preview.

        Args:
            title: Content title
            body_preview: First 500 chars of body

        Returns:
            SHA-256 hash string
        """
        # Normalize inputs
        normalized_title = title.lower().strip()
        normalized_body = body_preview[:500].lower().strip()

        # Create hash input
        hash_input = f"{normalized_title}||{normalized_body}"

        # Generate SHA-256 hash
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        return content_hash

    def is_duplicate(
        self, title: str, body: str | None = None
    ) -> tuple[bool, str | None]:
        """Check if content is a duplicate.

        Args:
            title: Content title
            body: Content body (optional)

        Returns:
            Tuple of (is_duplicate, existing_file_path)
        """
        body_preview = (body or "")[:500]
        content_hash = self.generate_hash(title, body_preview)

        if content_hash in self.hashes["hashes"]:
            existing = self.hashes["hashes"][content_hash]
            return True, existing.get("file_path")

        return False, None

    def add_hash(
        self,
        title: str,
        body: str,
        domain: str,
        level: str,
        file_path: str,
    ) -> str:
        """Add content hash to storage.

        Args:
            title: Content title
            body: Content body
            domain: Content domain
            level: Content level
            file_path: Path to content file

        Returns:
            Generated hash
        """
        body_preview = body[:500]
        content_hash = self.generate_hash(title, body_preview)

        # Check for collision (very unlikely with SHA-256)
        if content_hash in self.hashes["hashes"]:
            existing = self.hashes["hashes"][content_hash]
            if existing.get("title") != title:
                # Potential collision - add timestamp suffix
                timestamp = datetime.now().isoformat()
                content_hash = self.generate_hash(title, f"{body_preview}||{timestamp}")
                print("Warning: Hash collision detected, using timestamped hash")

        # Store hash metadata
        self.hashes["hashes"][content_hash] = {
            "title": title,
            "domain": domain,
            "level": level,
            "file_path": file_path,
            "created_at": datetime.now().isoformat(),
        }

        # Save to file
        self._save_hashes()

        return content_hash

    def remove_hash(self, content_hash: str) -> bool:
        """Remove hash from storage.

        Args:
            content_hash: Hash to remove

        Returns:
            True if removed, False if not found
        """
        if content_hash in self.hashes["hashes"]:
            del self.hashes["hashes"][content_hash]
            self._save_hashes()
            return True
        return False

    def get_stats(self) -> dict:
        """Get deduplication statistics.

        Returns:
            Dict with statistics
        """
        hashes_by_domain = {}
        hashes_by_level = {}

        for hash_data in self.hashes["hashes"].values():
            domain = hash_data.get("domain", "unknown")
            level = hash_data.get("level", "unknown")

            hashes_by_domain[domain] = hashes_by_domain.get(domain, 0) + 1
            hashes_by_level[level] = hashes_by_level.get(level, 0) + 1

        return {
            "total_hashes": len(self.hashes["hashes"]),
            "last_updated": self.hashes.get("last_updated"),
            "by_domain": hashes_by_domain,
            "by_level": hashes_by_level,
        }

    def clear_all(self) -> None:
        """Clear all stored hashes.

        Warning: This is destructive and cannot be undone.
        """
        self.hashes = {"hashes": {}, "last_updated": None, "total_hashes": 0}
        self._save_hashes()

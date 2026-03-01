"""Git file operations for content management."""

from datetime import datetime

from github import Github
from github.GithubException import GithubException


class ContentOps:
    """Handles Git operations for content files."""

    def __init__(self, github_token: str, owner: str, repo: str):
        """Initialize content operations.

        Args:
            github_token: GitHub API token
            owner: Repository owner
            repo: Repository name
        """
        self.client = Github(github_token)
        self.repo = self.client.get_repo(f"{owner}/{repo}")
        self.owner = owner
        self.repo_name = repo

    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch.

        Args:
            branch_name: Name for new branch
            base_branch: Branch to branch from

        Returns:
            True if created successfully

        Raises:
            GithubException: If branch creation fails
        """
        try:
            # Get base branch SHA
            base = self.repo.get_branch(base_branch)
            base_sha = base.commit.sha

            # Create new branch
            self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

            return True
        except GithubException as e:
            if e.status == 422:  # Branch already exists
                return False
            raise

    def commit_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str,
    ) -> bool:
        """Commit a file to a branch.

        Args:
            file_path: Path to file in repository
            content: File content
            commit_message: Commit message
            branch: Branch to commit to

        Returns:
            True if committed successfully

        Raises:
            GithubException: If commit fails
        """
        try:
            # Check if file exists
            try:
                existing_file = self.repo.get_contents(file_path, ref=branch)
                # Update existing file
                self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch,
                )
            except GithubException as e:
                if e.status == 404:
                    # Create new file
                    self.repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        branch=branch,
                    )
                else:
                    raise

            return True
        except GithubException:
            raise

    def delete_file(
        self,
        file_path: str,
        commit_message: str,
        branch: str,
    ) -> bool:
        """Delete a file from a branch.

        Args:
            file_path: Path to file in repository
            commit_message: Commit message
            branch: Branch to delete from

        Returns:
            True if deleted successfully

        Raises:
            GithubException: If deletion fails
        """
        try:
            # Get file to get SHA
            existing_file = self.repo.get_contents(file_path, ref=branch)

            # Delete file
            self.repo.delete_file(
                path=file_path,
                message=commit_message,
                sha=existing_file.sha,
                branch=branch,
            )

            return True
        except GithubException:
            raise

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists.

        Args:
            branch_name: Branch name to check

        Returns:
            True if branch exists
        """
        try:
            self.repo.get_branch(branch_name)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise

    def delete_branch(self, branch_name: str) -> bool:
        """Delete a branch.

        Args:
            branch_name: Branch name to delete

        Returns:
            True if deleted successfully

        Raises:
            GithubException: If deletion fails
        """
        try:
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            return True
        except GithubException:
            raise

    def generate_file_path(
        self, domain: str, level: str, category: str, slug: str
    ) -> str:
        """Generate file path for content.

        Args:
            domain: Content domain
            level: Difficulty level
            category: Content category
            slug: URL-friendly slug

        Returns:
            File path string
        """
        return f"src/content/{domain}/{level}/{category}/{slug}.md"

    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title.

        Args:
            title: Content title

        Returns:
            URL-friendly slug
        """
        import re

        # Convert to lowercase
        slug = title.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        # Trim hyphens from ends
        slug = slug.strip("-")

        # Limit length
        slug = slug[:100]

        return slug

    def generate_branch_name(
        self, domain: str, level: str, slug: str, timestamp: str | None = None
    ) -> str:
        """Generate branch name for PR.

        Args:
            domain: Content domain
            level: Difficulty level
            slug: Content slug
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Branch name string
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        return f"agent/content/{timestamp}/{domain}/{level}/{slug}"

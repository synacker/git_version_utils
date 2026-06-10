import os
import re
import subprocess
from functools import cached_property


class GitVersion:
    """Extract version information from a Git repository.

    Args:
        repo_path: Path to the Git repository (default: current working directory).
        tag_pattern: Glob pattern to match version tags (default: "v[0-9]*").
    """

    def __init__(
        self,
        repo_path: str | None = None,
        tag_pattern: str = "v[0-9]*",
    ):
        self.repo_path = os.path.abspath(repo_path or os.getcwd())
        self.tag_pattern = tag_pattern

    def _git(self, *args: str) -> str:
        """Execute a git command safely and return stripped stdout."""
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, *args],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, TimeoutError):
            return ""

    @cached_property
    def tag(self) -> str:
        """Latest version tag matching the tag pattern (e.g. 'v1.2.3')."""
        return self._git(
            "describe", "--match", self.tag_pattern, "--abbrev=0", "--tags"
        )

    @cached_property
    def version(self) -> str:
        """Full version string: '<semver>.<build>' (e.g. '1.2.3.42')."""
        tag = self.tag
        if not tag:
            return "0.0.0.0"
        stripped = re.sub(r"^[^\d]+", "", tag)
        return f"{stripped}.{self.build}"

    @cached_property
    def version_major(self) -> str:
        """Major version component."""
        parts = self.version.split(".")
        return parts[0] if len(parts) > 0 else "0"

    @cached_property
    def version_minor(self) -> str:
        """Minor version component."""
        parts = self.version.split(".")
        return parts[1] if len(parts) > 1 else "0"

    @cached_property
    def version_patch(self) -> str:
        """Patch version component."""
        parts = self.version.split(".")
        return parts[2] if len(parts) > 2 else "0"

    @cached_property
    def default_branch(self) -> str:
        """Default branch name from git config (falls back to 'master')."""
        result = self._git("config", "--get", "init.defaultBranch")
        return result or "master"

    @cached_property
    def build(self) -> str:
        """Number of commits since the last version tag."""
        tag = self.tag
        if not tag:
            return "0"
        return self._git("rev-list", f"{tag}..", "--count")

    @cached_property
    def branch(self) -> str:
        """Current branch name."""
        return self._git("branch", "--show-current")

    @cached_property
    def short(self) -> str:
        """Short 6-character commit hash."""
        return self._git("rev-parse", "--short=6", "HEAD")

    @cached_property
    def full(self) -> str:
        """Full version string with commit hash: '<version>-<short>'."""
        return f"{self.version}-{self.short}"

    @cached_property
    def extended(self) -> str:
        """Extended version: same as 'version' if build==0, else 'full'."""
        if self.build == "0":
            return self.version
        return f"{self.version}-{self.short}"

    @cached_property
    def commit(self) -> str:
        """Full 40-character commit hash."""
        return self._git("rev-parse", "HEAD")

    def env(self, prefix: str = "BUILD_VERSION") -> dict[str, str]:
        """Return all version info as a dictionary of environment variables.

        Args:
            prefix: Prefix for all variable names (default: "BUILD_VERSION").

        Returns:
            Dict mapping variable names to values, e.g.:
            {"BUILD_VERSION": "1.2.3.42", "BUILD_VERSION_MAJOR": "1", ...}
        """
        return {
            f"{prefix}": self.version,
            f"{prefix}_MAJOR": self.version_major,
            f"{prefix}_MINOR": self.version_minor,
            f"{prefix}_PATCH": self.version_patch,
            f"{prefix}_BUILD": self.build,
            f"{prefix}_TAG": self.tag,
            f"{prefix}_FULL": self.full,
            f"{prefix}_EXTENDED": self.extended,
            f"{prefix}_SHORT": self.short,
            f"{prefix}_COMMIT": self.commit,
            f"{prefix}_BRANCH": self.branch,
            f"{prefix}_DEFAULT_BRANCH": self.default_branch,
        }

    def __str__(self) -> str:
        return f"""
        Tag: {self.tag}
        Version: {self.version}
        Full: {self.full}
        Branch: {self.branch}
        Build: {self.build}
        Extended: {self.extended}
        Commit: {self.commit}
        """
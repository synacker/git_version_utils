import os
import re
import subprocess
import fnmatch
from functools import cached_property


class GitVersion:
    """Extract version information from a Git repository.

    Args:
        repo_path: Path to the Git repository (default: current working directory).
        tag_pattern: Glob pattern to match version tags (default: "v[0-9]*").
        release_branches: List of branch patterns considered as release branches.
            Defaults to [default_branch, "release/*"].
        safe_directory: Pass ``-c safe.directory=<value>`` to every git command.
            Use ``"*"`` to allow all directories (useful in Docker containers).
    """

    def __init__(
        self,
        repo_path: str | None = None,
        tag_pattern: str = "v[0-9]*",
        release_branches: list[str] | None = None,
        safe_directory: str | None = None,
    ):
        self.repo_path = os.path.abspath(repo_path or os.getcwd())
        self.tag_pattern = tag_pattern
        self._release_branches = release_branches
        self._safe_directory = safe_directory

    def _git(self, *args: str) -> str:
        """Execute a git command safely and return stripped stdout."""
        try:
            cmd = ["git", "-C", self.repo_path]
            if self._safe_directory is not None:
                cmd.extend(["-c", f"safe.directory={self._safe_directory}"])
            cmd.extend(args)
            result = subprocess.run(
                cmd,
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
    def release_branches(self) -> list[str]:
        """List of release branch patterns.

        Defaults to [default_branch, "release/*"] if not explicitly set.
        """
        if self._release_branches is not None:
            return self._release_branches
        return [self.default_branch, "release/*"]

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
        """Full version string.

        If the current branch matches a release branch pattern, returns just the
        version (e.g. '1.0.0.1'). Otherwise returns the extended version with
        commit hash (e.g. '1.0.0.1-a1b2c3').
        """
        if self._is_release_branch():
            return self.version
        return self.extended

    @cached_property
    def extended(self) -> str:
        """Extended version: '<version>-<short>' (e.g. '1.0.0.1-a1b2c3')."""
        return f"{self.version}-{self.short}"

    def _is_release_branch(self) -> bool:
        """Check if the current branch matches any release branch pattern."""
        current = self.branch
        if not current:
            return False
        for pattern in self.release_branches:
            if fnmatch.fnmatch(current, pattern):
                return True
        return False

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
            f"{prefix}_RELEASE_BRANCHES": " ".join(self.release_branches),
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
        Release branches: {", ".join(self.release_branches)}
        """
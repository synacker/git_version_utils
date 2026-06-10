import tempfile
import subprocess
from pathlib import Path

import pytest

from git_version import GitVersion


@pytest.fixture
def git_repo():
    """Create a temporary git repository with a tag for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo, capture_output=True, check=True,
        )

        # Create initial commit
        (repo / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=repo, capture_output=True, check=True,
        )

        # Create a tag
        subprocess.run(
            ["git", "tag", "v1.0.0"],
            cwd=repo, capture_output=True, check=True,
        )

        # Create a second commit
        (repo / "file.txt").write_text("hello world")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "second"],
            cwd=repo, capture_output=True, check=True,
        )

        yield repo


class TestGitVersion:
    def test_tag(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.tag == "v1.0.0"

    def test_version(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.version == "1.0.0.1"  # 1 commit after tag

    def test_version_major(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.version_major == "1"

    def test_version_minor(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.version_minor == "0"

    def test_version_patch(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.version_patch == "0"

    def test_build(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.build == "1"

    def test_branch(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.branch == "master"

    def test_short(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert len(gv.short) == 6

    def test_full_on_release_branch(self, git_repo):
        """On a release branch (master), full should equal version."""
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.full == gv.version
        assert gv.full == "1.0.0.1"

    def test_full_on_non_release_branch(self, git_repo):
        """On a non-release branch, full should equal extended (version-short)."""
        gv = GitVersion(
            repo_path=str(git_repo),
            release_branches=["main", "release/*"],
        )
        assert gv.full == gv.extended
        assert gv.full == f"1.0.0.1-{gv.short}"

    def test_extended_with_build(self, git_repo):
        """Extended always includes commit hash."""
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.extended == f"{gv.version}-{gv.short}"

    def test_extended_always_contains_commit(self, git_repo):
        """Extended always includes version and short commit hash."""
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.extended == f"{gv.version}-{gv.short}"

    def test_commit(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert len(gv.commit) == 40

    def test_default_branch(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        assert gv.default_branch == "master"

    def test_env(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        env = gv.env(prefix="TEST")
        assert env["TEST"] == "1.0.0.1"
        assert env["TEST_MAJOR"] == "1"
        assert env["TEST_MINOR"] == "0"
        assert env["TEST_PATCH"] == "0"
        assert env["TEST_BUILD"] == "1"
        assert env["TEST_TAG"] == "v1.0.0"
        assert env["TEST_BRANCH"] == "master"
        assert env["TEST_FULL"] == env["TEST"]  # On release branch, full == version
        assert len(env["TEST_COMMIT"]) == 40
        assert len(env["TEST_SHORT"]) == 6

    def test_custom_tag_pattern(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo), tag_pattern="release-*")
        assert gv.tag == ""  # No matching tag

    def test_no_tag(self):
        """Repository without any tags should return defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=repo, capture_output=True, check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=repo, capture_output=True, check=True,
            )
            (repo / "file.txt").write_text("hello")
            subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "initial"],
                cwd=repo, capture_output=True, check=True,
            )

            gv = GitVersion(repo_path=str(repo))
            assert gv.tag == ""
            assert gv.version == "0.0.0.0"
            assert gv.build == "0"

    def test_not_a_git_repo(self):
        """Non-git directory should return defaults gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gv = GitVersion(repo_path=tmpdir)
            assert gv.tag == ""
            assert gv.version == "0.0.0.0"
            assert gv.build == "0"
            assert gv.branch == ""
            assert gv.short == ""
            assert gv.commit == ""

    def test_release_branches_default(self, git_repo):
        """Default release_branches should include default branch and release/*."""
        gv = GitVersion(repo_path=str(git_repo))
        branches = gv.release_branches
        assert "master" in branches
        assert "release/*" in branches
        assert len(branches) == 2

    def test_release_branches_custom(self, git_repo):
        """Custom release_branches should be returned as-is."""
        gv = GitVersion(
            repo_path=str(git_repo),
            release_branches=["main", "release/*", "hotfix/*"],
        )
        assert gv.release_branches == ["main", "release/*", "hotfix/*"]

    def test_release_branches_single(self, git_repo):
        """Single branch in release_branches list."""
        gv = GitVersion(
            repo_path=str(git_repo),
            release_branches=["main"],
        )
        assert gv.release_branches == ["main"]

    def test_release_branches_in_env(self, git_repo):
        """release_branches should appear in env output."""
        gv = GitVersion(repo_path=str(git_repo))
        env = gv.env(prefix="TEST")
        assert "TEST_RELEASE_BRANCHES" in env
        assert "master" in env["TEST_RELEASE_BRANCHES"]
        assert "release/*" in env["TEST_RELEASE_BRANCHES"]

    def test_release_branches_in_str(self, git_repo):
        """release_branches should appear in string representation."""
        gv = GitVersion(repo_path=str(git_repo))
        output = str(gv)
        assert "Release branches" in output
        assert "master" in output
        assert "release/*" in output

    def test_str(self, git_repo):
        gv = GitVersion(repo_path=str(git_repo))
        output = str(gv)
        assert "v1.0.0" in output
        assert "1.0.0.1" in output
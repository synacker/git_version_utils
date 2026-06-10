import argparse

from .core import GitVersion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract version information from a Git repository.",
    )
    parser.add_argument(
        "--prefix", "-p",
        default="BUILD_VERSION",
        help="Prefix for environment variable names (default: BUILD_VERSION)",
    )
    parser.add_argument(
        "--repo", "-r",
        default=None,
        help="Path to the Git repository (default: current working directory)",
    )
    parser.add_argument(
        "--tag-pattern", "-t",
        default="v[0-9]*",
        help="Glob pattern to match version tags (default: v[0-9]*)",
    )
    parser.add_argument(
        "--property", "-P",
        choices=[
            "tag", "version", "version_major", "version_minor", "version_patch",
            "build", "branch", "short", "full", "extended", "commit",
            "default_branch", "release_branches", "env", "all",
        ],
        default="all",
        help="Which property to output (default: all)",
    )
    args = parser.parse_args()

    gv = GitVersion(repo_path=args.repo, tag_pattern=args.tag_pattern)

    if args.property == "env":
        for key, value in gv.env(prefix=args.prefix).items():
            print(f"{key}={value}")
    elif args.property == "all":
        print(gv)
    else:
        print(getattr(gv, args.property))


if __name__ == "__main__":
    main()
# git-version-utils

Extract version information from a Git repository and output as environment variables.

## Installation

```bash
pip install git-version-utils
```

## Usage

### CLI

```bash
# Print all version info
git-version

# Output as environment variables (useful with `source` or `eval`)
git-version --property env

# Custom prefix for environment variables
git-version --prefix MYAPP --property env

# Custom tag pattern
git-version --tag-pattern "release-*" --property env

# Get a single property
git-version --property version
git-version --property version_major
git-version --property commit

# Specify repository path
git-version --repo /path/to/repo --property env
```

### Python API

```python
from git_version import GitVersion

gv = GitVersion(repo_path="/path/to/repo", tag_pattern="v[0-9]*")

print(gv.version)       # "1.2.3.42"
print(gv.version_major) # "1"
print(gv.version_minor) # "2"
print(gv.version_patch) # "3"
print(gv.build)         # "42"
print(gv.tag)           # "v1.2.3"
print(gv.branch)        # "main"
print(gv.short)         # "a1b2c3"
print(gv.full)          # "1.2.3.42-a1b2c3"
print(gv.commit)        # "a1b2c3d4e5f6..."

# Get all as environment variables
env_vars = gv.env(prefix="BUILD_VERSION")
for key, value in env_vars.items():
    print(f"{key}={value}")
```

## Environment Variables Output

With default prefix `BUILD_VERSION`:

| Variable | Example | Description |
|---|---|---|
| `BUILD_VERSION` | `1.2.3.42` | Full version: `<semver>.<build>` |
| `BUILD_VERSION_MAJOR` | `1` | Major version component |
| `BUILD_VERSION_MINOR` | `2` | Minor version component |
| `BUILD_VERSION_PATCH` | `3` | Patch version component |
| `BUILD_VERSION_BUILD` | `42` | Commits since last tag |
| `BUILD_VERSION_TAG` | `v1.2.3` | Latest matching git tag |
| `BUILD_VERSION_FULL` | `1.2.3.42-a1b2c3` | Version with commit hash |
| `BUILD_VERSION_EXTENDED` | `1.2.3.42-a1b2c3` | Full if build>0, else version |
| `BUILD_VERSION_SHORT` | `a1b2c3` | Short 6-char commit hash |
| `BUILD_VERSION_COMMIT` | `a1b2c3d4...` | Full 40-char commit hash |
| `BUILD_VERSION_BRANCH` | `main` | Current branch name |
| `BUILD_VERSION_DEFAULT_BRANCH` | `master` | Default branch from git config |

## CI/CD Integration

### Shell (source)

```bash
source <(git-version --property env)
echo "$BUILD_VERSION"
```

### CMake

```cmake
execute_process(
    COMMAND git-version --property env
    OUTPUT_VARIABLE GIT_VERSION_ENV
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
```

### Docker

```dockerfile
RUN pip install git-version-utils
RUN source <(git-version --property env) && echo "Building $BUILD_VERSION"

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
```

## Docker CI Container

A pre-built Docker image with `git-version-utils` is available at
`ghcr.io/synacker/git-version-utils`.

The image is based on `python:3.13-slim` and includes `git` + `git-version-utils`.
It is designed to be used as the **job container** in CI pipelines.

### Usage

```bash
# Run git-version inside the container
docker run --rm \
  -v $(pwd):/workspace -w /workspace \
  ghcr.io/synacker/git-version-utils:latest \
  git-version --safe-directory '*' --property env
```

### GitHub Actions — Job Outputs

Use `container:` to run the job inside the image, then parse `git-version --property env`
into `$GITHUB_OUTPUT`. Downstream jobs consume the values via `needs.set-version.outputs.*`.

```yaml
name: CI with job outputs

on:
  push:
    branches: [main, "release/*"]

jobs:
  set-version:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/synacker/git-version-utils:latest
      options: --workdir /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}
    outputs:
      BUILD_VERSION: ${{ steps.git_version.outputs.BUILD_VERSION }}
      BUILD_VERSION_MAJOR: ${{ steps.git_version.outputs.BUILD_VERSION_MAJOR }}
      BUILD_VERSION_MINOR: ${{ steps.git_version.outputs.BUILD_VERSION_MINOR }}
      BUILD_VERSION_PATCH: ${{ steps.git_version.outputs.BUILD_VERSION_PATCH }}
      BUILD_VERSION_BUILD: ${{ steps.git_version.outputs.BUILD_VERSION_BUILD }}
      BUILD_VERSION_TAG: ${{ steps.git_version.outputs.BUILD_VERSION_TAG }}
      BUILD_VERSION_FULL: ${{ steps.git_version.outputs.BUILD_VERSION_FULL }}
      BUILD_VERSION_EXTENDED: ${{ steps.git_version.outputs.BUILD_VERSION_EXTENDED }}
      BUILD_VERSION_SHORT: ${{ steps.git_version.outputs.BUILD_VERSION_SHORT }}
      BUILD_VERSION_COMMIT: ${{ steps.git_version.outputs.BUILD_VERSION_COMMIT }}
      BUILD_VERSION_BRANCH: ${{ steps.git_version.outputs.BUILD_VERSION_BRANCH }}
      BUILD_VERSION_DEFAULT_BRANCH: ${{ steps.git_version.outputs.BUILD_VERSION_DEFAULT_BRANCH }}
      BUILD_VERSION_RELEASE_BRANCHES: ${{ steps.git_version.outputs.BUILD_VERSION_RELEASE_BRANCHES }}

    steps:
      - uses: actions/checkout@v6.0.3
        with:
          fetch-depth: 0

      - name: Extract version info
        id: git_version
        run: |
          while IFS='=' read -r key value; do
            echo "$key=$value" >> "$GITHUB_OUTPUT"
          done < <(git-version --property env)

  build:
    runs-on: ubuntu-latest
    needs: set-version
    steps:
      - uses: actions/checkout@v6.0.3

      - name: Use version info
        run: |
          echo "Building version: ${{ needs.set-version.outputs.BUILD_VERSION }}"
          echo "Tag: ${{ needs.set-version.outputs.BUILD_VERSION_TAG }}"
```

### GitHub Actions — Env File Artifact

A simpler approach: write the version info to a file and share it as an artifact.

```yaml
name: CI with env file

on:
  push:
    branches: [main, "release/*"]

jobs:
  set-version:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/synacker/git-version-utils:latest
      options: --workdir /__w/${{ github.event.repository.name }}/${{ github.event.repository.name }}
    steps:
      - uses: actions/checkout@v6.0.3
        with:
          fetch-depth: 0

      - name: Generate version.env
        run: git-version --property env > version.env

      - name: Upload version env file
        uses: actions/upload-artifact@v4
        with:
          name: version-env
          path: version.env

  build:
    runs-on: ubuntu-latest
    needs: set-version
    steps:
      - uses: actions/checkout@v6.0.3

      - name: Download version env file
        uses: actions/download-artifact@v4
        with:
          name: version-env

      - name: Load version and use it
        run: |
          source version.env
          echo "Building version: $BUILD_VERSION"
          echo "Tag: $BUILD_VERSION_TAG"
```

### GitLab CI

Use the image directly and share version info via
[dotenv artifacts](https://docs.gitlab.com/ee/ci/yaml/artifacts_reports.html#artifactsreportsdotenv).

```yaml
stages:
  - set-version
  - build

set-version:
  stage: set-version
  image: ghcr.io/synacker/git-version-utils:latest
  variables:
    GIT_DEPTH: 0
  script:
    - git-version --property env > version.env
  artifacts:
    reports:
      dotenv: version.env

build:
  stage: build
  image: python:3.13-slim
  needs:
    - job: set-version
      artifacts: true
  script:
    - echo "Building version: $BUILD_VERSION"
    - echo "Tag: $BUILD_VERSION_TAG"

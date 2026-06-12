# syntax=docker/dockerfile:1
#
# git-version-utils Docker image
#
# Provides a lightweight container with git-version-utils pre-installed
# for use in CI pipelines (GitHub Actions, GitLab CI, etc.).
#
# Build:
#   # From local source:
#   docker build -t ghcr.io/synacker/git-version-utils:latest .
#
#   # From pre-built wheel (used in CI after package build):
#   docker build -t ghcr.io/synacker/git-version-utils:latest \
#     --build-arg WHEEL=dist/git_version_utils-*.whl .
#
# Usage:
#   docker run --rm -v $(pwd):/workspace -w /workspace \
#     ghcr.io/synacker/git-version-utils:latest \
#     git-version --safe-directory '*' --property env

# ============================================================
# Stage 1: Builder -- install the package
# ============================================================
FROM python:3.13-alpine AS builder

RUN apk add --no-cache git

ARG WHEEL
COPY . /build/

# Install from wheel if provided, otherwise from local source
RUN if [ -n "$WHEEL" ]; then \
        wheel_path=$(ls /build/$WHEEL 2>/dev/null | head -1) && \
        pip install --no-cache-dir "$wheel_path"; \
    else \
        pip install --no-cache-dir /build; \
    fi

# Record the installed version for labelling the runtime image
RUN python -c "from git_version import __version__; print(__version__)" > /version.txt

# ============================================================
# Stage 2: Runtime -- minimal image with git + the package
# ============================================================
FROM python:3.13-alpine AS runtime

# git is required -- git-version-utils calls the git CLI via subprocess
RUN apk add --no-cache git

# Copy only the git_version package (not the entire site-packages with pip/setuptools)
COPY --from=builder /usr/local/lib/python3.13/site-packages/git_version /usr/local/lib/python3.13/site-packages/git_version
COPY --from=builder /usr/local/lib/python3.13/site-packages/git_version_utils-*.dist-info /usr/local/lib/python3.13/site-packages/

# Copy the git-version entrypoint script
COPY --from=builder /usr/local/bin/git-version /usr/local/bin/git-version

# Copy version label
COPY --from=builder /version.txt /version.txt
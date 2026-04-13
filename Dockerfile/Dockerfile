# syntax=docker/dockerfile:1
# =============================================================================
# CStyleCheck — Embedded C Style Compliance Checker
# =============================================================================
#
# Usage (mount your project at /repo):
#
#   docker run --rm \
#     -v "$(pwd):/repo" \
#     ghcr.io/<org>/cnamecheck:latest \
#     --config /app/naming_convention.yaml \
#     /repo/source/**/*.c /repo/source/**/*.h
#
# Override dictionary files at runtime:
#   docker run --rm -v "$(pwd):/repo" ghcr.io/<org>/cnamecheck:latest \
#     --keywords-file /repo/my_keywords.txt \
#     --stdlib-file   /repo/my_stdlib.txt   \
#     --spell-dict    /repo/my_words.txt     \
#     /repo/source/**/*.c
#
# The image ships with default dictionaries at /app/.
# Pass --github-actions to emit inline PR annotations inside GitHub Actions.
# =============================================================================

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

LABEL org.opencontainers.image.title="CStyleCheck"
LABEL org.opencontainers.image.description="Embedded C Style Compliance Checker (Barr-C / MISRA-C complementary)"
LABEL org.opencontainers.image.source="https://github.com/${GITHUB_REPOSITORY:-org/cnamecheck}"
LABEL org.opencontainers.image.licenses="MIT"

# ── System setup ──────────────────────────────────────────────────────────────
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
RUN pip install --no-cache-dir pyyaml==6.*

# ── Application files ──────────────────────────────────────────────────────────
WORKDIR /app

# Core checker and configuration
COPY src/cnamecheck.py          ./
COPY src/naming_convention.yaml ./
COPY src/_version.py            ./
COPY src/cnamecheck.options     ./
COPY src/aliases.txt            ./
COPY src/exclusions.yml         ./
COPY src/project.defines        ./

# Dictionary files (can be overridden at runtime with CLI flags)
COPY src/c_keywords.txt         ./
COPY src/c_stdlib_names.txt     ./
COPY src/c_spell_dict.txt       ./

ENTRYPOINT ["python", "/app/cnamecheck.py"]
CMD ["--help"]

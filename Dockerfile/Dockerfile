# syntax=docker/dockerfile:1
# =============================================================================
# CStyleCheck — Embedded C naming-convention linter
# =============================================================================
#
# Usage (mount your project at /repo):
#
#   docker run --rm \
#     -v "$(pwd):/repo" \
#     ghcr.io/<org>/cstylecheck:latest \
#     --config /app/rules.yml \
#     /repo/source/**/*.c /repo/source/**/*.h
#
# Override dictionary files at runtime:
#   docker run --rm -v "$(pwd):/repo" ghcr.io/<org>/cstylecheck:latest \
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
LABEL org.opencontainers.image.description="Embedded C naming-convention linter (Barr-C / MISRA-C complementary)"
LABEL org.opencontainers.image.source="https://github.com/${GITHUB_REPOSITORY:-org/cstylecheck}"
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
COPY src/cstylecheck.py          ./
COPY src/rules.yml ./
COPY src/_version.py            ./
COPY src/options.txt     ./
COPY src/aliases.txt            ./
COPY src/exclusions.yml         ./
COPY src/defines.txt        ./

# Dictionary files (can be overridden at runtime with CLI flags)
COPY src/c_keywords.txt         ./
COPY src/c_stdlib_names.txt     ./
COPY src/c_spell_dict.txt       ./

ENTRYPOINT ["python", "/app/cstylecheck.py"]
CMD ["--help"]

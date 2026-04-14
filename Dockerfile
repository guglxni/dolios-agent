# Dolios Agent — Extended NemoClaw + Hermes Agent Container
#
# Multi-stage build:
# 1. Builder: install Python deps with uv
# 2. Runtime: sandbox-ready image with Hermes Agent + Dolios orchestrator
#
# Security model (mirrors NemoClaw):
# - Immutable: /opt/dolios (code), /sandbox/.dolios (config)
# - Writable: /sandbox/workspace, /sandbox/skills, /sandbox/memory, /tmp
# - sandbox:sandbox user, Landlock + seccomp via OpenShell

# --- Builder stage ---
# Pin base images by digest for supply chain integrity (OWASP A03:2025)
FROM python:3.12-slim@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4 AS builder

# Pin uv by version (update digest periodically)
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first for layer caching
COPY pyproject.toml README.md ./
RUN uv sync --frozen --no-install-project --compile-bytecode 2>/dev/null || uv sync --no-install-project --compile-bytecode

# Copy Dolios source
COPY dolios/ dolios/
COPY environments/ environments/
COPY evolution/ evolution/
RUN uv sync --compile-bytecode 2>/dev/null || uv sync --compile-bytecode

# --- Runtime stage ---
FROM python:3.12-slim@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4 AS runtime

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create sandbox user (NemoClaw convention)
RUN groupadd -r sandbox && useradd -r -g sandbox -d /sandbox -s /bin/bash sandbox

# Create directory structure
# Writable state directories
RUN mkdir -p \
    /sandbox/workspace \
    /sandbox/skills \
    /sandbox/memory \
    /sandbox/memory/traces \
    /tmp/dolios \
    /sandbox/.dolios-data

# Immutable config directories
RUN mkdir -p \
    /sandbox/.dolios \
    /sandbox/dolios/brand \
    /sandbox/dolios/policies

# Symlink writable state from immutable config (NemoClaw pattern)
RUN ln -s /sandbox/.dolios-data /sandbox/.dolios/data

# Copy built Python environment from builder
COPY --from=builder /build/.venv /opt/dolios/.venv
ENV PATH="/opt/dolios/.venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/dolios/.venv" \
    PYTHONUNBUFFERED=1

# Copy Dolios source
COPY dolios/ /opt/dolios/dolios/
COPY environments/ /opt/dolios/environments/
COPY evolution/ /opt/dolios/evolution/

# Copy brand assets (read-only at runtime)
COPY brand/ /sandbox/dolios/brand/
COPY dolios-blueprint/policies/ /sandbox/dolios/policies/
COPY CLAUDE.md AGENTS.md /sandbox/dolios/

# Copy skills (writable — evolvable)
COPY skills/ /sandbox/skills/

# Copy vendor repos
COPY vendor/hermes-agent/ /opt/dolios/vendor/hermes-agent/
COPY vendor/nemoclaw/nemoclaw-blueprint/ /opt/dolios/vendor/nemoclaw-blueprint/
COPY vendor/hermes-agent-self-evolution/ /opt/dolios/vendor/hermes-agent-self-evolution/

# Copy blueprint
COPY dolios-blueprint/ /opt/dolios/dolios-blueprint/

# Add vendor to PYTHONPATH
ENV PYTHONPATH="/opt/dolios:/opt/dolios/vendor/hermes-agent:/opt/dolios/vendor/hermes-agent-self-evolution:${PYTHONPATH}"

# Install Hermes Agent dependencies — fail-closed on integrity check
# (OWASP A03:2025 — SEC-A03-H1: no unhashed fallback)
COPY vendor/hermes-agent/requirements.txt /tmp/hermes-requirements.txt
RUN pip install --no-cache-dir -r /tmp/hermes-requirements.txt && \
    rm /tmp/hermes-requirements.txt

# Set ownership
RUN chown -R sandbox:sandbox /sandbox /tmp/dolios

# Lock immutable directories (Landlock + DAC)
RUN chown -R root:root /sandbox/dolios/brand /sandbox/dolios/policies /sandbox/.dolios && \
    chmod -R 444 /sandbox/dolios/brand && \
    chmod -R 444 /sandbox/dolios/policies

# Build args
ARG DOLIOS_BUILD_ID=dev
ENV DOLIOS_BUILD_ID=${DOLIOS_BUILD_ID}

# Generate per-build auth token for sandbox authentication
RUN python3 -c "import secrets; open('/sandbox/.dolios/auth_token','w').write(secrets.token_hex(32))" \
    && chmod 400 /sandbox/.dolios/auth_token

WORKDIR /sandbox/workspace
USER sandbox

ENTRYPOINT ["dolios"]
CMD ["start"]

EXPOSE 8080 18789

LABEL org.opencontainers.image.title="Dolios Agent" \
      org.opencontainers.image.description="The Crafty Agent — self-improving, sandboxed AI" \
      org.opencontainers.image.licenses="MIT AND Apache-2.0"

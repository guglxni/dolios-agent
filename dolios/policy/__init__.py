"""Dolios policy engine — native Python implementation of the NemoClaw policy contract.

Public API:
    PolicyEngine       — main class: generate, check, approve
    is_endpoint_allowed — pure function: check host:port against a policy dict
    match_endpoint     — pure function: check one endpoint definition
    match_host         — pure function: host pattern matching
    validate_ssrf      — pure function: SSRF URL validation
    load_base_policy   — loader: vendor openclaw-sandbox.yaml
    load_preset        — loader: single vendor preset by name
    load_tier_definitions — loader: vendor tiers.yaml
"""

from dolios.policy.engine import PolicyEngine
from dolios.policy.matcher import (
    is_endpoint_allowed,
    match_endpoint,
    match_host,
    validate_ssrf,
)
from dolios.policy.presets import (
    load_base_policy,
    load_preset,
    load_tier_definitions,
)

__all__ = [
    "PolicyEngine",
    "is_endpoint_allowed",
    "match_endpoint",
    "match_host",
    "validate_ssrf",
    "load_base_policy",
    "load_preset",
    "load_tier_definitions",
]

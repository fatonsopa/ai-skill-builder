"""Host-native defaults; no provider inferred from credentials or file paths."""
from .common import Invalid

PLATFORMS = ["chatgpt", "claude", "codex", "claude-code"]
POLICY = {
    "schema_version": 1,
    "designed_hosts": PLATFORMS,
    "default_ai_route": "current_host_model",
    "external_cli_required": False,
    "execution_requirements": ["Python 3", "file access", "declared dependencies"],
    "tested_host_activation": [],
    "budget_policy": "Routine testing includes bounded retries without repeated approval; preserve criteria and attempts, honor explicit hard limits, and stop on stalled progress or retry ceilings.",
}


def route(context=None, provider="host", model=None):
    context = context or {"platform": "unknown", "model": None}
    platform = context["platform"]
    if provider == "host":
        return {
            "route": "host_agent", "platform": platform,
            "model": context.get("model") or "current_host_model",
            "model_identity_source": "host_reported" if context.get("model") else "not_exposed",
            "requires_external_cli": False,
        }
    if context.get("external_cli") is False:
        raise Invalid("This host has no declared external CLI capability; use its native model handoff.")
    family = {"chatgpt": "codex", "codex": "codex", "claude": "claude", "claude-code": "claude"}.get(platform)
    if family and provider != family and not context.get("allow_cross_provider", False):
        raise Invalid("Cross-provider evaluation needs an explicit configured choice; keep the host-native default.")
    if not model:
        raise Invalid("An external model invocation needs an explicit model identifier.")
    return {"route": provider, "platform": platform, "model": model, "requires_external_cli": True}

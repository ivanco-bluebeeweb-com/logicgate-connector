"""LogicGate Connector extension declaration.

LogicGate (Risk Cloud) is a no-code GRC platform built on a configurable
Application/Record/Field model, exposed through a Public API
(api.logicgate.com) via a static Bearer API Token.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "logicgate-connector",
    version="0.1.0",
    display_name="LogicGate",
    description=(
        "Connect your own LogicGate (Risk Cloud) account (static API Token) "
        "to discover your configured Applications (Risk Register, Vendor "
        "Assessments, Incident Management, etc.), browse and manage Records "
        "inside each, and get a lightweight risk posture overview."
    ),
    icon="icon.svg",
    capabilities=["logicgate:read", "logicgate:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="logicgate",
    description=(
        "LogicGate Connector — manage Applications, Fields and Records on a "
        "LogicGate Risk Cloud account."
    ),
)

ext.secret(
    "logicgate_connections",
    "JSON list of connected LogicGate accounts and encrypted API Tokens. Managed only through connect_logicgate and disconnect_logicgate.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one LogicGate account connection is saved."""
    import json

    raw = await ctx.secrets.get("logicgate_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    return {
        "healthy": True,
        "connections": len(connections),
    }

"""LogicGate Connector panels.

Same conventions as Vanta/Drata panels.py: no Cards in the left sidebar,
disconnect only in App settings, every input has its own visible label,
placeholders are contextually specific, the connect form stretches to the
sidebar's full width with contents stretched to fill it, and the sidebar
carries no instructions duplicated from the "How do I get this?" modal.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="Settings", on_click=ui.Call("__panel__logicgate_settings"),
    )


@ext.panel("logicgate_sidebar", slot="left", title="LogicGate")
async def logicgate_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("How do I get this?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__logicgate_connect_help")),
            ui.Form(action="connect_logicgate", submit_label="Connect", children=[
                _field("Account label", ui.Input(param_name="label", placeholder="Acme Corp — Production")),
                _field("API Token", ui.Input(param_name="api_token", placeholder="LogicGate Admin > API Tokens")),
                _field("Base URL (optional)", ui.Input(param_name="base_url", placeholder="https://api.logicgate.com")),
            ]),
        ])
    label = connections[0].get("label") or "LogicGate account"
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text(label, variant="body"),
        ui.Divider(),
        ui.Button("Applications", variant="ghost", full_width=True,
                  on_click=ui.Call("__panel__logicgate_applications")),
        ui.Button("Risk posture overview", variant="ghost", full_width=True,
                  on_click=ui.Call("__panel__logicgate_overview")),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("logicgate_connect_help", slot="center", title="How do I get this?", center_overlay=True)
async def logicgate_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Connecting LogicGate", level=2),
        ui.Text("1. In LogicGate, go to Admin > API Tokens.", variant="body"),
        ui.Text("2. Create a new API Token — access is limited to whatever Applications and permissions you grant it there.", variant="body"),
        ui.Text("3. Paste the token into the form on the left. Only change the Base URL if your organization uses a non-default LogicGate instance.", variant="body"),
    ])

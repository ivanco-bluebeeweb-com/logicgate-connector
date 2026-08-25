"""LogicGate Connector -- center panels for Applications/Records/Overview."""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


@ext.panel("logicgate_overview", slot="center", title="Risk posture overview", center_overlay=True)
async def logicgate_overview(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    from schemas import AuditRiskPostureParams
    result = await h.audit_risk_posture(ctx, AuditRiskPostureParams(connection_id=connections[0].get("id", "")))
    if not result.success:
        return ui.Alert(type="error", message=f"Could not load risk posture: {result.error}")
    d = result.data
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Risk posture overview", level=2),
        ui.Stack(direction="h", gap=4, align="stretch", children=[
            ui.Stat(label="Applications configured", value=str(d.application_count)),
            ui.Stat(label="Records sampled", value=str(d.records_sampled)),
        ]),
        ui.Text(d.applications_summary, variant="caption"),
    ])


@ext.panel("logicgate_applications", slot="center", title="Applications", center_overlay=True)
async def logicgate_applications(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Layers")
    from schemas import ListApplicationsParams
    result = await h.list_applications(ctx, ListApplicationsParams(connection_id=connections[0].get("id", "")))
    if not result.success:
        return ui.Alert(type="error", message=f"Could not load Applications: {result.error}")
    apps = result.data.applications
    if not apps:
        return ui.Empty(message="No Applications configured on this LogicGate account yet.", icon="Layers")
    rows = [{"Name": a.name, "Description": a.description or "—", "ID": a.application_id} for a in apps]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Applications", level=2),
        ui.DataTable(rows=rows, columns=["Name", "Description", "ID"]),
    ])


@ext.panel("logicgate_records", slot="center", title="Records", center_overlay=True)
async def logicgate_records(ctx, application_id: str = "", **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="FileText")
    if not application_id:
        return ui.Empty(message="Open an Application from the Applications list to see its Records.", icon="FileText")
    from schemas import ListRecordsParams
    result = await h.list_records(ctx, ListRecordsParams(connection_id=connections[0].get("id", ""), application_id=application_id))
    if not result.success:
        return ui.Alert(type="error", message=f"Could not load Records: {result.error}")
    records = result.data.records
    if not records:
        return ui.Empty(message="No Records in this Application yet.", icon="FileText")
    rows = [{"Name": r.name or "—", "Stage": r.stage or "—", "ID": r.record_id} for r in records]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Records", level=2),
        ui.DataTable(rows=rows, columns=["Name", "Stage", "ID"]),
    ])

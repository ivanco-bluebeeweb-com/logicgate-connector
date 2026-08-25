"""Chat functions for LogicGate Connector (LogicGate Public API)."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import logicgate_client as lg
from app import chat
from schemas import (
    ApplicationIdParams, ApplicationList, AuditRiskPostureParams,
    ConnectLogicGateParams, ConnectionList, ConnectionRefParams,
    CreateRecordParams, DeleteResult, DisconnectLogicGateParams, FieldList,
    ListApplicationsParams, ListFieldsParams, ListRecordsParams,
    LogicGateApplication, LogicGateConnection, LogicGateField, LogicGateRecord,
    NoParams, RecordIdParams, RecordList, RiskPostureAudit, UpdateRecordParams,
)

_SECRET_NAME = "logicgate_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> LogicGateConnection:
    return LogicGateConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or "LogicGate account",
        base_url=c.get("base_url", "") or "https://api.logicgate.com",
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise lg.LogicGateError("No LogicGate account connected yet. Use connect_logicgate first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise lg.LogicGateError(f"No connection found with id '{connection_id}'.")
    return connections[0]


def _client_for(c: dict) -> lg.LogicGateClient:
    return lg.LogicGateClient(api_token=c.get("api_token", ""), base_url=c.get("base_url", ""))


def _unwrap(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "content", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


@chat.function("connect_logicgate", "Connect a LogicGate (Risk Cloud) account via a static API Token, after verifying connectivity.", action_type="write", chain_callable=True, data_model=LogicGateConnection, event="logicgate-connector.connect_logicgate", effects=["logicgate.provider.connected"])
async def connect_logicgate(ctx, params: ConnectLogicGateParams) -> ActionResult:
    """Connect a LogicGate (Risk Cloud) account via a static API Token, after verifying connectivity."""
    client = lg.LogicGateClient(api_token=params.api_token, base_url=params.base_url)
    try:
        await client.request("GET", "/applications", params={"page": 1, "size": 1})
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    connections = await _load_connections(ctx)
    new_id = str(uuid.uuid4())
    record = {
        "id": new_id,
        "label": params.label or "LogicGate account",
        "api_token": params.api_token,
        "base_url": params.base_url,
    }
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(data=_connection_entity(record))


@chat.function("disconnect_logicgate", "Disconnect a LogicGate account: deletes only the saved credentials. Nothing in LogicGate itself is changed.", action_type="write", chain_callable=True, data_model=DeleteResult, event="logicgate-connector.disconnect_logicgate", effects=["logicgate.provider.disconnected"])
async def disconnect_logicgate(ctx, params: DisconnectLogicGateParams) -> ActionResult:
    """Disconnect a LogicGate account: deletes only the saved credentials. Nothing in LogicGate itself is changed."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No connection found with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data=DeleteResult(deleted=True, connection_id=params.connection_id))


@chat.function("list_connections", "List the connected LogicGate accounts.", action_type="read", chain_callable=True, data_model=ConnectionList, event="logicgate-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List the connected LogicGate accounts."""
    connections = await _load_connections(ctx)
    return ActionResult.success(data=ConnectionList(connections=[_connection_entity(c) for c in connections]))


# ---- Applications ----

def _application_entity(a: dict) -> LogicGateApplication:
    return LogicGateApplication(
        application_id=str(a.get("id", "")),
        name=a.get("name", ""),
        description=a.get("description", ""),
    )


@chat.function("list_applications", "List Applications (customer-defined data models, e.g. Risk Register, Vendor Assessments) configured on the connected LogicGate account.", action_type="read", chain_callable=True, data_model=ApplicationList, event="logicgate-connector.list_applications")
async def list_applications(ctx, params: ListApplicationsParams) -> ActionResult:
    """List Applications (customer-defined data models, e.g. Risk Register, Vendor Assessments) configured on the connected LogicGate account."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/applications")
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = _unwrap(data)
    return ActionResult.success(data=ApplicationList(applications=[_application_entity(a) for a in items]))


@chat.function("get_application", "Read one Application in full by id.", action_type="read", chain_callable=True, data_model=LogicGateApplication, event="logicgate-connector.get_application")
async def get_application(ctx, params: ApplicationIdParams) -> ActionResult:
    """Read one Application in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/applications/{params.application_id}")
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_application_entity(data or {}))


# ---- Fields ----

def _field_entity(f: dict) -> LogicGateField:
    return LogicGateField(
        field_id=str(f.get("id", "")),
        name=f.get("name", ""),
        field_type=f.get("type", f.get("fieldType", "")),
    )


@chat.function("list_fields", "List the Field schema (name, type, options) of one Application, before creating or updating Records in it.", action_type="read", chain_callable=True, data_model=FieldList, event="logicgate-connector.list_fields")
async def list_fields(ctx, params: ListFieldsParams) -> ActionResult:
    """List the Field schema (name, type, options) of one Application, before creating or updating Records in it."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/applications/{params.application_id}/fields")
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = _unwrap(data)
    return ActionResult.success(data=FieldList(fields=[_field_entity(f) for f in items]))


# ---- Records ----

def _record_entity(application_id: str, r: dict) -> LogicGateRecord:
    return LogicGateRecord(
        record_id=str(r.get("id", "")),
        application_id=application_id,
        name=r.get("name", r.get("label", "")),
        stage=r.get("stage", r.get("status", "")),
        field_values=r.get("fieldValues", r.get("fields", {})) or {},
    )


@chat.function("list_records", "List Records inside one Application, optionally paginated.", action_type="read", chain_callable=True, data_model=RecordList, event="logicgate-connector.list_records")
async def list_records(ctx, params: ListRecordsParams) -> ActionResult:
    """List Records inside one Application, optionally paginated."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query = {"page": params.page, "size": params.limit}
    try:
        data, _ = await client.request("GET", f"/applications/{params.application_id}/records", params=query)
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = _unwrap(data)
    return ActionResult.success(data=RecordList(records=[_record_entity(params.application_id, r) for r in items]))


@chat.function("get_record", "Read one Record in full, including all of its field values.", action_type="read", chain_callable=True, data_model=LogicGateRecord, event="logicgate-connector.get_record")
async def get_record(ctx, params: RecordIdParams) -> ActionResult:
    """Read one Record in full, including all of its field values."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/applications/{params.application_id}/records/{params.record_id}")
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_record_entity(params.application_id, data or {}))


@chat.function("create_record", "Create a new Record inside an Application, using exact field name/id keys from list_fields.", action_type="write", chain_callable=True, data_model=LogicGateRecord, event="logicgate-connector.create_record", effects=["logicgate.record.created"])
async def create_record(ctx, params: CreateRecordParams) -> ActionResult:
    """Create a new Record inside an Application, using exact field name/id keys from list_fields."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request(
            "POST", f"/applications/{params.application_id}/records",
            json_body={"fieldValues": params.field_values},
        )
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_record_entity(params.application_id, data or {}))


@chat.function("update_record", "Update selected field values of an existing Record. Only given fields change.", action_type="write", chain_callable=True, data_model=LogicGateRecord, event="logicgate-connector.update_record", effects=["logicgate.record.updated"])
async def update_record(ctx, params: UpdateRecordParams) -> ActionResult:
    """Update selected field values of an existing Record. Only given fields change."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request(
            "PATCH", f"/applications/{params.application_id}/records/{params.record_id}",
            json_body={"fieldValues": params.field_values},
        )
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_record_entity(params.application_id, data or {}))


# ---- Aggregated audit ----

@chat.function("audit_risk_posture", "Build a lightweight risk posture overview: how many Applications are configured and a sample of their Record counts.", action_type="read", chain_callable=True, data_model=RiskPostureAudit, event="logicgate-connector.audit_risk_posture")
async def audit_risk_posture(ctx, params: AuditRiskPostureParams) -> ActionResult:
    """Build a lightweight risk posture overview: how many Applications are configured and a sample of their Record counts."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        apps_data, _ = await client.request("GET", "/applications")
    except lg.LogicGateError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    apps = _unwrap(apps_data)
    records_sampled = 0
    summary_parts = []
    for a in apps[:10]:
        app_id = str(a.get("id", ""))
        name = a.get("name", "")
        try:
            recs_data, _ = await client.request("GET", f"/applications/{app_id}/records", params={"page": 1, "size": 1})
            recs = _unwrap(recs_data)
            records_sampled += len(recs)
            summary_parts.append(f"{name}: sampled")
        except lg.LogicGateError:
            summary_parts.append(f"{name}: unavailable")
    return ActionResult.success(data=RiskPostureAudit(
        application_count=len(apps),
        records_sampled=records_sampled,
        applications_summary="; ".join(summary_parts) if summary_parts else "No applications configured.",
    ))

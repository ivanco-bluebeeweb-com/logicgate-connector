"""Pydantic input contracts and SDL result entities for LogicGate Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved LogicGate account connection ID. Omit to use the first connected account.")


class ConnectLogicGateParams(BaseModel):
    label: str = Field("", description="Friendly account label, e.g. 'Acme Corp — Production'.")
    api_token: str = Field(..., description="LogicGate API Token, from Admin > API Tokens.")
    base_url: str = Field("", description="Optional API base URL override. Defaults to https://api.logicgate.com.")


class DisconnectLogicGateParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved LogicGate account connection ID to remove from Imperal.")


class ListApplicationsParams(ConnectionRefParams):
    pass


class ApplicationIdParams(ConnectionRefParams):
    application_id: str = Field(..., description="LogicGate Application ID.")


class ListFieldsParams(ConnectionRefParams):
    application_id: str = Field(..., description="LogicGate Application ID to list Fields for.")


class ListRecordsParams(ConnectionRefParams):
    application_id: str = Field(..., description="LogicGate Application ID to list Records from.")
    page: int = Field(1, description="Page number, 1-based.")
    limit: int = Field(50, description="Max records to return per page (1-200).")


class RecordIdParams(ConnectionRefParams):
    application_id: str = Field(..., description="LogicGate Application ID the record belongs to.")
    record_id: str = Field(..., description="LogicGate Record ID.")


class CreateRecordParams(ConnectionRefParams):
    application_id: str = Field(..., description="LogicGate Application ID to create the record in.")
    field_values: dict = Field(..., description="Map of field name/id to value, matching the Application's own Field schema (see list_fields).")


class UpdateRecordParams(RecordIdParams):
    field_values: dict = Field(..., description="Map of field name/id to new value. Only given fields change.")


class AuditRiskPostureParams(ConnectionRefParams):
    pass


# ---- SDL entities ----

class LogicGateConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    connection_id: str
    label: str
    base_url: str


class ConnectionList(sdl.Entity):
    id: str = ""
    title: str = ""
    connections: list[LogicGateConnection]


class LogicGateApplication(sdl.Entity):
    id: str = ""
    title: str = ""
    application_id: str
    name: str
    description: str = ""


class ApplicationList(sdl.Entity):
    id: str = ""
    title: str = ""
    applications: list[LogicGateApplication]


class LogicGateField(sdl.Entity):
    id: str = ""
    title: str = ""
    field_id: str
    name: str
    field_type: str = ""


class FieldList(sdl.Entity):
    id: str = ""
    title: str = ""
    fields: list[LogicGateField]


class LogicGateRecord(sdl.Entity):
    id: str = ""
    title: str = ""
    record_id: str
    application_id: str
    name: str = ""
    stage: str = ""
    field_values: dict = {}


class RecordList(sdl.Entity):
    id: str = ""
    title: str = ""
    records: list[LogicGateRecord]


class RiskPostureAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    application_count: int
    records_sampled: int
    applications_summary: str


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    deleted: bool
    connection_id: str

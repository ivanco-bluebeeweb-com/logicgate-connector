# LogicGate Connector — Preparation

**Prepared:** 2026-08-25
**Scope:** Maximum practical functionality against LogicGate's generic
Application/Record/Field model, per the user's standing "maximum functionality"
instruction for every new app.

## 1. Product outcome

LogicGate Connector lets an authorized Imperal user connect one or more LogicGate
(Risk Cloud) accounts (BYOK static API Token), discover their own configured
Applications (Risk Register, Vendor Assessments, Incident Management, etc.),
browse and manage Records inside each, and get a lightweight aggregated risk
posture report. LogicGate remains the system of record.

## 2. Connection architecture

- **Model:** BYOK, per Imperal account, multi-connection JSON secret
  (`logicgate_connections`).
- **Secret shape:** each record = `{connection_id, label, api_token, base_url}`
  (base_url defaults to `https://api.logicgate.com`).
- **Auth:** static Bearer token on every request — no exchange/refresh step.
- **No secret echo:** api_token is never returned in entities, labels, errors,
  panels, or logs.
- **Verification:** `connect_logicgate` performs a bounded single-page call
  (list Applications) before persisting the connection.

## 3. Provider client

`logicgate_client.py` is the single HTTP boundary. It:

1. holds no long-lived state beyond the token/base_url passed at construction;
2. builds Bearer authorization headers;
3. maps status codes into safe, user-facing structured errors (`LogicGateError`),
   marking 429/5xx as retryable;
4. never logs or raises the raw token in any exception message;
5. tolerantly unwraps both `{"data": [...], ...}` and bare-list responses, since
   the generic Application/Record model may vary in envelope shape across
   endpoints.

## 4. Generic entity model (no hardcoded Risk/Control types)

Because LogicGate has no fixed platform-level Risk/Control resource, every
Record-facing function takes an explicit `application_id` and returns/accepts a
free-form `fields: dict[str, Any]` payload, mirroring the Application's own
Field schema (discoverable via `list_fields`). This is architecturally different
from Vanta/Drata and mirrors the same generic pattern used elsewhere in the
portfolio for configurable-schema platforms (e.g. HubSpot's custom objects,
ServiceNow's generic table passthrough).

## 5. Error handling

- 401/403 → "Your API Token doesn't have access to this. Check Admin > API
  Tokens in LogicGate and verify scope/permissions."
- 404 → "Application/Record not found — check the id."
- 429/5xx → retryable=True, generic backoff message.

## 6. Aggregated report

`audit_risk_posture` scans configured Applications and reports counts (number
of Applications, number of Records sampled) — a lighter-weight report than
Vanta/Drata's audits since LogicGate exposes no fixed "failing test" concept;
the value here is orientation (how many Applications, how many Records) rather
than a fixed compliance score.

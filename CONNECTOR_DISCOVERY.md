# LogicGate Connector — Discovery

**Prepared:** 2026-08-25
**Source:** LogicGate Public API (developer.logicgate.com), static Bearer API Token auth.

## 1. What LogicGate is

LogicGate (Risk Cloud) is a no-code GRC platform for risk management, IT risk,
vendor risk, compliance, and policy management. Unlike Vanta/Drata (which have a
fixed platform-level entity model: Tests/Monitors, Controls, Frameworks), LogicGate
is built on a configurable workflow engine: each customer defines their own
**Applications** (data models — e.g. "Risk Register", "Vendor Assessments",
"Incident Management") with their own **Fields**, and stores data as **Records**
inside each Application. Records move through workflow **Stages** (e.g.
Draft → Review → Approved → Closed).

## 2. Authentication

- **Static Bearer API Token.** Generated in LogicGate Admin > API Tokens.
- Sent as `Authorization: Bearer <token>` on every request — same static-token
  model as Drata (no OAuth exchange).
- Token scope/visibility is controlled entirely within LogicGate; the connector
  cannot request broader access than configured there.

## 3. Core architecture (generic, not fixed entities)

| Concept | Description | Ops |
|---|---|---|
| Applications | Customer-defined data models (e.g. Risk Register, Vendor Assessments) | list, get |
| Fields | The field schema of one Application (name, type, options) | list |
| Records | Individual entries inside an Application, with arbitrary field values | list, get, create, update |
| Record Stage / workflow state | Current workflow stage of a record (if exposed by the API) | reflected on the record entity |

Because there is no fixed "Risk"/"Control" resource at the platform level, the
connector must expose **generic** functions that operate on any Application by
id, rather than hardcoded Risk/Control/Vendor functions like Vanta/Drata's.

## 4. Pagination & rate limits

- Standard page/pageSize (or cursor) pagination assumed on list endpoints —
  confirmed against the same conservative pattern used for Vanta/Drata
  (`page`, `limit` query params), since exact API docs could not be independently
  browsed this session (web reader tooling unavailable). Kept generic/tolerant in
  the client: accepts both `{"data": [...]}` and bare list responses.
- Standard 429/5xx retryable-error handling, same posture as every other connector
  in the portfolio.

## 5. Domain-sensitivity note

Like Vanta/Drata, this is a compliance/risk-register domain: record labels,
stages, and risk scores must be reflected exactly as returned by LogicGate — no
softening, paraphrasing, or reclassification of risk data.

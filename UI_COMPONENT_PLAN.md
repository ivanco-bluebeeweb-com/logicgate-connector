# LogicGate Connector — UI Component Plan

Source: `UI_COMPONENT_VOCABULARY.md` + `~/UI_INTERFACE_STANDARD.md`. Only primitives
from the verified vocabulary are used below.

## Standing rules applied (binding for every screen in this plan)
- Every input carries its own visible label (via a `Text(variant="caption")` +
  input pair, never a bare placeholder).
- Placeholders are contextually specific to the exact field, never generic.
- The connect form container is stretched to the full width of the left sidebar;
  its own contents stretch to fill it (`align="stretch"`).
- The sidebar carries NO instructions duplicated from the "How do I get this?"
  modal.
- No `Card` (decorated box) anywhere in the left sidebar — plain `Stack` +
  `Divider` only.

## 1. Left sidebar (`slot="left"`)

**Not connected:**
- `Button` "How do I get this?" (ghost, opens `logicgate_connect_help` modal panel)
- `Form(action="connect_logicgate")`:
  - Label `Input` (placeholder: "Acme Corp — Production")
  - API Token `Input` (placeholder: "LogicGate Admin > API Tokens")
  - Base URL `Input` (placeholder: "https://api.logicgate.com", optional)
  - Submit button "Connect"

**Connected:**
- `Text` account label, `Divider`
- `Button` list (ghost, full width, left-aligned) opening each center panel:
  Applications, Risk posture overview
- `Divider`
- `Button` "App settings" (secondary, always last)

## 2. Center panels (`slot="center"`, `center_overlay=True`)

- `logicgate_overview` — `audit_risk_posture` result as `Stat` cards (Applications
  tracked, Records sampled).
- `logicgate_applications` — `DataTable` of Applications (name, id, record count if
  known) or `Empty`. Each row opens `logicgate_records` for that Application
  (passed via panel kwargs).
- `logicgate_records` — `DataTable` of Records for the selected Application
  (dynamic columns are impractical in a fixed DataTable, so show id, name/label
  if present, and a raw-fields JSON-as-text column) or `Empty`.

## 3. Settings panel (`panels_settings.py`)

- List of connected accounts with a "Disconnect" button per row (`ui.Button`
  variant="destructive"). No other settings needed for v1.

## 4. Modal help panel

- `logicgate_connect_help` — plain numbered steps: 1) Admin > API Tokens in
  LogicGate, 2) Create token, 3) Paste it into the form. Center-overlay panel,
  triggered only from the "How do I get this?" button (never duplicated in the
  sidebar itself).

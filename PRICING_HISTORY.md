# Pricing History — LogicGate Connector

## 2026-08-25 — initial pricing (build → deploy → save_pricing → submit_for_review)

Same pattern as Vanta/Drata/Ping Identity/Okta/MuleSoft this build cycle:
pricing set via `developer.save_pricing` BEFORE `submit_for_review`, per the
standing rule ("ты не выставила прайсинги на функции перед заливом на
платформу... это должно быть частью дефолтного поведения всегда для всех
приложений и для всех сессий").

`save_pricing` succeeded on the **first** call — `manifest_json` came back
populated with `pricing_model: "per_action"` and all 8 non-zero tool prices
present. No retry needed (like Drata, unlike Vanta/Okta/MuleSoft/Ping
Identity's #2260 mismatch).

**First deploy attempt was REJECTED (19/20 checks)** — `ui.Button(align="left",
...)` is not a valid kwarg for `ui.Button` (only `disabled`, `full_width`,
`icon`, `label`, `on_click`, `size`, `variant` are accepted — there is no
per-button text-alignment kwarg in the current DUI vocabulary; `full_width`
alone is sufficient for a left-aligned nav button). Fixed by dropping `align`
entirely. Re-validated 0 errors, redeployed clean (21/21 — no warnings at
all, unlike Vanta/Drata which both still lack `@ext.on_install`).

**Category note:** same as Vanta/Drata — `category="grc"` does not exist in
the platform's category catalog; filed under `productivity`.

**Architecture note:** LogicGate has no fixed platform-level Risk/Control
entity model — everything is generic Applications/Fields/Records, so the
function set (and its pricing) is deliberately generic rather than
domain-specific like Vanta/Drata's Monitors/Controls/Vendors.

**Prices — fixed platform scale {0, 8, 16, 20, 40, 60}, no exceptions, no
markup:**

| Цена | Функции |
|---|---|
| 0 | `connect_logicgate`, `disconnect_logicgate`, `list_connections` (настройка доступа, не операция с LogicGate API) |
| 8 | `list_applications`, `get_application`, `list_fields` (лёгкие read-операции метаданных) |
| 16 | `list_records`, `get_record` (детальные read-операции с данными) |
| 20 | `create_record`, `update_record` (операции записи) |
| 40 | `audit_risk_posture` (агрегированный отчёт, требует нескольких запросов) |

Итог: pricing_model = per_action, все цены сохранены и подтверждены через
`manifest_json` в ответе `save_pricing`.

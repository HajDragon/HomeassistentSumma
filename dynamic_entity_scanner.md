# dynamic_entity_scanner.py

Dynamically scans Home Assistant for entities from a specific integration (e.g. Withings) **without hardcoding any entity IDs**. Resilient to entity ID renames and devices that drop off temporarily.

---

## Requirements

- Python 3.10+
- `requests` library (`pip install requests`)
- A long-lived Home Assistant access token (already configured in the file)

---

## Three Strategies

### Strategy 1 — Python REST Scan

Uses `GET /api/states` to pull every entity, then filters locally in Python.

#### Function signature

```python
scan_entities_python(
    integration_prefix: str | None = None,
    device_class:       str | None = None,
    entity_regex:       str | None = None,
    domain:             str | None = None,
) -> list[dict]
```

#### Parameters

| Parameter | Type | Description | Example |
|---|---|---|---|
| `integration_prefix` | `str` | Matches entity names that start with this slug (part after the domain dot) | `"withings"` |
| `device_class` | `str` | Matches `attributes.device_class` exactly | `"battery"`, `"weight"` |
| `entity_regex` | `str` | Regex applied to `entity_id` (case-insensitive) | `r"weight\|bmi"` |
| `domain` | `str` | Restricts to one HA domain | `"sensor"`, `"binary_sensor"` |

All parameters are optional and combinable. **Dead states (`unavailable`, `unknown`, `none`, `""`) are always rejected before any further filter runs.**

#### Examples

```python
# All active Withings entities across any domain
scan_entities_python(integration_prefix="withings")

# Only Withings battery sensors that are active
scan_entities_python(integration_prefix="withings", device_class="battery")

# Any sensor (any integration) whose entity_id contains 'weight' or 'bmi'
scan_entities_python(domain="sensor", entity_regex=r"weight|bmi")
```

Each returned item is a raw HA state object with `entity_id`, `state`, and `attributes`.

---

### Strategy 2 — Jinja2 Templates

Four Jinja2 templates are defined as module-level strings and can be:
- **Pasted directly** into HA Developer Tools → Template tab, or
- **Rendered via REST** using `render_template(template_string)` which posts to `POST /api/template`.

#### Template overview

| Variable name | What it filters |
|---|---|
| `JINJA2_BY_INTEGRATION` | All active entities from `integration_entities('withings')` |
| `JINJA2_BY_DEVICE_CLASS` | Withings entities with `device_class == 'battery'` |
| `JINJA2_BY_REGEX` | Withings entities whose `entity_id` matches `'weight\|battery'` |
| `JINJA2_GENERIC_STATES_FILTER` | **All** sensors globally with `device_class == 'battery'` — no integration needed |

#### Key Jinja2 patterns used

```jinja2
{# Safest starting point — HA built-in for integration targeting #}
{{ integration_entities('withings') | select('has_value') | list }}
```

```jinja2
{# Filter by device_class inside integration scope #}
{% for e in integration_entities('withings') %}
  {% if states[e].attributes.get('device_class','') == 'battery'
        and states[e].state not in ['unavailable','unknown','none',''] %}
    {{ e }}
  {% endif %}
{% endfor %}
```

```jinja2
{# Regex match on entity_id — 'search' test is built into HA Jinja2 #}
{{ integration_entities('withings') | select('search', 'weight|battery') | select('has_value') | list }}
```

```jinja2
{# Global fallback — no integration slug required #}
{{ states.sensor
   | selectattr('attributes.device_class', 'eq', 'battery')
   | rejectattr('state', 'in', ['unavailable','unknown','none',''])
   | map(attribute='entity_id') | list }}
```

---

### Strategy 3 — YAML Automation Snippet

`YAML_AUTOMATION` (printed at runtime) is a complete, copy-paste-ready HA automation that:

- **Triggers** when any active Withings battery drops below 20 %
- **Checks** at least one Withings entity is available before acting
- **Notifies** with a dynamic message listing all low-battery device names and their current level
- Uses **zero hardcoded entity IDs** — survives integration reloads and entity renames

```yaml
trigger:
  - platform: template
    value_template: >
      {% set low = integration_entities('withings')
         | select('has_value')
         | selectattr('attributes.device_class', 'eq', 'battery')
         | map(attribute='state') | map('int', default=100)
         | select('lt', 20) | list %}
      {{ low | count > 0 }}
```

Paste the full snippet into **Settings → Automations → Create Automation → Edit in YAML**.

---

## Running the script

```bash
# Activate the project venv first
source .venv/Scripts/activate        # Windows / Git Bash
# or
.venv\Scripts\activate               # Windows cmd / PowerShell

python dynamic_entity_scanner.py
```

Output sections:

1. **Strategy 1** — tabular list of matched entities with state and device_class
2. **Strategy 2** — each Jinja2 template rendered live against your HA instance
3. **Strategy 3** — YAML automation block printed to stdout
4. **Developer Tools guide** — step-by-step testing instructions

---

## Testing templates in HA Developer Tools

1. Open Home Assistant in your browser.
2. Click the **Developer Tools** icon (`</>`) in the left sidebar.
3. Select the **Template** tab.
4. Paste any Jinja2 block from Strategy 2 into the left editor panel.
5. The right panel renders the output **live** against real entity data — no save required.
6. Syntax errors are highlighted immediately.

**Quick one-liner to explore any integration:**

```jinja2
{{ integration_entities('withings') | select('has_value') | list }}
```

Replace `'withings'` with any slug shown in **Settings → Devices & Services**.  
To discover all available sensors when you don't know the slug:

```jinja2
{{ states.sensor | map(attribute='entity_id') | list }}
```

---

## File structure reference

| File | Role |
|---|---|
| [dynamic_entity_scanner.py](dynamic_entity_scanner.py) | This script — dynamic entity discovery |
| [push_dashboard.py](push_dashboard.py) | Builds and pushes the Lovelace dashboard via WebSocket |
| [Webhook.py](Webhook.py) | Triggers HA webhook to fire a camera capture event |
| [connection check.py](connection%20check.py) | Heartbeat check — verifies HA API is reachable |
| [list_devices.py](list_devices.py) | Lists all HA entities grouped by domain |

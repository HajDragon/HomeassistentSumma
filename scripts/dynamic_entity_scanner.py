"""
dynamic_entity_scanner.py
─────────────────────────────────────────────────────────────────────────────
Dynamically scans Home Assistant for entities from a specific integration
(e.g. Withings) without relying on hardcoded entity IDs.

Three layered strategies are provided:
  1. Python (REST)  — query /api/states and filter locally
  2. Jinja2 template — paste directly into HA Developer Tools → Template
  3. YAML automation  — ready-to-use HA automation snippet (printed as text)

All filters honour the same rules:
  • Skip states: 'unavailable', 'unknown', 'none', ''
  • Optionally restrict by device_class  (e.g. 'battery', 'weight')
  • Optionally restrict by entity_id / friendly_name regex
─────────────────────────────────────────────────────────────────────────────
"""

import os
import re
import json
import sys
import requests
from typing import Optional
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  — shared with the rest of your project
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

_HA_BASE_URL = os.getenv("HA_BASE_URL", "http://homeassistant.local:8123").rstrip("/")
TOKEN        = os.getenv("HA_TOKEN")
if not TOKEN:
    sys.exit("Error: HA_TOKEN not set — copy .env.example to .env and fill in your token.")

WS_URL = _HA_BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# States that mean "this entity is not usable right now"
DEAD_STATES = {"unavailable", "unknown", "none", ""}


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 1 — Pure Python / REST API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_states() -> list[dict]:
    """Return every entity state object from /api/states."""
    resp = requests.get(f"{_HA_BASE_URL}/api/states", headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def scan_entities_python(
    integration_prefix: Optional[str] = None,
    device_class: Optional[str] = None,
    entity_regex: Optional[str] = None,
    domain: Optional[str] = None,
) -> list[dict]:
    """
    Dynamically return active entities without any hardcoded entity IDs.

    Parameters
    ----------
    integration_prefix : str, optional
        Slug used at the start of entity IDs by this integration.
        For Withings, pass 'withings'.  Matches both 'sensor.withings_*'
        and 'binary_sensor.withings_*' etc.
    device_class : str, optional
        HA device_class attribute value, e.g. 'battery', 'weight',
        'temperature', 'humidity'.
    entity_regex : str, optional
        Regex applied to entity_id (case-insensitive).  Example:
        r'battery|weight'  matches any entity whose ID contains those words.
    domain : str, optional
        Restrict to a single HA domain, e.g. 'sensor', 'binary_sensor'.

    Returns
    -------
    list[dict]  — filtered, active entity state objects
    """
    all_states = fetch_all_states()
    results = []

    compiled_re = re.compile(entity_regex, re.IGNORECASE) if entity_regex else None

    for entity in all_states:
        entity_id: str = entity.get("entity_id", "")
        state: str     = entity.get("state", "").lower()
        attrs: dict    = entity.get("attributes", {})

        # ── 1. Skip dead states ───────────────────────────────────────────
        if state in DEAD_STATES:
            continue

        # ── 2. Domain filter ─────────────────────────────────────────────
        if domain:
            entity_domain = entity_id.split(".")[0]
            if entity_domain != domain:
                continue

        # ── 3. Integration prefix filter ─────────────────────────────────
        #       e.g. 'withings' matches 'sensor.withings_body_weight_kg'
        if integration_prefix:
            entity_name = entity_id.split(".", 1)[-1]   # part after the dot
            if not entity_name.startswith(integration_prefix.lower()):
                continue

        # ── 4. device_class filter ───────────────────────────────────────
        if device_class:
            if attrs.get("device_class", "").lower() != device_class.lower():
                continue

        # ── 5. Regex filter on entity_id ─────────────────────────────────
        if compiled_re and not compiled_re.search(entity_id):
            continue

        results.append(entity)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 2 — Render a Jinja2 template via the REST API
#              (same template you would paste into Developer Tools → Template)
# ─────────────────────────────────────────────────────────────────────────────

def render_template(template: str) -> str:
    """POST a Jinja2 template to /api/template and return the rendered string."""
    resp = requests.post(
        f"{_HA_BASE_URL}/api/template",
        headers=HEADERS,
        json={"template": template},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.text


# ── Jinja2 building blocks (copy-paste into Developer Tools → Template) ──────

JINJA2_BY_INTEGRATION = """\
{#
  Returns all active entity_ids that belong to the 'withings' integration.
  Uses integration_entities() — the safest HA built-in for this.
  Change 'withings' to any other integration slug as needed.
#}
{% set active = integration_entities('withings')
   | select('has_value')
   | reject('is_state', 'unavailable')
   | reject('is_state', 'unknown')
   | list %}
{{ active | join('\\n') }}
"""

# has_value() already covers unavailable/unknown/none, but being explicit is safer.

JINJA2_BY_DEVICE_CLASS = """\
{#
  Returns active sensor entities whose device_class is 'battery'.
  Change device_class to 'weight', 'temperature', etc. as needed.
  Also change the integration slug or remove the first select to search globally.
#}
{% set ns = namespace(entities=[]) %}
{% for entity_id in integration_entities('withings') %}
  {% if states[entity_id] is defined
        and states[entity_id].state not in ['unavailable','unknown','none','']
        and states[entity_id].attributes.get('device_class','') == 'battery' %}
    {% set ns.entities = ns.entities + [entity_id] %}
  {% endif %}
{% endfor %}
{{ ns.entities | join('\\n') }}
"""

JINJA2_BY_REGEX = """\
{#
  Returns active entities from the 'withings' integration whose entity_id
  matches the regex pattern (here: anything containing 'weight' or 'battery').
  Uses the 'search' test which is available in HA's Jinja2 environment.
#}
{% set pattern = 'weight|battery' %}
{% set active = integration_entities('withings')
   | select('search', pattern)
   | select('has_value')
   | list %}
{{ active | join('\\n') }}
"""

JINJA2_GENERIC_STATES_FILTER = """\
{#
  Fully generic: no integration needed.
  Searches ALL sensors for device_class='battery', state not dead.
  Great fallback when you don't know the integration slug.
#}
{% set active_batteries = states.sensor
   | selectattr('attributes.device_class', 'eq', 'battery')
   | rejectattr('state', 'in', ['unavailable','unknown','none',''])
   | map(attribute='entity_id')
   | list %}
{{ active_batteries | join('\\n') }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 3 — Print a ready-to-use YAML automation snippet
# ─────────────────────────────────────────────────────────────────────────────

YAML_AUTOMATION = """\
# ─── YAML Automation: notify when any Withings battery is low ──────────────
# Paste this into your automations.yaml (or via the HA UI automation editor).
#
# Key design: the condition and action both use integration_entities() so
# no entity IDs are hardcoded; the automation survives entity ID renames.

alias: "Withings — Low Battery Alert (dynamic)"
description: >
  Fires whenever any currently-available Withings entity with device_class
  'battery' drops below 20 %.  Works even if entity IDs change.

trigger:
  - platform: template
    # Trigger becomes true when at least one active Withings battery is < 20
    value_template: >
      {% set low = integration_entities('withings')
         | select('has_value')
         | selectattr('attributes.device_class', 'eq', 'battery')
         | map(attribute='state') | map('int', default=100)
         | select('lt', 20) | list %}
      {{ low | count > 0 }}

condition:
  - condition: template
    value_template: >
      {# Double-check: at least one entity is truly available #}
      {% set cnt = integration_entities('withings')
         | select('has_value') | list | count %}
      {{ cnt > 0 }}

action:
  - service: notify.persistent_notification
    data:
      title: "⚠️ Withings Battery Low"
      message: >
        {% set low_entities = integration_entities('withings')
           | select('has_value')
           | selectattr('attributes.device_class', 'eq', 'battery')
           | list %}
        {% for e in low_entities %}
          {{ state_attr(e, 'friendly_name') | default(e) }}: {{ states(e) }} %
        {% endfor %}

mode: single
"""


# ─────────────────────────────────────────────────────────────────────────────
# DEMO — run scan and render templates
# ─────────────────────────────────────────────────────────────────────────────

def _print_section(title: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)


def main():
    # ── Python REST scan ────────────────────────────────────────────────────
    _print_section("STRATEGY 1 — Python REST scan")

    print("\n[A] All active Withings entities:")
    entities = scan_entities_python(integration_prefix="withings")
    if entities:
        for e in entities:
            dc = e["attributes"].get("device_class", "—")
            print(f"  {e['entity_id']:<50}  state={e['state']:<12}  device_class={dc}")
    else:
        print("  (none found — is the Withings integration connected?)")

    print("\n[B] Active Withings entities with device_class='battery':")
    battery = scan_entities_python(integration_prefix="withings", device_class="battery")
    for e in battery:
        print(f"  {e['entity_id']:<50}  state={e['state']}")
    if not battery:
        print("  (none found)")

    print("\n[C] Active sensors matching regex 'weight|bmi' (any integration):")
    weight = scan_entities_python(domain="sensor", entity_regex=r"weight|bmi")
    for e in weight:
        print(f"  {e['entity_id']:<50}  state={e['state']}")
    if not weight:
        print("  (none found)")

    # ── Jinja2 templates via /api/template ──────────────────────────────────
    _print_section("STRATEGY 2 — Jinja2 templates (rendered via REST API)")

    templates = {
        "integration_entities('withings') — active only": JINJA2_BY_INTEGRATION,
        "device_class='battery' from withings"          : JINJA2_BY_DEVICE_CLASS,
        "regex 'weight|battery' from withings"          : JINJA2_BY_REGEX,
        "global sensor battery scan (no integration)"   : JINJA2_GENERIC_STATES_FILTER,
    }

    for label, tmpl in templates.items():
        print(f"\n  Template: {label}")
        try:
            result = render_template(tmpl).strip()
            if result:
                for line in result.splitlines():
                    if line.strip():
                        print(f"    → {line.strip()}")
            else:
                print("    → (empty result)")
        except requests.HTTPError as err:
            print(f"    ERROR: {err}")

    # ── YAML automation snippet ──────────────────────────────────────────────
    _print_section("STRATEGY 3 — YAML automation snippet")
    print(YAML_AUTOMATION)

    # ── Developer Tools testing guide ────────────────────────────────────────
    _print_section("HOW TO TEST IN HA DEVELOPER TOOLS")
    print("""
  1. Open Home Assistant in your browser.
  2. Go to  Developer Tools  (the </> icon in the left sidebar).
  3. Click the  Template  tab.
  4. Paste any of the Jinja2 blocks printed above (STRATEGY 2) into the
     template editor on the left.
  5. The right panel previews the rendered output in real time — no save
     needed.  Any syntax error is highlighted immediately.

  Handy one-liner to quickly list all active Withings entities:
  ──────────────────────────────────────────────────────────────
  {{ integration_entities('withings') | select('has_value') | list }}

  Replace 'withings' with any other integration slug.
  Use  states.sensor | map(attribute='entity_id') | list  to browse every
  sensor when you don't know the slug.
""")


if __name__ == "__main__":
    main()

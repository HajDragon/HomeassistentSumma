"""
deploy_submit_script.py
-----------------------
Creates (or updates) the 'goedheid_sla_meting_op' script in Home Assistant
using the REST Config API.  This stores the script in HA's UI storage
(/config/.storage/) which is functionally identical to a YAML-defined script.

Run on the developer machine:
    python scripts/deploy_submit_script.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

HA_HOST  = "homeassistant.local"
HA_PORT  = 8123
HA_TOKEN = os.getenv("HA_TOKEN", (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIs"
    "ImlhdCI6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ."
    "c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
))

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}


def _resolve_ha_url() -> str:
    """Resolve homeassistant.local once to avoid mDNS flakiness on Windows."""
    import socket
    try:
        ip = socket.gethostbyname(HA_HOST)
        print(f"  Resolved {HA_HOST} → {ip}")
        return f"http://{ip}:{HA_PORT}"
    except OSError:
        print(f"  DNS lookup failed; falling back to hostname")
        return f"http://{HA_HOST}:{HA_PORT}"


HA_URL = _resolve_ha_url()

# ---------------------------------------------------------------------------
# Script payload — mirrors the YAML definition in the package file exactly.
# HA 2024+ accepts both "sequence" and "action"; we use "sequence" to match
# the existing package YAML style.
# ---------------------------------------------------------------------------
SCRIPT_ID = "goedheid_sla_meting_op"

SCRIPT_CONFIG = {
    "alias": "Sla Huidige Meting Op",
    "icon": "mdi:content-save-check",
    "sequence": [
        {
            "service": "simulation_manager.save_measurement",
            "data": {
                "gewicht":    "{{ states('input_number.goedheid_gewicht')    | float(0) }}",
                "spiermassa": "{{ states('input_number.goedheid_spiermassa') | float(0) }}",
                "vetmassa":   "{{ states('input_number.goedheid_vetmassa')   | float(0) }}",
                "bmi":        "{{ states('input_number.goedheid_bmi')        | float(0) }}",
                "timestamp":  "{{ states('input_datetime.goedheid_meetdatum') }}",
            },
        }
    ],
}


def ha_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    url  = f"{HA_URL}{path}"  # HA_URL already uses raw IP to avoid per-request mDNS
    body = json.dumps(payload).encode() if payload is not None else None
    req  = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")
    except Exception as exc:
        print(f"  Connection error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # ── 1. Verify HA is reachable ───────────────────────────────────────────
    print("Connecting to Home Assistant…")
    status, info = ha_request("GET", "/api/")
    if status != 200:
        print(f"  ✗ Cannot reach HA (HTTP {status})")
        sys.exit(1)
    print(f"  ✓ HA {info.get('version', '?')} reachable")

    # ── 2. Check current state ──────────────────────────────────────────────
    print(f"\nChecking for existing script.{SCRIPT_ID}…")
    status, _ = ha_request("GET", f"/api/states/script.{SCRIPT_ID}")
    if status == 200:
        print(f"  ℹ  script.{SCRIPT_ID} already exists — will overwrite")
    else:
        print(f"  ℹ  script.{SCRIPT_ID} not found — will create")

    # ── 3. POST to config API ───────────────────────────────────────────────
    print(f"\nPushing script config via /api/config/script/config/{SCRIPT_ID}…")
    status, resp = ha_request(
        "POST",
        f"/api/config/script/config/{SCRIPT_ID}",
        SCRIPT_CONFIG,
    )
    print(f"  HTTP {status}: {resp}")

    if status not in (200, 201):
        print("\n  ✗ Config API rejected the payload.")
        print("    Possible cause: HA validates the sequence strictly.")
        print("    Trying alternative with 'action' key instead of 'sequence'…\n")

        alt_config = dict(SCRIPT_CONFIG)
        alt_config["action"] = alt_config.pop("sequence")
        status, resp = ha_request(
            "POST",
            f"/api/config/script/config/{SCRIPT_ID}",
            alt_config,
        )
        print(f"  HTTP {status}: {resp}")
        if status not in (200, 201):
            print("\n  ✗ Both attempts failed.  Manual deployment required — see below.")
            _print_manual_instructions()
            sys.exit(1)

    print(f"\n  ✓ Script config accepted (HTTP {status})")

    # ── 4. Verify entity is now live ────────────────────────────────────────
    print(f"\nVerifying script.{SCRIPT_ID} in HA states…")
    status, state = ha_request("GET", f"/api/states/script.{SCRIPT_ID}")
    if status == 200:
        print(f"  ✓ script.{SCRIPT_ID} is LIVE  (state: {state.get('state', '?')})")
    else:
        print(f"  ✗ Entity not found after push (HTTP {status}) — HA may need a reload.")
        print("    Triggering homeassistant/reload_all…")
        _reload_all()
        status, _ = ha_request("GET", f"/api/states/script.{SCRIPT_ID}")
        if status == 200:
            print(f"  ✓ script.{SCRIPT_ID} is LIVE after reload")
        else:
            print("  ✗ Still not found.  Manual deployment required — see below.")
            _print_manual_instructions()
            sys.exit(1)

    print("\nDeployment complete.")


def _reload_all() -> None:
    status, _ = ha_request("POST", "/api/services/homeassistant/reload_all", {})
    print(f"  reload_all → HTTP {status}")


def _print_manual_instructions() -> None:
    print("""
──────────────────────────────────────────────────────────────────
MANUAL FALLBACK — steps to add the script via the HA UI:
──────────────────────────────────────────────────────────────────
1. Open Home Assistant → Settings → Automations & Scenes → Scripts
2. Click  "+ Create script"  (top-right)
3. Click the three-dot menu (⋮) → "Edit in YAML"
4. Paste the following, then click Save:

alias: "Sla Huidige Meting Op"
icon: mdi:content-save-check
sequence:
  - service: simulation_manager.save_measurement
    data:
      gewicht:    "{{ states('input_number.goedheid_gewicht')    | float(0) }}"
      spiermassa: "{{ states('input_number.goedheid_spiermassa') | float(0) }}"
      vetmassa:   "{{ states('input_number.goedheid_vetmassa')   | float(0) }}"
      bmi:        "{{ states('input_number.goedheid_bmi')        | float(0) }}"
      timestamp:  "{{ states('input_datetime.goedheid_meetdatum') }}"

5. After saving, rename the script ID to  goedheid_sla_meting_op
   (edit the "Object ID" field at the top of the script editor)
──────────────────────────────────────────────────────────────────
""")


if __name__ == "__main__":
    main()

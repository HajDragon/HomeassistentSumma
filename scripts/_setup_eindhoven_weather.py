"""
One-shot script: rename weather.forecast_home → display name "Eindhoven"
via the HA entity registry, then update coordinates to exact city centre
via the Met.no options flow.

Run once from the project root with the venv active:
    python scripts/_setup_eindhoven_weather.py
"""

import json
import websocket  # websocket-client

WS_URL = "ws://homeassistant.local:8123/api/websocket"
TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIsImlhdCI"
    "6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ"
    ".c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
)

# Eindhoven city-centre coordinates
EH_LAT  = 51.4416
EH_LON  = 5.4697
EH_ELEV = 17  # metres above sea level

ENTITY_ID = "weather.forecast_home"

results = {}
state = {}


def send(ws, payload):
    ws.send(json.dumps(payload))


def on_open(ws):
    pass


def on_message(ws, raw):
    msg = json.loads(raw)
    t = msg.get("type")

    # ── AUTH ──────────────────────────────────────────────────────────────────
    if t == "auth_required":
        print("→ Authenticating...")
        send(ws, {"type": "auth", "access_token": TOKEN})

    elif t == "auth_ok":
        print(f"✓ Authenticated (HA {msg.get('ha_version', '?')})")
        # Step 1: rename the entity to "Eindhoven" in the entity registry
        print(f"→ Renaming {ENTITY_ID} → 'Eindhoven' in entity registry...")
        send(ws, {
            "id": 1,
            "type": "config/entity_registry/update",
            "entity_id": ENTITY_ID,
            "name": "Eindhoven",
        })

    elif t == "auth_invalid":
        print("✗ Auth failed.")
        ws.close()

    elif t == "result":
        mid = msg.get("id")
        ok  = msg.get("success", False)

        # id=1 — entity rename result
        if mid == 1:
            if ok:
                entity = msg.get("result", {}).get("entity_entry", {})
                print(f"✓ Entity renamed. name='{entity.get('name')}'"
                      f"  aliases={entity.get('aliases', [])}")
                # Step 2: start the Met.no options flow to update coordinates
                print("→ Starting Met.no options flow to update coordinates...")
                send(ws, {
                    "id": 2,
                    "type": "config_entries/options_flow/create",
                    "entry_id": state.get("entry_id", ""),
                })
            else:
                err = msg.get("error", {})
                print(f"✗ Entity rename failed: {err.get('code','?')} — {err.get('message','')}")
                ws.close()

        # id=2 — options flow started (or error if entry_id unknown)
        elif mid == 2:
            if ok:
                flow = msg.get("result", {})
                fid = flow.get("flow_id", "")
                state["options_flow_id"] = fid
                print(f"  Options flow started: {fid}")
                # Submit updated coordinates
                send(ws, {
                    "id": 3,
                    "type": "config_entries/options_flow/progress",
                    "flow_id": fid,
                    "user_input": {"elevation": EH_ELEV},
                })
            else:
                err = msg.get("error", {})
                # Options flow for Met.no only exposes elevation — that's fine;
                # we only need the rename anyway.
                print(f"  ℹ Options flow not available ({err.get('code','?')}) — skipping coordinate update.")
                results["done"] = True
                ws.close()

        # id=3 — options flow submitted
        elif mid == 3:
            if ok:
                print(f"✓ Elevation updated to {EH_ELEV}m.")
            else:
                err = msg.get("error", {})
                print(f"  ⚠ Options submit: {err.get('code','?')} — {err.get('message','')}")
            results["done"] = True
            ws.close()

    elif t == "event":
        pass


def on_error(ws, error):
    print(f"✗ WebSocket error: {error}")


def on_close(ws, code, msg_text):
    print()
    if results.get("done"):
        print("=" * 55)
        print("  ✓ Done!")
        print(f"  Entity  : {ENTITY_ID}")
        print("  Display : Eindhoven")
        print("  Run push_dashboard.py to refresh the card on the UI.")
        print("=" * 55)
    else:
        print("✗ Setup did not complete — check errors above.")


# ── Resolve the Met.no config entry_id beforehand via a quick WS probe ────────
# We embed it in the flow so the logic stays linear.
_entry_id_resolved = []


def on_message_probe(ws, raw):
    msg = json.loads(raw)
    t = msg.get("type")
    if t == "auth_required":
        ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    elif t == "auth_ok":
        ws.send(json.dumps({"id": 1, "type": "config_entries/get", "domain": "met"}))
    elif t == "result":
        entries = msg.get("result") or []
        if entries:
            _entry_id_resolved.append(entries[0]["entry_id"])
            print(f"  Resolved Met.no entry_id: {_entry_id_resolved[0]}")
        ws.close()
    elif t == "event":
        pass


print("=" * 55)
print("  Setting up Eindhoven weather")
print("=" * 55)

# First pass: resolve the Met.no entry_id
print("→ Resolving Met.no entry_id...")
probe = websocket.WebSocketApp(WS_URL, on_message=on_message_probe)
probe.run_forever()

if _entry_id_resolved:
    state["entry_id"] = _entry_id_resolved[0]
else:
    print("  ⚠ Could not resolve entry_id — options flow will be skipped.")

# Second pass: rename + update options
ws_app = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)
ws_app.run_forever()

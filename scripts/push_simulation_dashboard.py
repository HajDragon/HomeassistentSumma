"""
push_simulation_dashboard.py
Push the Simulation dashboard YAML to HA AND ensure all 4 measurement
periods exist — all in one WebSocket connection.

Message-ID plan
---------------
  1  lovelace/dashboards/list
  2  lovelace/dashboards/create          (only when not yet existing)
  3  lovelace/config/save
  4  call_service  switch_period  period_1
  5  call_service  switch_period  period_2
  6  call_service  switch_period  period_3
  7  call_service  switch_period  period_4
  8  call_service  switch_period  period_1  (restore active tab to Meting 1)
"""
import json
import os
import time
import yaml
import websocket  # pip install websocket-client

WS_URL = "ws://homeassistant.local:8123/api/websocket"
TOKEN  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIsImlhdCI"
    "6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ"
    ".c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
)

SIMULATIE_URL_PATH = "simulatie-goedheid"

# The 4 canonical periods — switch_period is idempotent: creates if missing,
# updates label/date if already present, never deletes existing measurements.
PERIODS = [
    {"period_id": "period_1", "label": "Meting 1 (start)", "date": "2026-01-01"},
    {"period_id": "period_2", "label": "Meting 2 (2 mnd)", "date": "2026-03-01"},
    {"period_id": "period_3", "label": "Meting 3 (4 mnd)", "date": "2026-05-01"},
    {"period_id": "period_4", "label": "Meting 4 (6 mnd)", "date": "2026-07-01"},
]

# IDs 4-7 = switch each period; id=8 = restore active to period_1
PERIOD_SWITCH_IDS = {4: PERIODS[0], 5: PERIODS[1], 6: PERIODS[2], 7: PERIODS[3]}
RESTORE_ACTIVE_ID = 8

# ── Load dashboard config from YAML ─────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "..", "config", "dashboards", "simulation_dashboard.yaml"), encoding="utf-8") as _f:
    _raw = yaml.safe_load(_f)

simulatie_config = {
    "title": "Simulatie Goedheid",
    "views": _raw["views"],
}


# ── WebSocket push ───────────────────────────────────────────────────────────
def push():
    print("=" * 55)
    print("  Pushing Simulation dashboard + ensuring 4 periods")
    print(f"  URL path  : {SIMULATIE_URL_PATH}")
    print(f"  Views     : {len(simulatie_config['views'])}")
    print("=" * 55)

    results = {}

    def send(ws, payload):
        ws.send(json.dumps(payload))

    def send_switch_period(ws, msg_id, period):
        send(ws, {
            "id": msg_id,
            "type": "call_service",
            "domain": "simulation_manager",
            "service": "switch_period",
            "service_data": period,
        })

    def on_open(ws):
        pass  # HA sends auth_required first

    def on_message(ws, raw):
        msg      = json.loads(raw)
        msg_type = msg.get("type")

        # ── Auth ──────────────────────────────────────────────────────────
        if msg_type == "auth_required":
            print("  → Authenticating...")
            send(ws, {"type": "auth", "access_token": TOKEN})

        elif msg_type == "auth_ok":
            print(f"  ✓ Authenticated  (HA {msg.get('ha_version', '?')})")
            print("  → Listing existing dashboards...")
            send(ws, {"id": 1, "type": "lovelace/dashboards/list"})

        elif msg_type == "auth_invalid":
            print("  ✗ Auth failed — check TOKEN.")
            results["error"] = "auth_invalid"
            ws.close()

        # ── Results ───────────────────────────────────────────────────────
        elif msg_type == "result":
            msg_id  = msg.get("id")
            success = msg.get("success", False)

            # id=1 — dashboard list
            if msg_id == 1:
                existing = [d.get("url_path") for d in (msg.get("result") or [])] if success else []
                if SIMULATIE_URL_PATH in existing:
                    print("  ℹ Dashboard already exists — saving config...")
                    send(ws, {
                        "id": 3,
                        "type": "lovelace/config/save",
                        "url_path": SIMULATIE_URL_PATH,
                        "config": simulatie_config,
                    })
                else:
                    print("  → Creating dashboard entry...")
                    send(ws, {
                        "id": 2,
                        "type": "lovelace/dashboards/create",
                        "url_path": SIMULATIE_URL_PATH,
                        "title": "Simulatie Goedheid",
                        "icon": "mdi:scale-bathroom",
                        "show_in_sidebar": True,
                        "require_admin": False,
                    })

            # id=2 — dashboard created
            elif msg_id == 2:
                if success:
                    print("  ✓ Dashboard entry created.")
                else:
                    err = msg.get("error", {})
                    if err.get("code") == "already_exists":
                        print("  ℹ Dashboard already existed.")
                    else:
                        print(f"  ⚠ Create warning: {err.get('code')} — {err.get('message','')}")
                print("  → Saving config...")
                send(ws, {
                    "id": 3,
                    "type": "lovelace/config/save",
                    "url_path": SIMULATIE_URL_PATH,
                    "config": simulatie_config,
                })

            # id=3 — config saved; now ensure periods
            elif msg_id == 3:
                if success:
                    print("  ✓ Dashboard config saved!")
                else:
                    err = msg.get("error", {})
                    print(f"  ✗ Save failed: {err.get('code','?')} — {err.get('message','')}")
                    results["error"] = err
                    ws.close()
                    return
                print("  → Ensuring 4 measurement periods...")
                time.sleep(0.2)
                send_switch_period(ws, 4, PERIODS[0])

            # ids 4-7 — switch_period calls for each of the 4 periods
            elif msg_id in PERIOD_SWITCH_IDS:
                period = PERIOD_SWITCH_IDS[msg_id]
                label  = period["label"]
                if success:
                    print(f"  ✓ Period ready: {label}")
                else:
                    print(f"  ⚠ Period warning ({label}): {msg.get('error', {})}")
                next_id = msg_id + 1
                if next_id in PERIOD_SWITCH_IDS:
                    time.sleep(0.2)
                    send_switch_period(ws, next_id, PERIOD_SWITCH_IDS[next_id])
                else:
                    # All 4 done — restore active period to Meting 1
                    time.sleep(0.2)
                    send_switch_period(ws, RESTORE_ACTIVE_ID, PERIODS[0])

            # id=8 — restore active period
            elif msg_id == RESTORE_ACTIVE_ID:
                print("  ✓ Active period restored to Meting 1.")
                results["done"] = True
                ws.close()

    def on_error(ws, error):
        print(f"  ✗ WebSocket error: {error}")
        results["error"] = str(error)

    def on_close(ws, code, msg):
        print()
        print("=" * 55)
        if results.get("done"):
            print("  ALL DONE")
            print()
            print("  1. Press F5 in your HA browser to reload.")
            print(f"  2. Open: http://homeassistant.local:8123/{SIMULATIE_URL_PATH}")
        else:
            print(f"  Finished with issues: {results.get('error', 'unknown')}")
        print("=" * 55)

    ws_app = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws_app.run_forever()


if __name__ == "__main__":
    push()

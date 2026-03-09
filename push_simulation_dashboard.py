"""
push_simulation_dashboard.py
Push the updated Simulation dashboard.yaml to Home Assistant via WebSocket.
"""
import json
import os
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

# ── Load dashboard config from YAML ─────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "Simulation dashboard.yaml"), encoding="utf-8") as _f:
    _raw = yaml.safe_load(_f)

simulatie_config = {
    "title": "Simulatie Goedheid",
    "views": _raw["views"],
}

# ── WebSocket push ───────────────────────────────────────────────────────────
def push():
    print("=" * 55)
    print("  Pushing Simulation dashboard to Home Assistant")
    print(f"  URL path  : {SIMULATIE_URL_PATH}")
    print(f"  Views     : {len(simulatie_config['views'])}")
    print("=" * 55)

    results = {}

    def send(ws, payload):
        ws.send(json.dumps(payload))

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
                print(f"  ✓ Existing dashboards: {existing or '(none)'}")

                if SIMULATIE_URL_PATH in existing:
                    print("  ℹ Dashboard already exists — skipping create.")
                    print("  → Saving config...")
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
                    code = err.get("code", "?")
                    if code == "already_exists":
                        print("  ℹ Dashboard already existed.")
                    else:
                        print(f"  ⚠ Create warning: {code} — {err.get('message','')}")
                print("  → Saving config...")
                send(ws, {
                    "id": 3,
                    "type": "lovelace/config/save",
                    "url_path": SIMULATIE_URL_PATH,
                    "config": simulatie_config,
                })

            # id=3 — config saved
            elif msg_id == 3:
                if success:
                    print("  ✓ Simulation dashboard config saved!")
                    results["done"] = True
                else:
                    err = msg.get("error", {})
                    print(f"  ✗ Save failed: {err.get('code','?')} — {err.get('message','')}")
                    results["error"] = err
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
            print("  Next steps:")
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

"""
seed_periods.py
───────────────────────────────────────────────────────────────
Directly seeds all 4 Mevrouw Goedheid simulation periods into
sensor.simulation_manager via the HA WebSocket API.

Works without SSH or Studio Code Server — only needs network
access to Home Assistant (same as push_simulation_dashboard.py).

Usage:
  python seed_periods.py
───────────────────────────────────────────────────────────────
"""
import json
import time
import websocket  # pip install websocket-client

WS_URL = "ws://homeassistant.local:8123/api/websocket"
TOKEN  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIsImlhdCI"
    "6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ"
    ".c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
)

# Measurement data from plan.md
PERIODS = [
    {
        "period_id":  "period_1",
        "label":      "Meting 1 (start)",
        "date":       "2026-01-01",
        "measurement": {
            "gewicht":    70.0,
            "spiermassa": 29.5,
            "vetmassa":   24.0,
            "bmi":        24.8,
            "timestamp":  "2026-01-01T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_2",
        "label":      "Meting 2 (2 mnd)",
        "date":       "2026-03-01",
        "measurement": {
            "gewicht":    72.0,
            "spiermassa": 29.3,
            "vetmassa":   25.5,
            "bmi":        25.5,
            "timestamp":  "2026-03-01T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_3",
        "label":      "Meting 3 (4 mnd)",
        "date":       "2026-05-01",
        "measurement": {
            "gewicht":    74.5,
            "spiermassa": 29.0,
            "vetmassa":   27.0,
            "bmi":        26.4,
            "timestamp":  "2026-05-01T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_4",
        "label":      "Meting 4 (6 mnd)",
        "date":       "2026-07-01",
        "measurement": {
            "gewicht":    77.0,
            "spiermassa": 28.8,
            "vetmassa":   28.5,
            "bmi":        27.3,
            "timestamp":  "2026-07-01T09:00:00+00:00",
        },
    },
]

# We queue up all service calls as (id, domain, service, data) tuples.
# IDs: 1=reset, 2/3=period1, 4/5=period2, 6/7=period3, 8/9=period4, 10=switch back
_calls = []
_msg_id = 0

def _build_calls():
    global _calls
    calls = []
    # Reset first
    calls.append({"service": "simulation_manager.reset_simulation", "data": {}})
    for p in PERIODS:
        calls.append({
            "service": "simulation_manager.switch_period",
            "data": {
                "period_id": p["period_id"],
                "label":     p["label"],
                "date":      p["date"],
            },
        })
        calls.append({
            "service": "simulation_manager.save_measurement",
            "data": p["measurement"],
        })
    # Leave on period_1 as the active view
    calls.append({
        "service": "simulation_manager.switch_period",
        "data": {"period_id": "period_1"},
    })
    return calls

def run():
    calls = _build_calls()
    # Assign IDs 1..N
    pending = {i + 1: c for i, c in enumerate(calls)}
    results = {}

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=lambda ws: None,
        on_message=lambda ws, raw: handle(ws, raw, pending, results),
        on_error=lambda ws, err: print(f"  ✗ WS error: {err}"),
        on_close=lambda ws, code, msg: print(f"  ✓ Connection closed ({code})"),
    )

    print("=" * 55)
    print("  Seeding Mevrouw Goedheid periods via WebSocket")
    print(f"  {len(calls)} service calls queued")
    print("=" * 55)
    ws.run_forever()

    if results.get("done"):
        print("\n  All periods seeded successfully!")
        print("  Refresh your HA dashboard to see the data.")
    else:
        print("\n  Something went wrong — check output above.")


def handle(ws, raw, pending, results):
    msg = json.loads(raw)
    t = msg.get("type")

    if t == "auth_required":
        print("  → Authenticating...")
        ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))

    elif t == "auth_ok":
        print(f"  ✓ Authenticated (HA {msg.get('ha_version', '?')})")
        # Fire the first call
        _fire_next(ws, pending, 1)

    elif t == "auth_invalid":
        print("  ✗ Authentication failed.")
        ws.close()

    elif t == "result":
        msg_id  = msg.get("id")
        success = msg.get("success", False)
        call    = pending.get(msg_id, {})
        svc     = call.get("service", f"call #{msg_id}")

        if success:
            print(f"  ✓ [{msg_id}/{len(pending)}] {svc}")
        else:
            err = msg.get("error", {})
            print(f"  ✗ [{msg_id}/{len(pending)}] {svc} — {err.get('code')}: {err.get('message')}")

        next_id = msg_id + 1
        if next_id in pending:
            time.sleep(0.3)
            _fire_next(ws, pending, next_id)
        else:
            results["done"] = True
            ws.close()


def _fire_next(ws, pending, msg_id):
    call = pending[msg_id]
    service_parts = call["service"].split(".")
    domain, service = service_parts[0], service_parts[1]
    ws.send(json.dumps({
        "id":   msg_id,
        "type": "call_service",
        "domain":  domain,
        "service": service,
        "service_data": call["data"],
    }))


if __name__ == "__main__":
    run()

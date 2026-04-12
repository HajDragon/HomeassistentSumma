"""
seed_periods.py
───────────────────────────────────────────────────────────────
Directly seeds all 8 March 2026 cardiac monitoring points into
sensor.simulation_manager via the HA WebSocket API.

Works without SSH or Studio Code Server — only needs network
access to Home Assistant (same as push_simulation_dashboard.py).

Usage:
  python seed_periods.py
───────────────────────────────────────────────────────────────
"""
import json
import os
import sys
import time
import websocket  # pip install websocket-client

from dotenv import load_dotenv

load_dotenv()

_HA_BASE_URL = os.getenv("HA_BASE_URL", "http://homeassistant.local:8123").rstrip("/")
TOKEN        = os.getenv("HA_TOKEN")
if not TOKEN:
    sys.exit("Error: HA_TOKEN not set — copy .env.example to .env and fill in your token.")

WS_URL = _HA_BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"

# Measurement data from lesson plan (March 2026).
PERIODS = [
    {
        "period_id":  "period_1",
        "label":      "Meting 1 (01-03-2026)",
        "date":       "2026-03-01",
        "measurement": {
            "gewicht":        68.0,
            "bloeddruk_sys":  130,
            "bloeddruk_dia":  80,
            "bloeddruk":      "130/80",
            "hartfrequentie": 72,
            "ademfrequentie": 16,
            "saturatie":      96,
            "opmerking":      "Stabiele situatie na ontslag",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-01T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_2",
        "label":      "Meting 2 (04-03-2026)",
        "date":       "2026-03-04",
        "measurement": {
            "gewicht":        68.2,
            "bloeddruk_sys":  132,
            "bloeddruk_dia":  82,
            "bloeddruk":      "132/82",
            "hartfrequentie": 74,
            "ademfrequentie": 16,
            "saturatie":      96,
            "opmerking":      "Geen klachten",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-04T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_3",
        "label":      "Meting 3 (08-03-2026)",
        "date":       "2026-03-08",
        "measurement": {
            "gewicht":        68.7,
            "bloeddruk_sys":  135,
            "bloeddruk_dia":  85,
            "bloeddruk":      "135/85",
            "hartfrequentie": 78,
            "ademfrequentie": 17,
            "saturatie":      95,
            "opmerking":      "Licht vermoeid",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-08T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_4",
        "label":      "Meting 4 (11-03-2026)",
        "date":       "2026-03-11",
        "measurement": {
            "gewicht":        69.3,
            "bloeddruk_sys":  138,
            "bloeddruk_dia":  86,
            "bloeddruk":      "138/86",
            "hartfrequentie": 80,
            "ademfrequentie": 18,
            "saturatie":      95,
            "opmerking":      "Enkels licht gezwollen",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-11T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_5",
        "label":      "Meting 5 (15-03-2026)",
        "date":       "2026-03-15",
        "measurement": {
            "gewicht":        70.1,
            "bloeddruk_sys":  142,
            "bloeddruk_dia":  88,
            "bloeddruk":      "142/88",
            "hartfrequentie": 86,
            "ademfrequentie": 19,
            "saturatie":      94,
            "opmerking":      "Kortademig bij inspanning",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-15T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_6",
        "label":      "Meting 6 (18-03-2026)",
        "date":       "2026-03-18",
        "measurement": {
            "gewicht":        70.8,
            "bloeddruk_sys":  145,
            "bloeddruk_dia":  90,
            "bloeddruk":      "145/90",
            "hartfrequentie": 90,
            "ademfrequentie": 20,
            "saturatie":      94,
            "opmerking":      "Meer oedeem in onderbenen",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-18T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_7",
        "label":      "Meting 7 (22-03-2026)",
        "date":       "2026-03-22",
        "measurement": {
            "gewicht":        71.5,
            "bloeddruk_sys":  150,
            "bloeddruk_dia":  92,
            "bloeddruk":      "150/92",
            "hartfrequentie": 96,
            "ademfrequentie": 21,
            "saturatie":      93,
            "opmerking":      "Gewicht stijgt snel",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-22T09:00:00+00:00",
        },
    },
    {
        "period_id":  "period_8",
        "label":      "Meting 8 (25-03-2026)",
        "date":       "2026-03-25",
        "measurement": {
            "gewicht":        72.2,
            "bloeddruk_sys":  155,
            "bloeddruk_dia":  95,
            "bloeddruk":      "155/95",
            "hartfrequentie": 102,
            "ademfrequentie": 22,
            "saturatie":      92,
            "opmerking":      "Duidelijke verslechtering",
            "profile_age":    70,
            "profile_history": "History of MI, Arthrosis",
            "timestamp":      "2026-03-25T09:00:00+00:00",
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

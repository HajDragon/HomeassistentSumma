"""
deploy_simulation_manager.py
─────────────────────────────────────────────────────────────────────────────
Deploys the Simulation Manager custom integration and Lovelace card to your
Home Assistant instance over the REST + WebSocket API.

Steps performed
───────────────
  1. Upload custom_components/simulation_manager/* via the HA Supervisor
     file upload endpoint (requires SSH/SFTP access OR Studio Code Server).
     This script prints the scp/copy commands you must run on the HA host.
  2. Register the Lovelace JS resource (www/ → /local/).
  3. Reload configuration via the HA Core REST API.
  4. Optionally seed the simulation with the four Mevrouw Goedheid periods.

Usage
─────
  python deploy_simulation_manager.py [--seed]

  --seed   After deploying, call the services to populate the four
           Mevrouw Goedheid measurement periods from your lesson plan.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import requests

# ── Shared connection config (reuse from existing project) ────────────────────

BASE_URL = "http://homeassistant.local:8123"
TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIsImlhdCI"
    "6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ"
    ".c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

DOMAIN = "simulation_manager"


# ── Helper: call a HA service via REST ────────────────────────────────────────

def call_service(domain: str, service: str, data: dict) -> dict:
    url = f"{BASE_URL}/api/services/{domain}/{service}"
    resp = requests.post(url, headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json() if resp.text else {}


# ── Helper: GET entity state ──────────────────────────────────────────────────

def get_state(entity_id: str) -> dict | None:
    url = f"{BASE_URL}/api/states/{entity_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


# ── Step 1: Print file-copy instructions ─────────────────────────────────────

def print_copy_instructions() -> None:
    print(
        """
╔══════════════════════════════════════════════════════════════════╗
║  STEP 1 — Copy files to your Home Assistant config directory     ║
╚══════════════════════════════════════════════════════════════════╝

You need SSH / Studio Code Server access to your HA host.
Run the following commands from within HA (or via SCP from this machine):

  mkdir -p /config/custom_components/simulation_manager
  mkdir -p /config/www/simulation-period-card

  # Copy integration
  cp custom_components/simulation_manager/__init__.py   /config/custom_components/simulation_manager/
  cp custom_components/simulation_manager/manifest.json /config/custom_components/simulation_manager/
  cp custom_components/simulation_manager/const.py      /config/custom_components/simulation_manager/
  cp custom_components/simulation_manager/models.py     /config/custom_components/simulation_manager/
  cp custom_components/simulation_manager/sensor.py     /config/custom_components/simulation_manager/
  cp custom_components/simulation_manager/services.yaml /config/custom_components/simulation_manager/

  # Copy Lovelace card
  cp www/simulation-period-card/simulation-period-card.js /config/www/simulation-period-card/

Then add the integration to your configuration.yaml:

  simulation_manager:

And add the Lovelace resource in your dashboard settings:
  URL:  /local/simulation-period-card/simulation-period-card.js
  Type: JavaScript Module

After copying, restart Home Assistant Core:
  ha core restart
"""
    )


# ── Step 2: Register Lovelace resource via REST ───────────────────────────────

def register_lovelace_resource() -> None:
    print("Checking if Lovelace resource is already registered...")
    url = f"{BASE_URL}/api/lovelace/resources"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code == 401:
        print("  ✗ Unauthorised — check your TOKEN.")
        return
    if resp.status_code != 200:
        print(f"  ✗ Could not fetch resources (HTTP {resp.status_code}).")
        return

    resources = resp.json()
    card_url = "/local/simulation-period-card/simulation-period-card.js"
    already  = any(r.get("url") == card_url for r in resources)

    if already:
        print("  ✓ Lovelace resource already registered.")
        return

    add_resp = requests.post(
        url,
        headers=HEADERS,
        json={"res_type": "module", "url": card_url},
        timeout=10,
    )
    if add_resp.status_code in (200, 201):
        print("  ✓ Lovelace resource registered.")
    else:
        print(f"  ✗ Failed to register resource (HTTP {add_resp.status_code}): {add_resp.text}")


# ── Step 3: Verify sensor entity exists ──────────────────────────────────────

def verify_integration() -> bool:
    print(f"\nVerifying sensor.{DOMAIN} exists...")
    state = get_state(f"sensor.{DOMAIN}")
    if state:
        print(f"  ✓ sensor.{DOMAIN} found. State: {state['state']}")
        return True
    else:
        print(
            f"  ✗ sensor.{DOMAIN} not found.\n"
            "    Make sure you have:\n"
            "      1. Copied the files to /config/custom_components/simulation_manager/\n"
            "      2. Added  simulation_manager:  to configuration.yaml\n"
            "      3. Restarted Home Assistant Core."
        )
        return False


# ── Step 4 (optional): Seed Mevrouw Goedheid data ────────────────────────────

# This mirrors the measurement table from plan.md exactly.
GOEDHEID_SEED_DATA = [
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


def seed_goedheid_data() -> None:
    print("\nSeeding Mevrouw Goedheid simulation data...")

    # Reset first so we start clean.
    print("  Resetting existing simulation state...")
    call_service(DOMAIN, "reset_simulation", {})
    time.sleep(0.5)

    for entry in GOEDHEID_SEED_DATA:
        pid   = entry["period_id"]
        label = entry["label"]
        date  = entry["date"]

        # Switch to (create) the period.
        call_service(DOMAIN, "switch_period", {
            "period_id": pid,
            "label":     label,
            "date":      date,
        })
        time.sleep(0.3)

        # Store the measurement for this period.
        call_service(DOMAIN, "save_measurement", entry["measurement"])
        time.sleep(0.3)

        print(f"  ✓ {label} ({date}) seeded.")

    # Leave the simulation on meting 1 as the 'current' view.
    call_service(DOMAIN, "switch_period", {"period_id": "period_1"})
    print("  ✓ Active period reset to Meting 1 (start).")
    print("  Seed complete — open your dashboard to verify.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy Simulation Manager to Home Assistant.")
    parser.add_argument("--seed", action="store_true", help="Seed Mevrouw Goedheid demo data after deploy.")
    args = parser.parse_args()

    print("═" * 66)
    print("  Simulation Manager — Deployment Script")
    print("═" * 66)

    print_copy_instructions()

    input("Press ENTER once you have copied the files and restarted HA Core...")

    register_lovelace_resource()

    ok = verify_integration()
    if not ok:
        sys.exit(1)

    if args.seed:
        seed_goedheid_data()
    else:
        print(
            "\nTip: run  python deploy_simulation_manager.py --seed"
            "  to auto-populate the Mevrouw Goedheid lesson data."
        )

    print("\n✓ Deployment complete.")


if __name__ == "__main__":
    main()

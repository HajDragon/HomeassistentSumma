"""
refresh_cardiac_history_influx.py
───────────────────────────────────────────────────────────────
Purges old cardiac lesson points in InfluxDB and writes the
8 approved lesson datapoints for March 2026.

Required env vars:
  INFLUX_URL        e.g. http://localhost:8086
  INFLUX_TOKEN      API token with write/delete rights
  INFLUX_ORG        organization name
  INFLUX_BUCKET     target bucket

Optional env vars:
  INFLUX_MEASUREMENT  default: goedheid_cardiac

Usage:
  python scripts/refresh_cardiac_history_influx.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL") or "http://localhost:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
MEASUREMENT = os.getenv("INFLUX_MEASUREMENT", "goedheid_cardiac")

if not INFLUX_TOKEN or not INFLUX_ORG or not INFLUX_BUCKET:
    sys.exit(
        "Missing required env vars: INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET."
    )

LESSON_ROWS = [
    ("2026-03-01T09:00:00Z", 68.0, 130, 80, 72, 16, 96, "Stabiele situatie na ontslag"),
    ("2026-03-04T09:00:00Z", 68.2, 132, 82, 74, 16, 96, "Geen klachten"),
    ("2026-03-08T09:00:00Z", 68.7, 135, 85, 78, 17, 95, "Licht vermoeid"),
    ("2026-03-11T09:00:00Z", 69.3, 138, 86, 80, 18, 95, "Enkels licht gezwollen"),
    ("2026-03-15T09:00:00Z", 70.1, 142, 88, 86, 19, 94, "Kortademig bij inspanning"),
    ("2026-03-18T09:00:00Z", 70.8, 145, 90, 90, 20, 94, "Meer oedeem in onderbenen"),
    ("2026-03-22T09:00:00Z", 71.5, 150, 92, 96, 21, 93, "Gewicht stijgt snel"),
    ("2026-03-25T09:00:00Z", 72.2, 155, 95, 102, 22, 92, "Duidelijke verslechtering"),
]


def _to_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> None:
    print("Connecting to InfluxDB:", INFLUX_URL)
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        delete_api = client.delete_api()
        write_api = client.write_api(write_options=SYNCHRONOUS)

        print("Purging existing cardiac points for measurement:", MEASUREMENT)
        delete_api.delete(
            start="1970-01-01T00:00:00Z",
            stop="2100-01-01T00:00:00Z",
            predicate=f'_measurement="{MEASUREMENT}"',
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
        )

        points: list[Point] = []
        for ts, gewicht, sys_bp, dia_bp, hr, rr, spo2, note in LESSON_ROWS:
            point = (
                Point(MEASUREMENT)
                .tag("patient", "mevrouw_goedheid")
                .tag("profile", "70y_mi_arthrosis")
                .field("gewicht", gewicht)
                .field("bloeddruk_sys", sys_bp)
                .field("bloeddruk_dia", dia_bp)
                .field("hartfrequentie", hr)
                .field("ademfrequentie", rr)
                .field("saturatie", spo2)
                .field("opmerking", note)
                .time(_to_dt(ts), WritePrecision.S)
            )
            points.append(point)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

    print("Influx refresh complete. Written points:", len(LESSON_ROWS))


if __name__ == "__main__":
    main()

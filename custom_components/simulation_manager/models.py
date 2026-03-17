"""
Data models for Simulation Manager.

Hierarchy:
    SimulationState
        └─ MeasurementPeriod  (keyed by period_id in a dict)
                └─ Measurement  (ordered list — append-only)

Design principles:
  - Every model owns its own serialisation (to_dict / from_dict).
  - SimulationState exposes the three core mutations as plain methods;
    the integration layer stays thin and just calls these methods + persists.
  - No HA imports here — models are pure Python for easy unit testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Measurement — a single body-scan reading
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Measurement:
    """One measurement snapshot stored inside a period."""

    timestamp: str
    # Body Scan metrics
    gewicht: float = 0.0
    spiermassa: float = 0.0
    vetmassa: float = 0.0
    vochtbalans: float = 0.0
    bmi: float = 0.0
    # Cardiac metrics
    bloeddruk_sys: float = 0.0
    bloeddruk_dia: float = 0.0
    hartfrequentie: float = 0.0
    ademfrequentie: float = 0.0
    saturatie: float = 0.0
    # Notes
    opmerking: str = ""
    # Accommodates arbitrary extra fields sent via the service call.
    extra: dict[str, Any] = field(default_factory=dict)

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        d = {
            "timestamp": self.timestamp,
            "gewicht": self.gewicht,
            "spiermassa": self.spiermassa,
            "vetmassa": self.vetmassa,
            "vochtbalans": self.vochtbalans,
            "bmi": self.bmi,
            "bloeddruk_sys": self.bloeddruk_sys,
            "bloeddruk_dia": self.bloeddruk_dia,
            "hartfrequentie": self.hartfrequentie,
            "ademfrequentie": self.ademfrequentie,
            "saturatie": self.saturatie,
            "opmerking": self.opmerking,
        }
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Measurement":
        known = {
            "timestamp",
            "gewicht",
            "spiermassa",
            "vetmassa",
            "vochtbalans",
            "bmi",
            "bloeddruk_sys",
            "bloeddruk_dia",
            "hartfrequentie",
            "ademfrequentie",
            "saturatie",
            "opmerking",
        }
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            timestamp=data.get(
                "timestamp",
                datetime.now(timezone.utc).isoformat(),
            ),
            gewicht=float(data.get("gewicht", 0)),
            spiermassa=float(data.get("spiermassa", 0)),
            vetmassa=float(data.get("vetmassa", 0)),
            vochtbalans=float(data.get("vochtbalans", 0)),
            bmi=float(data.get("bmi", 0)),
            bloeddruk_sys=float(data.get("bloeddruk_sys", 0)),
            bloeddruk_dia=float(data.get("bloeddruk_dia", 0)),
            hartfrequentie=float(data.get("hartfrequentie", 0)),
            ademfrequentie=float(data.get("ademfrequentie", 0)),
            saturatie=float(data.get("saturatie", 0)),
            opmerking=str(data.get("opmerking", "")),
            extra=extra,
        )


# ─────────────────────────────────────────────────────────────────────────────
# MeasurementPeriod — one time-slice (e.g. "Meting 1 (start)")
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MeasurementPeriod:
    """A named time-window that holds an ordered list of measurements."""

    period_id: str
    label: str = ""
    date: str = ""
    measurements: list[Measurement] = field(default_factory=list)

    # ── Mutation ──────────────────────────────────────────────────────────

    def add_measurement(self, data: dict[str, Any]) -> Measurement:
        """Append a new Measurement from a raw data dict and return it."""
        m = Measurement.from_dict(data)
        self.measurements.append(m)
        return m

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_id": self.period_id,
            "label": self.label or self.period_id,
            "date": self.date,
            "measurements": [m.to_dict() for m in self.measurements],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MeasurementPeriod":
        period = cls(
            period_id=data["period_id"],
            label=data.get("label", data["period_id"]),
            date=data.get("date", ""),
        )
        period.measurements = [
            Measurement.from_dict(m) for m in data.get("measurements", [])
        ]
        return period


# ─────────────────────────────────────────────────────────────────────────────
# SimulationState — top-level aggregate
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SimulationState:
    """
    Aggregate root for all simulation periods.

    Holds a dict[period_id -> MeasurementPeriod] so look-ups are O(1)
    regardless of the number of periods.  `period_order` preserves
    insertion order so the UI can render tabs deterministically.

    Scalability: supports 100+ periods with no structural change.
    """

    active_period_id: str | None = None
    periods: dict[str, MeasurementPeriod] = field(default_factory=dict)
    period_order: list[str] = field(default_factory=list)

    # ── Core mutations ────────────────────────────────────────────────────

    def switch_period(
        self,
        period_id: str,
        *,
        label: str = "",
        date: str = "",
    ) -> MeasurementPeriod:
        """
        Set `period_id` as the active period.

        If the period does not exist yet, it is created transparently
        so callers never need to pre-register periods.
        Previous period data is NEVER discarded.
        """
        if period_id not in self.periods:
            self.periods[period_id] = MeasurementPeriod(
                period_id=period_id,
                label=label or period_id.replace("_", " ").title(),
                date=date,
            )
            self.period_order.append(period_id)
        else:
            # Allow updating label/date on an existing period.
            if label:
                self.periods[period_id].label = label
            if date:
                self.periods[period_id].date = date

        self.active_period_id = period_id
        return self.periods[period_id]

    def save_measurement(self, data: dict[str, Any]) -> Measurement | None:
        """
        Append a measurement to the active period.

        Returns None (and is a no-op) if no period is currently active.
        The caller is responsible for setting an active period first.
        """
        if self.active_period_id is None:
            return None
        period = self.periods.get(self.active_period_id)
        if period is None:
            return None
        return period.add_measurement(data)

    def reset(self) -> None:
        """
        Destroy all periods and clear the active pointer.

        Intentionally a full wipe: callers use `switch_period` to
        re-bootstrap the state after a reset.
        """
        self.periods.clear()
        self.period_order.clear()
        self.active_period_id = None

    # ── Serialisation  (storage ↔ model roundtrip) ────────────────────────

    def to_storage_dict(self) -> dict[str, Any]:
        return {
            "active_period_id": self.active_period_id,
            "period_order": self.period_order,
            "periods": {
                pid: period.to_dict()
                for pid, period in self.periods.items()
            },
        }

    @classmethod
    def from_storage_dict(cls, data: dict[str, Any]) -> "SimulationState":
        state = cls(
            active_period_id=data.get("active_period_id"),
            period_order=data.get("period_order", []),
        )
        state.periods = {
            pid: MeasurementPeriod.from_dict(raw)
            for pid, raw in data.get("periods", {}).items()
        }
        return state

    # ── Entity attribute projection ────────────────────────────────────────

    def to_entity_attributes(self) -> dict[str, Any]:
        """
        Return the dict written to sensor.simulation_manager attributes.

        Keeping the active period data inline avoids a second entity look-up
        in the Lovelace card.
        """
        active_data = (
            self.periods[self.active_period_id].to_dict()
            if self.active_period_id and self.active_period_id in self.periods
            else None
        )
        return {
            "active_period_id": self.active_period_id,
            "period_order": self.period_order,
            "total_periods": len(self.periods),
            "periods": {
                pid: period.to_dict()
                for pid, period in self.periods.items()
            },
            # Convenience shortcut for the Lovelace card:
            "active_period_data": active_data,
        }

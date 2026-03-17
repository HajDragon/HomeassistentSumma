"""
Sensor platform for Simulation Manager — MEASUREMENT sensors.
==============================================================

Why this module exists
----------------------
HA's native SQLite recorder only captures long-term statistics for entities
that declare ``state_class = SensorStateClass.MEASUREMENT`` (or TOTAL /
TOTAL_INCREASING).  The main ``sensor.simulation_manager`` entity stores its
state as the *active period ID* (a string), so the recorder ignores it.

This platform creates one numeric SensorEntity per measurement metric.
Because they declare ``SensorStateClass.MEASUREMENT``, the HA recorder:
  1. Writes every state change to the ``states`` table (short-term history).
  2. Compiles hourly mean / min / max into the ``statistics`` table
     (long-term history, survives the default 10-day purge window).

No file I/O or external databases are used — all storage goes through HA's
own SQLite recorder, honouring the HAOS constraint.

Scalability note
----------------
``METRIC_DESCRIPTORS`` is the single source of truth for tracked metrics.
Adding a new body-scan field requires only one new dict entry here; no other
file needs to change.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ── Metric descriptors ─────────────────────────────────────────────────────────
# Extend this list to add new tracked fields — no code elsewhere needs changing.

METRIC_DESCRIPTORS: list[dict[str, Any]] = [
    {
        "key":          "gewicht",
        "name":         "Simulatie Gewicht",
        "unique_id":    f"{DOMAIN}_gewicht",
        "unit":         UnitOfMass.KILOGRAMS,
        "device_class": SensorDeviceClass.WEIGHT,
        "icon":         "mdi:scale-bathroom",
    },
    {
        "key":          "spiermassa",
        "name":         "Simulatie Spiermassa",
        "unique_id":    f"{DOMAIN}_spiermassa",
        "unit":         UnitOfMass.KILOGRAMS,
        "device_class": SensorDeviceClass.WEIGHT,
        "icon":         "mdi:arm-flex",
    },
    {
        "key":          "vetmassa",
        "name":         "Simulatie Vetmassa",
        "unique_id":    f"{DOMAIN}_vetmassa",
        "unit":         UnitOfMass.KILOGRAMS,
        "device_class": SensorDeviceClass.WEIGHT,
        "icon":         "mdi:water-percent",
    },
    {
        "key":          "vochtbalans",
        "name":         "Simulatie Vochtbalans",
        "unique_id":    f"{DOMAIN}_vochtbalans",
        "unit":         "%",
        "device_class": None,
        "icon":         "mdi:water-percent",
    },
    {
        "key":          "bmi",
        "name":         "Simulatie BMI",
        "unique_id":    f"{DOMAIN}_bmi",
        # BMI has no HA-native device class; unit is the physical convention.
        "unit":         "kg/m²",
        "device_class": None,
        "icon":         "mdi:human-male-height",
    },
    {
        "key":          "bloeddruk_sys",
        "name":         "Simulatie Bloeddruk Systolisch",
        "unique_id":    f"{DOMAIN}_bloeddruk_sys",
        "unit":         "mmHg",
        "device_class": None,
        "icon":         "mdi:heart-pulse",
    },
    {
        "key":          "bloeddruk_dia",
        "name":         "Simulatie Bloeddruk Diastolisch",
        "unique_id":    f"{DOMAIN}_bloeddruk_dia",
        "unit":         "mmHg",
        "device_class": None,
        "icon":         "mdi:heart-pulse",
    },
    {
        "key":          "hartfrequentie",
        "name":         "Simulatie Hartfrequentie",
        "unique_id":    f"{DOMAIN}_hartfrequentie",
        "unit":         "bpm",
        "device_class": None,
        "icon":         "mdi:pulse",
    },
    {
        "key":          "ademfrequentie",
        "name":         "Simulatie Ademfrequentie",
        "unique_id":    f"{DOMAIN}_ademfrequentie",
        "unit":         "/min",
        "device_class": None,
        "icon":         "mdi:lungs",
    },
    {
        "key":          "saturatie",
        "name":         "Simulatie Saturatie",
        "unique_id":    f"{DOMAIN}_saturatie",
        "unit":         "%",
        "device_class": None,
        "icon":         "mdi:oxygen",
    },
]


# ── Platform entry-point ───────────────────────────────────────────────────────

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """
    Called by HA after ``discovery.async_load_platform`` fires from __init__.py.

    Reads the shared SimulationState reference from hass.data, creates one
    SimulationMeasurementSensor per descriptor, then stores a key→entity
    mapping back into hass.data so _commit() can call async_write_ha_state()
    on each sensor after every mutation.
    """
    sim_state = hass.data[DOMAIN]["state"]

    entities: list[SimulationMeasurementSensor] = [
        SimulationMeasurementSensor(descriptor, sim_state)
        for descriptor in METRIC_DESCRIPTORS
    ]

    # Register entity references for push-updates from __init__._commit().
    hass.data[DOMAIN]["measurement_sensors"] = {
        entity.metric_key: entity for entity in entities
    }

    async_add_entities(entities, update_before_add=True)
    _LOGGER.info(
        "Simulation Manager sensor platform: registered %d MEASUREMENT sensors.",
        len(entities),
    )


# ── Sensor entity ──────────────────────────────────────────────────────────────

class SimulationMeasurementSensor(SensorEntity):
    """
    A single numeric sensor for one body-scan metric in the active period.

    State class
    -----------
    ``SensorStateClass.MEASUREMENT`` instructs the HA recorder to:
      • Store every state change in ``states`` (visible in history graphs).
      • Compile statistics (mean / min / max) in ``statistics`` for long-term
        storage — data is never auto-purged the way raw state rows are.

    Push model
    ----------
    ``_attr_should_poll = False`` because values are pushed from __init__.py's
    _commit() via ``async_write_ha_state()``.  This avoids unnecessary polling
    and keeps state changes atomic with the underlying data store.

    Forward compatibility
    ---------------------
    ``native_value`` reads from the Measurement dataclass fields first, then
    falls back to the ``extra`` dict, so custom metrics added via the
    ALLOW_EXTRA service schema are automatically surfaced if a descriptor is
    added to METRIC_DESCRIPTORS.
    """

    _attr_state_class  = SensorStateClass.MEASUREMENT
    _attr_should_poll  = False

    def __init__(
        self,
        descriptor: dict[str, Any],
        sim_state: Any,
    ) -> None:
        self._sim_state: Any = sim_state
        self.metric_key: str = descriptor["key"]
        self._attr_name                       = descriptor["name"]
        self._attr_unique_id                  = descriptor["unique_id"]
        self._attr_native_unit_of_measurement = descriptor["unit"]
        self._attr_device_class               = descriptor.get("device_class")
        self._attr_icon                       = descriptor["icon"]

    @property
    def native_value(self) -> float | None:
        """
        Return the most recent measurement value for the active period.

        Returns None when no active period is set or when the active period
        has no measurements yet.  The recorder treats None as "unavailable"
        and does not write a statistics row for that interval.
        """
        active_id: str | None = self._sim_state.active_period_id
        if not active_id:
            return None

        period = self._sim_state.periods.get(active_id)
        if period is None or not period.measurements:
            return None

        latest = period.measurements[-1]

        # Primary lookup: fixed dataclass fields.
        raw = getattr(latest, self.metric_key, None)
        # Fallback: extra dict supports forward-compatible custom metrics.
        if raw is None:
            raw = latest.extra.get(self.metric_key)

        return float(raw) if raw is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the active period label alongside the numeric value."""
        active_id = self._sim_state.active_period_id
        if not active_id:
            return {}
        period = self._sim_state.periods.get(active_id)
        return {
            "active_period_id":    active_id,
            "active_period_label": (
                period.label if period and period.label else active_id
            ),
        }

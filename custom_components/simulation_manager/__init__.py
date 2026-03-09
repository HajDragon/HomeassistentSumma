"""
Simulation Manager — Home Assistant Custom Integration
======================================================

Responsibilities
----------------
1. Load persisted state from `homeassistant.helpers.storage.Store` on startup.
2. Register three HA services:
       simulation_manager.switch_period
       simulation_manager.save_measurement
       simulation_manager.reset_simulation
3. After every mutation, persist the new state AND push it to
   `sensor.simulation_manager` so the Lovelace card receives a reactive update
   via WebSocket (no polling).

State lives entirely in `SimulationState` (pure-Python model).
This module is the thin orchestration layer between HA and the model.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_ACTIVE_PERIOD,
    DOMAIN,
    ENTITY_ID,
    NO_ACTIVE_PERIOD,
    SERVICE_RESET_SIMULATION,
    SERVICE_SAVE_MEASUREMENT,
    SERVICE_SWITCH_PERIOD,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .models import SimulationState

_LOGGER = logging.getLogger(__name__)

# ── Service schemas ────────────────────────────────────────────────────────────

SWITCH_PERIOD_SCHEMA = vol.Schema(
    {
        vol.Required("period_id"): cv.string,
        vol.Optional("label"): cv.string,
        vol.Optional("date"): cv.string,
    }
)

SAVE_MEASUREMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("gewicht"):    vol.Coerce(float),
        vol.Optional("spiermassa"): vol.Coerce(float),
        vol.Optional("vetmassa"):   vol.Coerce(float),
        vol.Optional("bmi"):        vol.Coerce(float),
        vol.Optional("timestamp"):  cv.string,
    },
    extra=vol.ALLOW_EXTRA,  # Forward-compatible: pass any custom metric
)

# No fields needed for reset — schema is intentionally empty.
RESET_SIMULATION_SCHEMA = vol.Schema({})


# ── Integration entry-point ────────────────────────────────────────────────────

async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the Simulation Manager integration from configuration.yaml."""
    store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    raw = await store.async_load()

    state: SimulationState = (
        SimulationState.from_storage_dict(raw) if raw else SimulationState()
    )

    # Stash references so helpers defined below can share them.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["state"] = state
    hass.data[DOMAIN]["store"] = store

    # ── Shared persist + publish helper ─────────────────────────────────────

    async def _commit() -> None:
        """Persist state to disk and push a fresh snapshot to the HA state machine."""
        await store.async_save(state.to_storage_dict())
        hass.states.async_set(
            ENTITY_ID,
            state.active_period_id or NO_ACTIVE_PERIOD,
            state.to_entity_attributes(),
        )
        _LOGGER.debug(
            "State committed. active=%s periods=%d",
            state.active_period_id,
            len(state.periods),
        )

    # ── Service: switch_period ───────────────────────────────────────────────

    async def handle_switch_period(call: ServiceCall) -> None:
        """
        Switch the active period. Creates the period when it does not exist.
        All previously stored measurements for every period are preserved.
        """
        period_id: str = call.data["period_id"]
        label: str = call.data.get("label", "")
        date: str = call.data.get("date", "")

        state.switch_period(period_id, label=label, date=date)
        await _commit()
        _LOGGER.info("Switched to period '%s'.", period_id)

    # ── Service: save_measurement ────────────────────────────────────────────

    async def handle_save_measurement(call: ServiceCall) -> None:
        """
        Append a measurement to the active period.
        Aborts with a warning if no active period has been set.
        """
        if state.active_period_id is None:
            _LOGGER.warning(
                "save_measurement called but no active period is set. "
                "Call simulation_manager.switch_period first."
            )
            return

        data = dict(call.data)
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        state.save_measurement(data)
        await _commit()
        _LOGGER.info(
            "Measurement saved to period '%s'.", state.active_period_id
        )

    # ── Service: reset_simulation ────────────────────────────────────────────

    async def handle_reset_simulation(call: ServiceCall) -> None:
        """Wipe all period data and reset the active-period pointer to None."""
        state.reset()
        await _commit()
        _LOGGER.info("Simulation state has been fully reset.")

    # ── Register services ─────────────────────────────────────────────────────

    hass.services.async_register(
        DOMAIN,
        SERVICE_SWITCH_PERIOD,
        handle_switch_period,
        schema=SWITCH_PERIOD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_MEASUREMENT,
        handle_save_measurement,
        schema=SAVE_MEASUREMENT_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_SIMULATION,
        handle_reset_simulation,
        schema=RESET_SIMULATION_SCHEMA,
    )

    # Publish the restored/initial state immediately so the entity exists
    # right after boot (avoids "entity not found" on the first dashboard load).
    await _commit()

    _LOGGER.info(
        "Simulation Manager started. Loaded %d period(s); active: %s.",
        len(state.periods),
        state.active_period_id or "none",
    )
    return True

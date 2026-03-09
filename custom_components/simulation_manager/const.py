"""Constants for the Simulation Manager integration."""

DOMAIN = "simulation_manager"

# Persistent storage
STORAGE_KEY = "simulation_manager_state"
STORAGE_VERSION = 1

# Entity
ENTITY_ID = f"sensor.{DOMAIN}"

# Attribute keys written to the entity state
ATTR_ACTIVE_PERIOD = "active_period_id"
ATTR_PERIODS = "periods"
ATTR_PERIOD_ORDER = "period_order"
ATTR_TOTAL_PERIODS = "total_periods"

# Service names
SERVICE_SWITCH_PERIOD = "switch_period"
SERVICE_SAVE_MEASUREMENT = "save_measurement"
SERVICE_RESET_SIMULATION = "reset_simulation"

# Default / sentinel values
NO_ACTIVE_PERIOD = "none"

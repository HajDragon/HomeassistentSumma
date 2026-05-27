 # Developer Documentation
 
 This document is for engineers taking over this Home Assistant codebase. It describes the current architecture, how the custom integration and Lovelace assets fit together, and how to handle the legacy bootstrap scripts safely.
 
 ## Project Overview
 
 This repository powers an educational Smart Room on Home Assistant OS running on HA Green. The main scenario is the Mevrouw Goedheid cardiac monitoring simulation, which presents a patient timeline with multiple measurement periods, live helper entities, and a teacher-facing dashboard.
 
 The architecture is deliberately split into three layers:
 
 - Home Assistant configuration in [config/](../config)
 - Custom backend integrations in [custom_components/](../custom_components)
 - Frontend assets in [www/](../www)
 
 The simulation manager is the central piece. It stores period state, publishes entity attributes for Lovelace, and exposes services that the dashboard and scripts call. The UI now drives day-to-day changes through Home Assistant helpers and scripts inside the UI. File-based deployment scripts remain in the repo for first-time bootstrap and reconstruction only.
 
 ## Directory Responsibilities
 
 ### `config/`
 
 This folder contains the Home Assistant YAML configuration that defines the simulation scenario.
 
 - [config/packages/mevrouw_goedheid_simulation.yaml](../config/packages/mevrouw_goedheid_simulation.yaml) defines the helper entities, template sensors, and UI-facing scripts for the simulation.
 - [config/dashboards/](../config/dashboards) contains the teacher dashboards. The simulation dashboard is built from modular row fragments in [config/dashboards/simulation/](../config/dashboards/simulation) and can also be supplied as a full file at [config/dashboards/simulatie_goedheid.yaml](../config/dashboards/simulatie_goedheid.yaml).
 - [config/dashboards/overview_dashboard.yaml](../config/dashboards/overview_dashboard.yaml) is the broader overview dashboard for the room.
 
 These dashboards are now primarily UI-managed in Home Assistant. The YAML files are still useful for initial setup, reproducible bootstrap, and understanding the intended structure.
 
 ### `custom_components/`
 
 This folder contains the Python integrations that extend Home Assistant.
 
 - [custom_components/simulation_manager/](../custom_components/simulation_manager) is the core integration for simulation state, service registration, persistence, and measurement sensors.
 - [custom_components/photo_scanner/](../custom_components/photo_scanner) scans and uploads images into the HA `www/photos` directory and updates `input_select.available_photos`.
 
 The simulation manager persists `SimulationState` via Home Assistant storage, registers the services `simulation_manager.switch_period`, `simulation_manager.save_measurement`, and `simulation_manager.reset_simulation`, and pushes state to `sensor.simulation_manager` after every mutation so the frontend updates immediately.
 
 ### `www/`
 
 This folder contains static assets that Home Assistant serves under `/local/`.
 
 - [www/simulation-period-card/](../www/simulation-period-card) contains the custom Lovelace card that renders the simulation periods and measurement table.
 - [www/photo_uploader/](../www/photo_uploader) contains the frontend card for uploading photos to the `photo_scanner` integration.
 
 The simulation card is reactive: it reads the single `sensor.simulation_manager` entity and its attributes instead of polling separate sources. That is the key design choice to keep the UI synchronized with the backend state.
 
 ### `scripts/`
 
 This folder holds developer-machine utilities for bootstrap, deployment, and one-time data seeding.
 
 - [scripts/build_simulation_dashboard.py](../scripts/build_simulation_dashboard.py) merges modular dashboard row files into a single Lovelace YAML file.
 - [scripts/push_dashboard.py](../scripts/push_dashboard.py) pushes the current dashboards to Home Assistant through the WebSocket Lovelace API.
 - [scripts/deploy_simulation_manager.py](../scripts/deploy_simulation_manager.py) guides installation of the custom integration and Lovelace resource and can seed demo periods.
 - [scripts/seed_periods.py](../scripts/seed_periods.py) seeds the March 2026 simulation periods directly into the integration.
 
 These scripts run on a developer machine, not on HAOS itself.
 
 ## Environment And Dependencies
 
 The repository does not commit a real `.env` file. Instead, [.env.example](../.env.example) documents the keys expected by the scripts.
 
 Required keys:
 
 - `HA_BASE_URL`: Base URL of the Home Assistant instance, defaulting to `http://homeassistant.local:8123`
 - `HA_TOKEN`: Long-lived access token for API and WebSocket calls
 
 The script dependencies in [requirements.txt](../requirements.txt) are:
 
 - `python-dotenv` for loading environment variables from `.env`
 - `requests` for REST-based API calls
 - `websocket-client` for Home Assistant WebSocket API calls
 - `pyyaml` for dashboard YAML handling
 - `influxdb-client` for time-series refresh tooling that interacts with InfluxDB
 
 ## Integration Design
 
 The simulation manager integration is structured for testability and predictable state flow.
 
 - [custom_components/simulation_manager/models.py](../custom_components/simulation_manager/models.py) contains pure Python data models with no Home Assistant imports.
 - [custom_components/simulation_manager/__init__.py](../custom_components/simulation_manager/__init__.py) loads persisted state, registers services, guarantees default periods exist, and writes state back to Home Assistant storage.
 - [custom_components/simulation_manager/sensor.py](../custom_components/simulation_manager/sensor.py) exposes measurement sensors with `SensorStateClass.MEASUREMENT` so Home Assistant can record history and long-term statistics.
 - [custom_components/simulation_manager/services.yaml](../custom_components/simulation_manager/services.yaml) documents the service schemas for UI and developer use.
 
 The important runtime behavior is this: every state mutation updates both persistent storage and `sensor.simulation_manager`. The Lovelace card subscribes to that entity and therefore updates without polling.
 
 The data model is intentionally extensible. `Measurement` stores known measurement fields plus an `extra` dictionary, and the service schema accepts additional keys. If you add a new metric, you usually update the model, the service schema, and the metric descriptor list in `sensor.py`.
 
 ## Legacy Deployment Scripts
 
 The four scripts below are historically important. They were originally used as part of a scripted deployment flow that pushed YAML-style configuration into Home Assistant and, in the older workflow, paired with webhook-driven automation. The project has since moved to a UI-first operating model for adding, editing, or removing functionality.
 
 ### Warning
 
 **Do not run these scripts on the live Home Assistant environment unless you are bootstrapping a brand-new instance or rebuilding the project from scratch.**
 
 They can overwrite dashboard definitions, reseed simulation periods, reset existing state, and replace UI-managed configuration. That is appropriate only when you are creating the environment fresh and want the repo to reconstruct it from source.
 
 ### `scripts/deploy_simulation_manager.py`
 
 This is the bootstrap script for the simulation integration and the simulation-period Lovelace card.
 
 What it does:
 
 - Prints the manual copy instructions for [custom_components/simulation_manager/](../custom_components/simulation_manager) and [www/simulation-period-card/](../www/simulation-period-card)
 - Registers the Lovelace resource `/local/simulation-period-card/simulation-period-card.js`
 - Verifies that `sensor.simulation_manager` exists after restart
 - Optional seed mode populates the four Mevrouw Goedheid periods
 
 How it works:
 
 - Uses `python-dotenv` to read `HA_BASE_URL` and `HA_TOKEN`
 - Uses REST calls to Home Assistant for resource registration and entity checks
 - Calls the simulation manager services `reset_simulation`, `switch_period`, and `save_measurement` when seeding data
 
 Why it is legacy:
 
 - It assumes the repo is being copied into a fresh HA config tree
 - It is a setup helper, not a day-to-day operational tool
 
 ### `scripts/push_dashboard.py`
 
 This script pushes dashboard definitions to Home Assistant over the WebSocket Lovelace API.
 
 What it does:
 
 - Authenticates to Home Assistant over WebSocket
 - Saves an overview dashboard, a cameras dashboard, and a health dashboard
 - Creates the cameras dashboard entry when needed
 - Uses the current dashboard YAML embedded in the script as the payload source
 
 How it works:
 
 - Sends `lovelace/config`, `lovelace/dashboards/list`, `lovelace/dashboards/create`, and `lovelace/config/save` messages
 - Relies on a live HA session token and an accessible `HA_BASE_URL`
 
 Why it is legacy:
 
 - It is a scripted way to push dashboard state into Home Assistant
 - The current project direction is to manage dashboards in the UI rather than re-pushing them from a local file on every change
 
 ### `scripts/seed_periods.py`
 
 This script seeds the eight March 2026 measurement periods into `simulation_manager`.
 
 What it does:
 
 - Connects to the Home Assistant WebSocket API
 - Resets the simulation state
 - Creates or activates each period in order
 - Saves the measurement payload for each March 2026 data point
 - Leaves the simulation on `period_1`
 
 How it works:
 
 - Builds a queue of service calls for `simulation_manager.reset_simulation`, `simulation_manager.switch_period`, and `simulation_manager.save_measurement`
 - Authenticates with the long-lived token from `.env`
 - Sends each call sequentially and waits for the result before continuing
 
 Why it is legacy:
 
 - It is a bulk data seeding tool for reconstructing the lesson timeline
 - Running it on a live environment will overwrite the current simulation state and is therefore risky
 
 ### `scripts/build_simulation_dashboard.py`
 
 This script builds a monolithic Lovelace YAML file from modular row fragments.
 
 What it does:
 
 - Reads the row files in [config/dashboards/simulation/](../config/dashboards/simulation)
 - Combines them into [config/dashboards/simulation_dashboard.yaml](../config/dashboards/simulation_dashboard.yaml)
 - Falls back to [config/dashboards/simulatie_goedheid.yaml](../config/dashboards/simulatie_goedheid.yaml) if the full dashboard already exists
 
 How it works:
 
 - Concatenates the dashboard header with each row fragment
 - Preserves the current dashboard structure in a single file that Home Assistant can parse
 
 Why it is legacy:
 
 - It exists to support file-based dashboard reconstruction
 - In normal operation, dashboard changes should be made in the Home Assistant UI instead of regenerating and reapplying YAML
 
 ## Developer Onboarding
 
 For a new developer, the safest workflow is UI-first.
 
 1. Open Home Assistant and confirm the existing dashboards and helpers before editing anything.
 2. Verify the integration is loaded by checking for `sensor.simulation_manager` and the simulation services in Developer Tools.
 3. If you need to modify the integration, edit the files in [custom_components/simulation_manager/](../custom_components/simulation_manager) and reload or restart Home Assistant as required.
 4. If you need to modify the simulation UI, update the helper entities in [config/packages/mevrouw_goedheid_simulation.yaml](../config/packages/mevrouw_goedheid_simulation.yaml) and adjust the Lovelace card in [www/simulation-period-card/](../www/simulation-period-card).
 5. Use the Home Assistant UI to add, remove, or reorder dashboard content whenever possible.
 6. Treat the scripts in [scripts/](../scripts) as bootstrap or reconstruction tools only.
 
 The practical rule is simple: if you are changing an existing live setup, use the UI. If you are rebuilding the environment from scratch, the scripts can help you reconstruct the baseline.
 
 ## Implementation Notes
 
 - Add new measurement fields in `models.py` first, then expose them in `sensor.py` and the service schema.
 - Keep entity references dynamic and helper-driven. Avoid hardcoding entity IDs that can change when devices are replaced or the room is repurposed.
 - Preserve the push model. The Lovelace card should continue consuming the single simulation entity instead of polling separate sources.
 - Keep static assets in `www/` and register them as Home Assistant resources under `/local/`.
 - Do not add OS-level dependencies or host-level package installs. This project is designed to run within HAOS boundaries.
 
## Light Automation
- Light automation is handled by two main components, Light Calender entity and and the light automation, light automation takes the calender events (each day from 8-17) as a trigger and turns on the lights for the duration of each calender event.
    


 ## Reference Files
 
 - [README.md](../README.md)
 - [docs/README_ADMINS.md](README_ADMINS.md)
 - [config/packages/mevrouw_goedheid_simulation.yaml](../config/packages/mevrouw_goedheid_simulation.yaml)
 - [custom_components/simulation_manager/__init__.py](../custom_components/simulation_manager/__init__.py)
 - [custom_components/simulation_manager/models.py](../custom_components/simulation_manager/models.py)
 - [custom_components/simulation_manager/sensor.py](../custom_components/simulation_manager/sensor.py)
 - [custom_components/photo_scanner/__init__.py](../custom_components/photo_scanner/__init__.py)
 - [scripts/deploy_simulation_manager.py](../scripts/deploy_simulation_manager.py)
 - [scripts/push_dashboard.py](../scripts/push_dashboard.py)
 - [scripts/seed_periods.py](../scripts/seed_periods.py)
 - [scripts/build_simulation_dashboard.py](../scripts/build_simulation_dashboard.py)

# Add Casus Without UI Changes

This guide explains how to add a new simulation case through the backend only.
The simulation dashboard stays unchanged because it reads generic Active Patient entities.

## Developer Documentation

Architecture summary:
- Selector entity: input_select.active_simulation_patient
- Bridge logic: script.active_patient_apply_profile
- Generic UI-facing sensors: sensor.active_patient_*
- Conditional UI toggles: input_boolean.active_patient_supports_*

To add Casus 3:
1. Open config/packages/active_patient_simulation.yaml.
2. Under input_select.active_simulation_patient options, add the new patient display name.
3. In script.active_patient_apply_profile, extend patient_catalog with a new object for that exact name.
4. Fill only generic keys used by the bridge:
   - age
   - gender
   - primary_condition
   - case_focus
   - bp
   - heart_rate
   - temperature
   - skin_triage
   - supports_cardiac
   - supports_skin_triage
   - supports_temperature
5. Keep values assignment-free in Lovelace; only update this catalog.
6. Restart Home Assistant or reload YAML/script helpers.
7. Select the new patient in input_select.active_simulation_patient.
8. Confirm sensor.active_patient_name and related generic sensors update correctly.
9. Save one measurement through script.active_patient_save_measurement to verify timeline storage.

Validation checklist:
- No dashboard YAML edits were required.
- Cardiac block appears only when supports_cardiac is true.
- Skin/temperature blocks appear only when matching toggles are true.
- simulation_manager timeline row contains the new patient metadata.

## Administrator Documentation

Goal: Add a new case profile from the configuration layer and use it in the dashboard.

1. Add the new patient name to Active Simulation Patient options in the package file.
2. Add the patient profile values in the patient catalog section.
3. Reload scripts and template entities from Home Assistant settings, or restart Home Assistant.
4. Open the simulation dashboard.
5. Choose the new patient from Active Patient.
6. Check that profile text and relevant vital cards appear automatically.
7. Use Save Measurement once to confirm the timeline records the new case.

Operational rule:
- Do not edit the dashboard layout when creating a new case.

## Teacher Documentation

What to do when you receive a new assignment case:
1. Open the simulation dashboard.
2. Select the patient from the Active Patient dropdown.
3. Confirm the summary card shows the correct age, focus, and condition.
4. If the assignment is blood pressure focused, use the cardiac card.
5. If the assignment is skin/fever focused, use the skin and temperature cards.
6. Choose the phase and date.
7. Save the measurement to store the lesson moment in the timeline.

What not to do:
- Do not change dashboard code for new cases.
- Do not duplicate cards per patient.

Result:
- One dashboard supports all existing and future cases through patient selection only.
# Zorg Kamer Docenten Documentatie

## Inleiding

Welcome to this project ! the zorg kamer project is made to simulate how a nurse could care for a patient (in our case an elderly person) using devices and sensors that are installed accros the room. It exists so that the studentes can see how technology can make it so that basic caring could be done from far away using smart sensors and a monitoring dashboard made with homeassistant for ease of use.

There are things that are intentionally left to do with hand and things that are automated, I will provide a step by step guide on them to ensure that the teachers would have a good understanding of what to expect vs what not to.

# What sensors are installed in the room?

there are a handfull of sensors iinstalled in the room that im going to list below:

# Static Sensors

- `patient_name` – Patient name in the scenario.
- `patient_age` – Age used for scenario context.
- `patient_gender` – Gender for scenario context.
- `patient_case_focus` – Current clinical case point (example: heart failure focus).
- `patient_skin_triage` – Skin observation status (light/normal/alert).
- `sensor.active_patient_temperature` – body temperature from the patient record.
- `sensor.active_patient_bp` – base blood pressure value for the active patient.
- `sensor.active_patient_heart_rate` – base heart rate in bpm.

# Health monitoring sensors

- `.gewicht` – Current measured weight in the simulation.
- `.gewicht` – Weight shown on the dashboard.
- `.spiermassa` – Muscle mass shown value for the current session.
- `.vetmassa` – Fat mass shown value for the current session.
- `.bmi` – Body mass index value shown.
- `.vochtbalans` – Fluid balance shown value.
- `.bloeddruk` – Combined blood pressure display string (SYS/DIA).
- `.hartfrequentie` – Display heart rate value.
- `.ademfrequentie` – Display respiratory rate.
- `.saturatie` – Display blood oxygen saturation.
- `.bloedtempratuur` – Display blood temperature.
- `Val Detectie` – Fall detection status.

# Security sensors

- `rookmelder` – Smoke detector status.
- `DoorSensor` – Door open/close status.
- `SOS Wabdknop` – Emergency button status.
- `Person detection` – Presence detection status.
- `Beweging Sensor` – Motion detection status.
- `Camera's` - achter en voor de kamer.

Er zijn andere sensoren die zijn geïnstalleerd maar deze zijn de belangrijkste en meest relevante voor jullie te weten, er zijn ook nog een aantal sensoren die worden gebruikt voor het monitoren van de apparaten zelf zoals batterij niveau en dergelijke maar deze zijn niet relevant voor de les en worden dus niet besproken.

# How to access the dashboard?

1. Open a web browser on your computer or tablet.(Dont use bing)
2. Open the URL: `https://homeassistant.local:8123`.
3. Log in with the credentials provided by your technical team.
4. Once logged in, you will see the dashboard with various cards displaying patient information and sensor data.

## What is in the dashboard?
The dashboard is designed to provide an overview of the patient's status and the various sensors in the room. we are talking about multiple dahsboards that are designed to show different information but the main one is the Simulatie dashboard which shows the following:

### Overview
- A clock-weather card showing the current weather conditions in Eindhoven (for simulation context).
- A set of metric cards displaying key patient vitals (weight, blood pressure, heart rate, respiratory rate, SpO₂).

- A Card showing wellness and health information such as heartrate, blood pressure, weight, SpO2, etc.

- A card showing live security data such as motion detection, door status, fall detection, and smoke detection.

- A card showing current Network Status of the Router in the room.

- A card showing extended security options and controls such as the emergency button status and siren control.


### Cameras
- A card showing the live feed from the cameras installed in the room .
- A card showing Live detection status of the status detection sensor.
- A card called PTZ bediening which is used to control the cameras and move them around to see different angles of the room. when you click on a direction, you also have to click on the stop button at the center to avoid to much rotation.

- A card showing Schakelaars & Instellingen which is used to control all the camera settings such as Audio opnemen, Bewegingsdetectie, FTP upload, etc.

- You can switch between the voordeur en achterkant camera using the dropdown menu at the top of the card with a camera logo, they share the exact same interface.


### Kaart
- A card showing the current Location of the patient. 

### Maating
- A card showing the current weight, muscle mass, fat mass, BMI, and fluid balance of the patient. They are Synced automatically via the Withings application, the flow is as followed:
1. the person performs a measurement via on of the Withings devices (scale, blood pressure(BpmConnect), SmartWatch, beamO etc.) (SleepAnaluzer is excluded from this flow as it is used for sleep monitoring only).

2. Follow the instuctions carefully on the device to ensure that the measurement is successful.

3. The measurement is then automatically synced to the Withings app and then pushed to the Home Assistant dashboard via the Withings integration. You will first see it on the app and then it will appear on the dashboard within a few seconds. If not so you need to  follow the guide in the troubleshooting section to troubleshoot the issue.

### simulatie
- In the simulatie-dashboard you will see a combination of 7 big and small cards with different information that we will go one by one:
- the first card is called Databron en Simulatiefase, it shows the current data source for the simulation (either live or simulated) and the current phase of the clinical case (for example: Meting 1,2,3 ....). This is used to provide time context for the scenario being simulated.
- the second card is called Huidige meetwaarden, it shows the current measured values for the patient such as weight, blood pressure, heart rate, adenfrequentie, Spo02, and bloedtempratuur, these values are updated in real time as the measurements are taken and synced via the Withings integration or they can be inserted manually by the teacher via the "Simulatie Invoer" card.
- the third card is called Simulatie Invoer, it is used by the teacher to manually insert values for the patient in case they want to simulate a specific scenario or if the Withings integration is not working for some reason. it has input fields for weight, blood pressure, heart rate, adenfrequentie, Spo02, and bloedtempratuur. once the values are inserted and the "Sla huidige meting op" button is clicked, the values will be updated on the "Huidige meetwaarden" card and also pushed to the `sensor.simulation_manager` sensor which is used to manage the simulation state and trigger automations based on the input values. It will also update the chart on the Cardiale monitoring card and the field below it which shows the current vlaues stored in each measurement point for the current session.
-The fourth card is called Cardiale monitoring, it shows a chart with the historical values for Gewicht, Spiermassa, vetmassa, vochtbalans, BMI, Bloeddruk(sysatolisch) hartfrequentie, ademfrequentie en saturatie for the current session. this is used to provide a visual representation of how the patient's condition is evolving over time during the simulation.
Each value in the chart can be selected to be seen individually or all together, this is done by clicking on the value name in the legend at the bottom of the chart. The values are updated in real time as new measurements are taken and synced via the Withings integration or inserted manually via the "Simulatie Invoer" card.
below the chaer you will find the periodic table which shows the current values stored in each measurement point for the current session, this is used to provide a quick overview of the current state of the patient based on the input values

-Below the table you will find **meting toevoegeb aan actieve periode** this is an **alternative** way to insert values for the patient just as the simulatie invoer card, it has the same input fields and works exactly the same way but its used to insert a value to the active seleted period so the period shall be chosen by the choosing between meting 1,2,3,4,5,6,7,8 on top of the chart and then inserting the values and clicking on "Opslaan" button, this will update the chart and the field below it with the new values for the selected period. this is used to simulate a scenario where the patient condition changes over time and you want to show how it evolves during the simulation.
Note that when you are adding a new value to table the new value's will be presented with an orange color on top of the currently active values in the table.

- on the next card you will fund Patientprofiel, it shows the static information about the patient such as name, age, anamnese, monitoring focus devices etc,
below it you will find the patientfoto dropdown menu and an option to browse and upload a new photo for the patient or really anyother context, you can upload a photo using the browse option and by clicking on the vreniew fotogalerij button to refresh the photos directry and make the photo appear in the dropdown menu.




### Cardiale monitoring
- This card shows a chart with the historical values for **Gewicht**, **bloeddruk**, **hartfrequentie**, **ademfrequentie**, **saturatie**, **opmerkingen** en **ademfrequentie** for the current session. its based on the assigment that has been given to me this is used to provide a visual representation of how the patient's condition is evolving over time during the simulation.

### observatie progressie
- the last card is called observatie progressie, it gives a visual representation of the patient's skin triage status over time, it shows a timeline with the different triage statusesd the time they were recorded. this is used to show how the patient's condition is evolving over time during the simulation.


#### Troubleshooting
The homeassistant dashboard is designed to be used by people who are not tech savvy, also troubleshooting problems is not a big deal but you need to follow the steps carefully to ensure that you can fix the issue without any problems.

1. Check if the Withings integration is still active in Home Assistant. You can do this by going to **Settings → Devices & Services → Integrations** and looking for the Withings integration. If it is not there, you need to set it up again. contact your technical team for help with this.

2. Click on the withings intergration, it will open a page where you will see all the devices that are connected to it, I assume that the devices are already setup by your technical team, you have to click on the 3 dots on top of each dropdown menu (dont mistake it with 3 dots on the right of the device name) and then click on "Reload" to force a sync with the Withings app.

3. If the above steps did not work, you can try to restart Home Assistant. You can do this by going to **Settings → System → Restart**. This will restart Home Assistant and hopefully fix any issues with the Withings integration.
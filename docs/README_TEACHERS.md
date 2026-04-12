# Zorgkamer - Docentenhandleiding

## Lescontext

Welkom bij dit project. Het zorgkamer-project simuleert hoe een verpleegkundige voor een patient (in ons geval een oudere) kan zorgen met behulp van apparaten en sensoren die in de kamer zijn geinstalleerd.

Het project is ontwikkeld zodat studenten kunnen zien hoe technologie basiszorg op afstand mogelijk maakt. Dit gebeurt via slimme sensoren en een monitoring-dashboard in Home Assistant.

Sommige handelingen moeten bewust handmatig worden uitgevoerd, terwijl andere volledig geautomatiseerd zijn. Deze handleiding legt stap voor stap uit wat docenten wel en niet kunnen verwachten.

## Welke sensoren zijn in de kamer geinstalleerd?

Hieronder staan de belangrijkste sensoren.

### Statische sensoren


- `patient_name` - Patientnaam in het scenario.
- `patient_age` - Leeftijd voor de context van het scenario.
- `patient_gender` - Geslacht voor de context van het scenario.
- `patient_case_focus` - Huidig klinisch focuspunt (bijvoorbeeld focus op hartfalen).
- `patient_skin_triage` - Status van huidobservatie (licht/normaal/waarschuwing).
- `sensor.active_patient_temperature` - Lichaamstemperatuur uit het patientendossier.
- `sensor.active_patient_bp` - Basiswaarde van de bloeddruk voor de actieve patient.
- `sensor.active_patient_heart_rate` - Basis hartslag in bpm.

### Gezondheidsmonitoring sensoren

- `.gewicht` - Huidig gemeten gewicht in de simulatie.
- `.gewicht (Dashboard)` - Gewicht weergegeven op het dashboard.
- `.spiermassa` - Weergegeven waarde van de spiermassa voor de huidige sessie.
- `.vetmassa` - Weergegeven waarde van de vetmassa voor de huidige sessie.
- `.bmi` - Weergegeven Body Mass Index (BMI)-waarde.
- `.vochtbalans` - Weergegeven waarde van de vochtbalans.
- `.bloeddruk` - Gecombineerde weergave van de bloeddruk (SYS/DIA).
- `.hartfrequentie` - Weergave van de hartslag.
- `.ademfrequentie` - Weergave van de ademhalingsfrequentie.
- `.saturatie` - Weergave van de zuurstofsaturatie in het bloed.
- `.bloedtempratuur` - Weergave van de bloedtemperatuur.
- `Val Detectie` - Status van de valdetectie.

### Beveiligingssensoren

- `rookmelder` - Status van de rookmelder.
- `DoorSensor` - Status van de deur (open/dicht).
- `SOS Wandknop` - Status van de noodknop.
- `Person detection` - Status van de aanwezigheidsdetectie.
- `Beweging Sensor` - Status van de bewegingsdetectie.
- `Camera's` - Achter en voor in de kamer.

Er zijn nog andere sensoren geinstalleerd, maar bovenstaande zijn het meest relevant voor de lessen. Daarnaast bestaan er ook sensoren voor apparaatmonitoring (zoals batterijniveau), maar die zijn niet nodig voor deze handleiding.

## Hoe krijg ik toegang tot het dashboard?

1. Open een webbrowser op je computer of tablet (gebruik geen Bing).
2. Ga naar: <https://homeassistant.local:8123>
3. Log in met de inloggegevens van het technische team.
4. Na inloggen zie je het dashboard met kaarten voor patientinformatie en sensorgegevens.

## Wat staat er op het dashboard?

Het dashboard geeft een overzicht van de status van de patient en de sensoren in de kamer. Er zijn meerdere dashboards, maar het belangrijkste is het Simulatie-dashboard.



<img src="./Photos/Overview.png" alt="Simulatie Dashboard" width="400"/>


### Overzicht (Overview)

- Een klok-weerkaart met de huidige weersomstandigheden in Eindhoven (voor simulatiecontext).
- Een set metrische kaarten met vitale functies (gewicht, bloeddruk, hartslag, ademhalingsfrequentie, SpO2).
- Een kaart met welzijns- en gezondheidsinformatie (zoals hartslag, bloeddruk en gewicht).
- Een kaart met live beveiligingsgegevens (bewegingsdetectie, deurstatus, valdetectie, rookdetectie).
- Een kaart met de netwerkstatus van de router in de kamer.
- Een kaart met uitgebreide beveiligingsopties (zoals noodknopstatus en sirenebediening).

---

<img src="./Photos/camera.png" alt="Simulatie Dashboard" width="400"/>

### Camera's

- Een kaart met live videobeelden van de camera's in de kamer.
- Een kaart met live detectiestatus van de detectiesensor.
- Een kaart `PTZ bediening` om camera's te draaien en te richten.
- Klik na een richting ook op de stopknop in het midden, zodat de camera niet te ver doordraait.
- Een kaart `Schakelaars & Instellingen` voor camera-opties zoals audio opnemen, bewegingsdetectie en FTP-upload.
- Wisselen tussen voor- en achterkantcamera kan via het uitklapmenu met cameralogo bovenaan de kaart.

---

<img src="./Photos/kaart.png" alt="Simulatie Dashboard" width="400"/>

### Kaart

- Een kaart met de huidige locatie van de patient.

---
<br><br/>

<img src="./Photos/maating.png" alt="Simulatie Dashboard" width="400"/>



### Metingen (Maating)

Deze kaart toont gewicht, spiermassa, vetmassa, BMI en vochtbalans. Deze waarden synchroniseren automatisch via de Withings-app.

Workflow:

1. De persoon voert een meting uit via een Withings-apparaat (weegschaal, bloeddrukmeter/BpmConnect, SmartWatch, beamO, enzovoort).
2. Let op: SleepAnalyzer valt buiten deze flow, omdat dit apparaat alleen voor slaapmonitoring wordt gebruikt.
3. Volg de instructies op het apparaat zorgvuldig.
4. De meting synchroniseert naar de Withings-app en vervolgens naar Home Assistant.
5. Je ziet de meting eerst in de app en daarna binnen enkele seconden op het dashboard.
6. Verschijnt de meting niet, volg dan de stappen in de sectie Problemen oplossen.

---
<br><br/>

### Simulatie

In het Simulatie-dashboard staan zeven grote en kleine kaarten met verschillende soorten informatie:

- **Databron en Simulatiefase**: Toont de huidige gegevensbron (live of gesimuleerd) en de huidige fase van de casus (bijvoorbeeld Meting 1, 2, 3...).
- **Huidige meetwaarden**: Toont actuele waarden zoals gewicht, bloeddruk, hartslag, ademfrequentie, SpO2 en bloedtemperatuur.
- **Simulatie Invoer**: Voor handmatige invoer van waarden, bijvoorbeeld bij een les-scenario of tijdelijke uitval van Withings.
- **Cardiale monitoring**: Grafiek met historische waarden voor onder andere gewicht, spiermassa, vetmassa, vochtbalans, BMI, systolische bloeddruk, hartfrequentie, ademfrequentie en saturatie.
- **Periodieke tabel (onder de grafiek)**: Snel overzicht van opgeslagen waarden per meetmoment in de huidige sessie.
- **Meting toevoegen aan actieve periode (onder de tabel)**: Alternatieve invoer om waarden toe te voegen aan een geselecteerde periode (Meting 1 t/m 8).
- **Patientprofiel**: Toont statische patientinformatie en biedt opties voor patientfoto upload en verversen van de fotogalerij.

#### Uitleg Simulatie Invoer

De kaart `Simulatie Invoer` bevat velden voor gewicht, bloeddruk, hartslag, ademfrequentie, SpO2 en bloedtemperatuur.

Na klik op `Sla huidige meting op`:

- worden de waarden bijgewerkt op de kaart `Huidige meetwaarden`;
- worden ze doorgestuurd naar `sensor.simulation_manager`;
- worden grafiek en tabel op `Cardiale monitoring` direct bijgewerkt.

#### Uitleg Meting toevoegen aan actieve periode

Deze methode werkt vergelijkbaar met `Simulatie Invoer`, maar koppelt waarden direct aan een specifieke periode (Meting 1 t/m 8).

Na invoer en klik op `Opslaan` worden nieuwe waarden oranje bovenaan de actieve waarden in de tabel getoond. Dit is geschikt om scenario's met tijdsverloop te simuleren.

### Cardiale monitoring (Overzicht)

Deze kaart toont een grafiek met historische waarden voor gewicht, bloeddruk, hartfrequentie, ademfrequentie, saturatie en opmerkingen binnen de huidige sessie. Dit maakt zichtbaar hoe de toestand van de patient tijdens de simulatie verandert.

### Observatie progressie

De laatste kaart toont de huidtriage-status over langere tijd, inclusief een tijdlijn met triagestatussen en registratiemomenten.

## Problemen oplossen (Troubleshooting)

Het Home Assistant-dashboard is ontworpen voor gebruik zonder technische achtergrond. Volg deze stappen zorgvuldig:

1. **Controleer de integratie**
	Kijk of de Withings-integratie actief is via Instellingen -> Apparaten & Diensten -> Integraties.
	Als de integratie ontbreekt, moet deze opnieuw worden ingesteld door het technische team.

2. **Forceer een synchronisatie**
	Open de Withings-integratie en ga naar de gekoppelde apparaten.
	Klik op de drie puntjes bovenaan elk uitklapmenu (niet de drie puntjes naast de apparaatnaam) en kies `Herladen`.

3. **Herstart het systeem**
	Als bovenstaande niet werkt, herstart Home Assistant via Instellingen -> Systeem -> Herstarten.
	Dit kan tijdelijke verbindingsproblemen met Withings oplossen.

### Metingen worden niet gesynchroniseerd
- Ga naar **Instellingen -> Apparaten & Diensten -> Integraties -> Withings** Druk op **Account Toevoegen** en volg de stappen om opnieuw in te loggen met de Withings-account. Gebruik Deze inloggegevens die het technische team heeft verstrekt. Na succesvolle herauthenticatie zouden de metingen weer moeten synchroniseren.
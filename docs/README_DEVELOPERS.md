# Ontwikkelaarsdocumentatie: Cardiac Monitoring Refresh (2026-03)

## Doel van deze wijziging

Deze release vervangt de oude lichaamssamenstelling/PESDIE-flow door een cardio-monitoring scenario voor Mevrouw Goedheid.

- Patiëntprofiel: 70 jaar, voorgeschiedenis van myocardinfarct (MI) en artrose.
- Datareeks: 8 vaste meetpunten van 01-03-2026 t/m 25-03-2026.
- Vitals: gewicht, bloeddruk, hartfrequentie, ademfrequentie, saturatie, opmerkingen.

## Architectuurwijzigingen

1. Datahelpers en templates zijn herbouwd in config/packages/mevrouw_goedheid_simulation.yaml.
2. Canonieke dashboard-entiteiten zijn beschikbaar als:
   - sensor.gewicht
   - sensor.bloeddruk
   - sensor.hartfrequentie
   - sensor.ademfrequentie
   - sensor.saturatie
3. Alertlogica is toegevoegd:
   - Lage saturatie: sensor.saturatie < 93
   - Hoge pols: sensor.hartfrequentie > 100
4. De simulation_manager blijft de periodedata dragen; extra velden worden opgeslagen via ALLOW_EXTRA.

## Data refresh flow

- **Klasse:** `SimulationState`
- **Verantwoordelijkheid:** Beheert de lijst met simulatieperioden en hun bijbehorende metingen.
- **Opslag:** Gegevens worden geserialiseerd naar een JSON-compatibel woordenboekformaat (`to_dict`) en opnieuw samengesteld (`from_dict`).

## Dashboard wijzigingen

- Nieuwe kernblokken:
  - Databron + simulatiefase
  - Patiëntprofiel
  - Huidige meetwaarden + alerts
  - Simulatie invoer
  - Metingentabel met opmerkingen
  - 6-maanden trendkaart (geschaald op maartdata)
  - Observatielog progressie

- **Mechanisme:** Na elke staatmutatie verwerkt de integratie de volledige staat en stelt deze in als de `attributes` van `sensor.simulation_manager`.
- **Voordeel:** De Lovelace frontend-kaart abonneert zich op wijzigingen in deze enkele entiteit via de Home Assistant WebSocket API. Dit zorgt voor onmiddellijke UI-updates wanneer gegevens wijzigen.

- config/packages/mevrouw_goedheid_simulation.yaml
- config/dashboards/simulation_dashboard.yaml
- config/dashboards/simulation/row1_controls.yaml
- config/dashboards/simulation/row2_meetwaarden.yaml
- config/dashboards/simulation/row3_period_card.yaml
- scripts/seed_periods.py
- scripts/refresh_cardiac_history_influx.py

## Verificatiechecklist

Het project houdt zich aan een "Nul Hardcoding" filosofie. Entiteit-ID's (bijv. specifieke sensoren zoals `sensor.temperature_123`) mogen niet hardcoded zijn in de broncode.

### Dynamische Entiteit Scanner

Het script `scripts/dynamic_entity_scanner.py` demonstreert het patroon voor het dynamisch ontdekken van entiteiten.

- **Probleem:** Hardcoded ID's breken het systeem als een sensor wordt vervangen of als de code in een andere kamer wordt ingezet.
- **Oplossing:** Gebruik Home Assistant's Area Registry of Label Registry om apparaten te groeperen. Het systeem moet zoeken naar "alle temperatuursensoren in de Klaslokaal-ruimte" in plaats van te verwijzen naar een specifiek ID.

## Bestandsstructuur

- `custom_components/simulation_manager/`: De backend integratielogica.
- `www/simulation-period-card/`: De frontend aangepaste kaart (JavaScript).
- `config/packages/`: YAML-configuratiepakketten.
- `scripts/`: Hulpscripts voor ontwikkeling en implementatie (draaien op de ontwikkelaarsmachine, niet HAOS).

## Weersintegratie & Clock-Weather-Card

### Architectuuroverzicht

Het weersdashboard bestaat uit drie lagen:

| Laag           | Component                     | Verantwoordelijkheid                                                              |
| -------------- | ----------------------------- | --------------------------------------------------------------------------------- |
| Dataprovider   | Met.no (`domain: met`)      | Haalt weersvoorspellingen op via de open API van yr.no op basis van coördinaten  |
| HA-entiteit    | `weather.forecast_home`     | Stelt weersstatus en uurlijkse/dagelijkse voorspellingen beschikbaar als HA-state |
| Frontend-kaart | `custom:clock-weather-card` | Toont klok, huidige conditie en 5-daagse voorspelling in Lovelace                 |

### Omgevingsconfiguratie

De Met.no-integratie is geconfigureerd via de HA-config flow (niet via YAML). De waarden die bij setup zijn ingevoerd:

```
Naam      : Home  (weergavenaam 'Eindhoven' ingesteld via entity registry)
Entiteit  : weather.forecast_home
Breedtegraad : 51.4351 °N  (thuislocatie vanuit HA-kerninstelling)
Lengtegraad  : 5.4617 °E
Hoogte       : 0 m
```

De weergavenaam is los van de `entry_id` bijgewerkt naar **Eindhoven** via de entity registry (`config/entity_registry/update` WebSocket-call in `scripts/_setup_eindhoven_weather.py`).

### Script: `scripts/_setup_eindhoven_weather.py`

Eenmalig hulpscript dat op de **ontwikkelaarsmachine** wordt uitgevoerd (niet op HAOS).

**Wat het doet:**

1. Loopt in twee WebSocket-sessies: eerst een probe om de `entry_id` van de actieve Met.no-inschrijving te resolven, daarna de eigenlijke aanpassing.
2. Roept `config/entity_registry/update` aan om de `name` van `weather.forecast_home` in te stellen op `"Eindhoven"`.
3. Probeert de Met.no options-flow te starten om de hoogte bij te werken; valt stil terug als die WebSocket-handshake niet beschikbaar is (de REST-fallback is uitgecommentarieerd in het bestand).

**Opnieuw uitvoeren:**

```bash
python scripts/_setup_eindhoven_weather.py
```

Het script is idempotent — een tweede uitvoering overschrijft de naam gewoon opnieuw.

**Wanneer je dit script nodig hebt:**

- Na een HA-reinstallatie waarbij de entity registry is gewist.
- Als iemand de entiteitnaam handmatig heeft gereset via de HA-UI.

### Kaartkonfiguratie in `scripts/push_dashboard.py`

De `clock-weather-card` wordt als eerste kaart in het overzichtsview geïnjecteerd:

```python
{
    "type": "custom:clock-weather-card",
    "entity": "weather.forecast_home",
    "forecast_rows": 5,
    "locale": "nl",
    "time_format": 24,
    "hide_today_section": False,
    "hide_forecast_section": False,
    "show_humidity": True,
    "show_wind": True,
}
```

De kaart is geïnstalleerd via HACS (`pkissling/clock-weather-card`). Als de kaart na een HA-herstart verdwenen is, controleer dan of het HACS-frontend-resource `/hacsfiles/clock-weather-card/clock-weather-card.js` nog actief is via **HACS → Frontend**.

### Schaalbaarheidsnotitie

Met.no ondersteunt meerdere locaties door meerdere `config_entries` aan te maken (één per stad). Als de smart room naar een andere locatie verhuist, voer dan een nieuwe config flow uit via `scripts/_setup_eindhoven_weather.py` (pas `EH_LAT`, `EH_LON`, `EH_ELEV` en de naam aan) — de dashboardkaart blijft werken zolang `entity` in de kaartkonfiguratie overeenkomt.

---

## Best Practices voor Bijdragen

1. **Wijzig Eerst Modellen:** Bij het toevoegen van functies, update eerst `models.py` om ervoor te zorgen dat de gegevensstructuur werkt.
2. **Update Services:** Stel nieuwe functionaliteit bloot via services in `services.yaml` en handlers in `__init__.py`.
3. **Frontend Synchronisatie:** Zorg ervoor dat de frontend-kaart de nieuwe staatstructuur die naar `sensor.simulation_manager` wordt gepusht correct afhandelt.
4. **Photo Uploader Frontend:** Voor ontwikkelaars die de dashboard-uploader willen ondeFrsteunen of uitbreiden:

   - De uploader frontend bestaat uit `photo_uploader.js` en wordt geplaatst onder `www/photo_uploader/photo_uploader.js` in de Home Assistant-config.
   - Resource-URL in Lovelace: `/local/photo_uploader/photo_uploader.js` (type `module`).
   - Kaart YAML om te gebruiken op dashboards:

```yaml
type: 'custom:photo-uploader'
```

    - De backend-service is`photo_scanner.upload` (service data: `filename`, `content` (base64), `overwrite`). De service slaat bestanden op in `config/www/photos` en triggert `photo_scanner.scan`.
4.  **Geen OS-wijzigingen:** Vertrouw niet op het installeren van systeempakketten via `apt` of `pip` op de HA-host. Alles moet draaien binnen de standaard Home Assistant-omgeving.

# Belangrijke Opmerking

## Push Scripts
   - Pushen van de codebase moet met zorg gebueren, Ik heb deze push scripts toegevoegd om een base te kunnen hebben en verder uit de UI kunnen werken, Als alle benodigdheden zijn toegevoegd kunnen we meeste functionaliteiten toevoegen via de UI zonder dat we de codebase hoeven aan te passen, maar voor het geval dat er iets is dat niet via de UI kan worden toegevoegd kunnen we altijd deze scripts gebruiken om de codebase aan te passen en daarna verder te werken via de UI.

## Commits 
   - Ik heb geprobeerd om de commits zo duidelijk mogelijk te maken, maar als er iets is dat niet duidelijk is of als er vragen zijn over bepaalde commits, aarzel dan niet om het te vragen. Ik zal mijn best doen om alles zo duidelijk mogelijk uit te leggen.
Arshia Azadia

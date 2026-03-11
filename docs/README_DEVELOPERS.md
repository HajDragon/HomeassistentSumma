# Ontwikkelaarsdocumentatie: Home Assistant Educatieve Slimme Kamer

## Overzicht

Dit document biedt technische details voor softwareontwikkelaars die het Home Assistant Educational Smart Room-project onderhouden of uitbreiden. Het systeem is gebouwd op Home Assistant OS (HAOS) en maakt gebruik van een aangepaste integratie voor staatbeheer en een aangepaste Lovelace-kaart voor de gebruikersinterface.

## Architectuur

De kern van de simulatielogica bevindt zich in de map `custom_components/simulation_manager`. In tegenstelling tot standaard Home Assistant-sensoren die typisch staatloos of polling-gebaseerd zijn, vereist dit project gestructureerde, persistente staten om simulatieperioden en metingen over herstarts heen bij te houden.

### 1. Staatbeheer (Het Brein)

Alle bedrijfslogica is ingekapseld in `models.py`. Deze module is puur Python en heeft geen afhankelijkheden van de Home Assistant-kern.

-   **Klasse:** `SimulationState`
-   **Verantwoordelijkheid:** Beheert de lijst met simulatieperioden en hun bijbehorende metingen.
-   **Opslag:** Gegevens worden geserialiseerd naar een JSON-compatibel woordenboekformaat (`to_dict`) en opnieuw samengesteld (`from_dict`).

### 2. Integratielaag (De Lijm)

Het bestand `__init__.py` dient als de brug tussen Home Assistant en de `SimulationState`.

-   **Service Registratie:** Het registreert services zoals `simulation_manager.switch_period`, `simulation_manager.save_measurement`, en `simulation_manager.reset_simulation`.
-   **Staat Mutatie:** Wanneer een service wordt aangeroepen, roept deze laag de overeenkomstige methode op het `SimulationState`-object aan.
-   **Persistentie:** Wijzigingen worden opgeslagen in `.storage/simulation_manager` met behulp van `homeassistant.helpers.storage.Store`.

### 3. Reactieve Frontend Updates (De Megafoon)

Om ervoor te zorgen dat de frontend direct wordt bijgewerkt zonder polling, pusht de integratie de volledige staat naar één sensor-entiteit: `sensor.simulation_manager`.

-   **Mechanisme:** Na elke staatmutatie verwerkt de integratie de volledige staat en stelt deze in als de `attributes` van `sensor.simulation_manager`.
-   **Voordeel:** De Lovelace frontend-kaart abonneert zich op wijzigingen in deze enkele entiteit via de Home Assistant WebSocket API. Dit zorgt voor onmiddellijke UI-updates wanneer gegevens wijzigen.

```python
# Integratie update patroon in __init__.py
def _push_update(self):
    """Notify frontend of new state."""
    self.hass.states.async_set(
        ENTITY_ID, 
        self.state.active_period_id or NO_ACTIVE_PERIOD,
        attributes=self.state.to_dict()
    )
    # Asynchronous save to disk
    self._store.async_delay_save(self._data_to_save, 1.0)
```

## Schaalbaarheid en Dynamische Configuratie

Het project houdt zich aan een "Nul Hardcoding" filosofie. Entiteit-ID's (bijv. specifieke sensoren zoals `sensor.temperature_123`) mogen niet hardcoded zijn in de broncode.

### Dynamische Entiteit Scanner

Het script `scripts/dynamic_entity_scanner.py` demonstreert het patroon voor het dynamisch ontdekken van entiteiten.

-   **Probleem:** Hardcoded ID's breken het systeem als een sensor wordt vervangen of als de code in een andere kamer wordt ingezet.
-   **Oplossing:** Gebruik Home Assistant's Area Registry of Label Registry om apparaten te groeperen. Het systeem moet zoeken naar "alle temperatuursensoren in de Klaslokaal-ruimte" in plaats van te verwijzen naar een specifiek ID.

## Bestandsstructuur

-   `custom_components/simulation_manager/`: De backend integratielogica.
-   `www/simulation-period-card/`: De frontend aangepaste kaart (JavaScript).
-   `config/packages/`: YAML-configuratiepakketten.
-   `scripts/`: Hulpscripts voor ontwikkeling en implementatie (draaien op de ontwikkelaarsmachine, niet HAOS).

## Best Practices voor Bijdragen

1.  **Wijzig Eerst Modellen:** Bij het toevoegen van functies, update eerst `models.py` om ervoor te zorgen dat de gegevensstructuur werkt.
2.  **Update Services:** Stel nieuwe functionaliteit bloot via services in `services.yaml` en handlers in `__init__.py`.
3.  **Frontend Synchronisatie:** Zorg ervoor dat de frontend-kaart de nieuwe staatstructuur die naar `sensor.simulation_manager` wordt gepusht correct afhandelt.
4.  **Geen OS-wijzigingen:** Vertrouw niet op het installeren van systeempakketten via `apt` of `pip` op de HA-host. Alles moet draaien binnen de standaard Home Assistant-omgeving.

# Systeembeheerdershandleiding: Home Assistant Educatieve Slimme Kamer

## Overzicht

Deze handleiding is bedoeld voor systeembeheerders die de educatieve slimme kamer beheren met behulp van de Home Assistant-gebruikersinterface. Het behandelt configuratie, apparaatbeheer en stappen voor probleemoplossing. Er is geen programmeerkennis of terminaltoegang vereist voor deze taken.

## Dashboardconfiguratie

De primaire interface voor de simulatie is de **Simulation Period Card**. Dit aangepaste element stelt leraren in staat de simulatie te besturen en gegevens te loggen.

### De Simulatiekaart Toevoegen

Als u het simulatiebedieningspaneel aan een nieuwe dashboardweergave moet toevoegen:

1.  Navigeer naar het gewenste Dashboard.
2.  Klik op het **Dashboard bewerken** (potloodpictogram) in de rechterbovenhoek.
3.  Klik op de knop **+ Kaart toevoegen**.
4.  Scrol naar de onderkant van de lijst en selecteer **Handmatig**.
5.  Voer de volgende configuratie-YAML in:

```yaml
type: custom:simulation-period-card
```

6.  Klik op **Opslaan**. De kaart zal proberen de simulatiemanager-entiteit automatisch te ontdekken.

## Apparaten Beheren

Wanneer nieuwe hardware aan de kamer wordt toegevoegd (bijv. slimme stekkers, sensoren of lampen), moet deze correct worden toegewezen in Home Assistant zodat het systeem deze herkent.

### Een Nieuw Apparaat Toevoegen

1.  Ga naar **Instellingen** > **Apparaten & Diensten**.
2.  Als het apparaat automatisch wordt ontdekt, klik op **Configureren**. Zo niet, klik op **+ Integratie toevoegen** en zoek naar het merk van het apparaat (bijv. Withings, Philips Hue).
3.  Volg de instructies op het scherm om het apparaat te koppelen.

### Toewijzen aan een Ruimte

De geautomatiseerde logica vertrouwt er vaak op dat apparaten zich in de juiste "Ruimte" bevinden.

1.  Zoek na het toevoegen van het apparaat deze in de apparaatlijst.
2.  Klik op het **potloodpictogram** (Bewerken) naast de naam van het apparaat.
3.  Selecteer in het vervolgkeuzemenu **Ruimte** de juiste kamer (bijv. "Klaslokaal" of "Lab").
4.  Klik op **Bijwerken**.

## Probleemoplossing

### Fouten in Simulatiekaart

**Probleem:** Het dashboard toont "Custom Element doesn't exist: simulation-period-card".
**Oplossing:**
1.  Dit is vaak een browsercache-probleem. Voer een harde verversing van de browserpagina uit (Ctrl + F5 op Windows/Linux, Cmd + Shift + R op macOS).
2.  Controleer of het bestand `simulation-period-card.js` bestaat in de map `www/simulation-period-card/` met behulp van de File Editor add-on indien beschikbaar.

### Simulatiemanager Niet Beschikbaar

**Probleem:** De kaart toont een fout of knoppen reageren niet.
**Oplossing:**
1.  Ga naar **Ontwikkelhulpmiddelen** > **Staten**.
2.  Zoek naar `sensor.simulation_manager`.
3.  Controleer de kolom **Staat**.
    -   Als de staat `unavailable` of `unknown` is, is de integratie mogelijk niet geladen.
    -   Herstart Home Assistant door naar **Instellingen** > **Systeem** > **Herstarten** te gaan.

### Gegevens Worden Niet Opgeslagen

**Probleem:** Klikken op "Meting Opslaan" werkt de tabel niet bij.
**Oplossing:**
1.  Zorg ervoor dat Home Assistant draait en verbonden is met het netwerk.
2.  Controleer of er momenteel een periode actief is. Het systeem vereist een actieve periode (bijv. "Periode 1") om metingen aan te koppelen.

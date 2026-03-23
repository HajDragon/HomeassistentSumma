# Lerarenhandleiding: Educatieve Slimme Kamer Simulatie

## Inleiding

Welkom in de Slimme Kamer! Met dit systeem kunt u interactieve simulaties uitvoeren tijdens uw lessen, de kameromgeving regelen en experimentgegevens in realtime loggen. Deze handleiding legt uit hoe u de dashboardbediening gebruikt.

## Lesvoorbereiding

Vink de volgende punten aan op het dashboard **vóór** u de simulatie start. U vindt deze in de kaart **Lesvoorbereiding ✓** bovenaan de pagina.

1. **Weegschaal gereserveerd (Xerte)** — Heeft u de body scan slimme weegschaal gereserveerd via Xerte?
2. **Studenten kennen vochtbalans & BMI** — Hebben uw studenten voorkennis over vochtbalans en BMI?
3. **Studenten kennen spijsvertering** — Hebben uw studenten kennis van voedingsstoffen en het spijsverteringskanaal?
4. **Studenten kunnen PESDIE toepassen** — Weten uw studenten hoe ze een PESDIE schrijven?

Zet elk vakje op **Aan** zodra u het punt hebt gecontroleerd. Zodra alle vier vakjes aan staan, verandert de statusregel **Les klaar om te starten?** naar **True**.

> De checkboxes worden **niet** gereset als u op "Reset Simulatie" drukt — ze blijven aan staan voor de hele les.

## Een Klassimulatie Starten

De simulatie is georganiseerd in "Perioden". Het activeren van een periode stelt de status van de kamer in voor die specifieke lesfase.

1. **Toegang tot het Dashboard:** Open de Home Assistant-app op de tablet in het klaslokaal of navigeer naar het tabblad Simulatie in de webbrowser.
2. **Selecteer een Periode:** Zoek de rij tabbladen met het label "Periode 1", "Periode 2", enz.
3. **Activeren:** Tik op het tabblad dat overeenkomt met de huidige lesactiviteit.
   - Het systeem schakelt van context. Apparaten kunnen van status veranderen (bijv. lichten of schermen), afhankelijk van de configuratie voor die periode.
   - De gegevenstabel hieronder toont nu alleen metingen voor deze specifieke periode.

## Experimentgegevens Loggen

Tijdens een les kunnen u of uw studenten datapunten direct in het systeem opnemen.

1. **Kies de juiste meting:** Controleer eerst of de juiste fase actief staat (Meting 1, 2, 3 of 4).
2. **Voer meetwaarden in:** Gebruik de sectie **Simulatie Invoer (aanpasbaar)** voor de actuele waarden.
3. **Voer PESDIE in:** Ga naar **PESDIE Workflow (Per Student)** en vul in:
   - **Student ID** (bijvoorbeeld student_01)
   - **PESDIE Output** (1 tekst met P-E-S-D-I-E)
4. **Opslaan PESDIE:** Tik op de knop **Submit PESDIE**.
   - De inzending verschijnt in de lijst **PESDIE Inzendingen per Periode**.
   - Elke inzending krijgt automatisch een oplopend **PESDIE #** nummer binnen de huidige meting/periode.
   - De PESDIE-lijst toont nu meteen de tabel (zonder grafiek), zodat je direct de nieuwe regel ziet.
5. **Opslaan meetwaarden (optioneel):** Gebruik **Submit Waarde** als u ook meetwaarden tegelijk wilt bewaren.

## De Simulatie Resetten

Aan het einde van een les of bij het starten van een volledig nieuw experiment, moet u mogelijk de gegevens wissen.

1. **Zoek de Resetknop:** Zoek de **RESET**-knop, meestal te vinden in de buurt van de periodeselectieknoppen.
2. **Bevestig Reset:** Er verschijnt een bevestigingsvenster om per ongeluk verwijderen te voorkomen. Tik op **Bevestigen** of **OK**.
   - **Actie:** Dit wist alle opgenomen metingen van het scherm.
   - **Staat:** Het systeem keert terug naar een "Geen Actieve Periode"-staat.
   - U kunt nu een nieuwe periode selecteren om de volgende sessie vers te beginnen.

## Ondersteuning

Als het dashboard niet reageert of de apparaten in de kamer zich niet gedragen zoals verwacht, neem dan contact op met de systeembeheerder. Probeer niet om apparaten los te koppelen of instellingen te wijzigen in de gedetailleerde configuratiemenu's.

## Foto Uploader (Voor Leraren)

U kunt afbeeldingen (bijv. foto van een casus of patiëntetter) direct vanaf het dashboard uploaden zodat ze beschikbaar zijn in opdrachten en kaarten.

- Zodra de beheerder `photo_uploader.js` heeft toegevoegd als dashboardresource (`/local/photo_uploader/photo_uploader.js`), voegt u een kaart toe met:

```yaml
type: 'custom:photo-uploader'
```

- Kies een bestand en klik op **Upload**. De afbeelding wordt opgeslagen in de servermap `www/photos` en is meteen beschikbaar voor de Photo Scanner en andere kaarten.

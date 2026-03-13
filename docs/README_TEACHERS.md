# Lerarenhandleiding: Educatieve Slimme Kamer Simulatie

## Inleiding

Welkom in de Slimme Kamer! Met dit systeem kunt u interactieve simulaties uitvoeren tijdens uw lessen, de kameromgeving regelen en experimentgegevens in realtime loggen. Deze handleiding legt uit hoe u de dashboardbediening gebruikt.

## Een Klassimulatie Starten

De simulatie is georganiseerd in "Perioden". Het activeren van een periode stelt de status van de kamer in voor die specifieke lesfase.

1.  **Toegang tot het Dashboard:** Open de Home Assistant-app op de tablet in het klaslokaal of navigeer naar het tabblad Simulatie in de webbrowser.
2.  **Selecteer een Periode:** Zoek de rij tabbladen met het label "Periode 1", "Periode 2", enz.
3.  **Activeren:** Tik op het tabblad dat overeenkomt met de huidige lesactiviteit.
    -   Het systeem schakelt van context. Apparaten kunnen van status veranderen (bijv. lichten of schermen), afhankelijk van de configuratie voor die periode.
    -   De gegevenstabel hieronder toont nu alleen metingen voor deze specifieke periode.

## Experimentgegevens Loggen

Tijdens een les kunnen u of uw studenten datapunten direct in het systeem opnemen.

1.  **Kies de juiste meting:** Controleer eerst of de juiste fase actief staat (Meting 1, 2, 3 of 4).
2.  **Voer meetwaarden in:** Gebruik de sectie **Simulatie Invoer (aanpasbaar)** voor de actuele waarden.
3.  **Voer PESDIE in:** Ga naar **PESDIE Workflow (Per Student)** en vul in:
    -   **Student ID** (bijvoorbeeld student_01)
    -   **PESDIE Output** (1 tekst met P-E-S-D-I-E)
4.  **Opslaan PESDIE:** Tik op de knop **Submit PESDIE**.
    -   De inzending verschijnt in de lijst **PESDIE Inzendingen per Periode**.
    -   Elke inzending krijgt automatisch een oplopend **PESDIE #** nummer binnen de huidige meting/periode.
    -   De PESDIE-lijst toont nu meteen de tabel (zonder grafiek), zodat je direct de nieuwe regel ziet.
5.  **Opslaan meetwaarden (optioneel):** Gebruik **Submit Waarde** als u ook meetwaarden tegelijk wilt bewaren.

## Lesworkflow Voor PESDIE

Gebruik deze volgorde tijdens de kern van de les:

1.  Bespreek de trend tussen Meting 1 t/m 4 met de klas.
2.  Laat elke student 1 PESDIE schrijven voor Mevrouw Goedheid.
3.  Laat studenten om de beurt hun Student ID en PESDIE invullen.
4.  Druk na elke student op **Submit PESDIE**.
5.  Bespreek in de afronding enkele PESDIE-voorstellen klassikaal.

## De Simulatie Resetten

Aan het einde van een les of bij het starten van een volledig nieuw experiment, moet u mogelijk de gegevens wissen.

1.  **Zoek de Resetknop:** Zoek de **RESET**-knop, meestal te vinden in de buurt van de periodeselectieknoppen.
2.  **Bevestig Reset:** Er verschijnt een bevestigingsvenster om per ongeluk verwijderen te voorkomen. Tik op **Bevestigen** of **OK**.
    -   **Actie:** Dit wist alle opgenomen metingen van het scherm.
    -   **Staat:** Het systeem keert terug naar een "Geen Actieve Periode"-staat.
    -   U kunt nu een nieuwe periode selecteren om de volgende sessie vers te beginnen.

## Ondersteuning

Als het dashboard niet reageert of de apparaten in de kamer zich niet gedragen zoals verwacht, neem dan contact op met de systeembeheerder. Probeer niet om apparaten los te koppelen of instellingen te wijzigen in de gedetailleerde configuratiemenu's.

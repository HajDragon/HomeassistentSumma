# Beheerdershandleiding: Cardiac Monitoring Dashboard

## Doel

Deze handleiding beschrijft het beheer van de nieuwe Body Scan + BPM Connect simulatie voor Mevrouw Goedheid.

## Wat is veranderd

1. PESDIE workflow is verwijderd uit de gebruikersinterface.
2. Stappenplan-kaarten zijn verwijderd.
3. De simulatie draait nu op 8 vaste meetpunten in maart 2026.
4. Alerts zijn actief voor lage saturatie en hoge pols.

## Bediening via Home Assistant UI

1. Open het dashboard Body Scan en BPM Connect.
2. Controleer Databron en Simulatiefase.
3. Controleer de kaart Huidige Meetwaarden voor gewicht, bloeddruk, pols, ademfrequentie en saturatie.
4. Controleer de twee alert-indicatoren:
   - Alert lage saturatie (<93)
   - Alert hoge pols (>100)

## Nieuwe les starten

1. Zet de simulatiefase op Reset / Startklaar.
2. Kies daarna de gewenste meting (1 t/m 8).
3. Controleer dat datum, waarden en opmerking meeschakelen.
4. Gebruik Sla huidige meting op als u een datapunt wilt vastleggen.

## Controlepunten na deploy

1. De observatielog toont 8 regels van 01-03-2026 t/m 25-03-2026.
2. De trendkaart toont stijgend gewicht, stijgende bloeddruk en dalende saturatie.
3. Het patiëntprofiel toont 70 jaar, MI en artrose.
4. Er zijn geen PESDIE- of stappenplanblokken zichtbaar.

## Foutafhandeling

1. Als waarden niet updaten: herlaad de pagina en controleer sensor.simulation_manager in Ontwikkelhulpmiddelen > Staten.
2. Als de custom kaart niet laadt: controleer of simulation-period-card.js als resource beschikbaar is.
3. Als de trendkaart leeg is: controleer of apexcharts-card beschikbaar is en de entiteiten status hebben.

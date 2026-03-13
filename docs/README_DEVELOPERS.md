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

1. Purge oude simulatiedata via service simulation_manager.reset_simulation.
2. Seed nieuwe 8 punten via scripts/seed_periods.py.
3. Indien InfluxDB gebruikt wordt voor externe trendanalyse:
   - Gebruik scripts/refresh_cardiac_history_influx.py
   - Dit script verwijdert bestaande punten voor de meting en schrijft exact de 8 lespunten terug.

## Influx configuratie

Vereiste environment variabelen voor scripts/refresh_cardiac_history_influx.py:

- INFLUX_URL (bijvoorbeeld http://localhost:8086)
- INFLUX_TOKEN
- INFLUX_ORG
- INFLUX_BUCKET
- Optioneel: INFLUX_MEASUREMENT (standaard goedheid_cardiac)

## Dashboard wijzigingen

- PESDIE kaarten en stappenplan zijn verwijderd uit het simulatiedashboard.
- Nieuwe kernblokken:
  - Databron + simulatiefase
  - Patiëntprofiel
  - Huidige meetwaarden + alerts
  - Simulatie invoer
  - Metingentabel met opmerkingen
  - 6-maanden trendkaart (geschaald op maartdata)
  - Observatielog progressie

## Belangrijke bestanden

- config/packages/mevrouw_goedheid_simulation.yaml
- config/dashboards/simulation_dashboard.yaml
- config/dashboards/simulation/row1_controls.yaml
- config/dashboards/simulation/row2_meetwaarden.yaml
- config/dashboards/simulation/row3_period_card.yaml
- scripts/seed_periods.py
- scripts/refresh_cardiac_history_influx.py

## Verificatiechecklist

1. Controleer of alleen de 8 maartregels aanwezig zijn in tabel en trend.
2. Controleer huidige eindstand op 25-03-2026: gewicht 72.2 kg, saturatie 92, pols 102.
3. Trigger test:
   - Saturatie 92 activeert lage-saturatie alert.
   - Hartfrequentie 101 activeert hoge-pols alert.
4. Bevestig dat er geen PESDIE- en stappenplanblokken meer zichtbaar zijn.

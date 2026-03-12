import json
import os
import sys
import time
import websocket  # websocket-client

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("HA_BASE_URL", "http://homeassistant.local:8123").rstrip("/")
TOKEN    = os.getenv("HA_TOKEN")
if not TOKEN:
    sys.exit("Error: HA_TOKEN not set — copy .env.example to .env and fill in your token.")

WS_URL = BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"

# ─────────────────────────────────────────────
# HELPER: styled markdown card
# ─────────────────────────────────────────────
def md(text):
    return {"type": "markdown", "content": text}


# ─────────────────────────────────────────────
# HELPER: section heading markdown
# ─────────────────────────────────────────────
def heading(icon, title, subtitle=""):
    sub = f"\n*{subtitle}*" if subtitle else ""
    return md(f"## {icon} {title}{sub}")


# ─────────────────────────────────────────────
# SECTION 1 — QUICK STATUS BAR
# ─────────────────────────────────────────────
quick_status_note = md(
    "## 🔴 Beveiligingsoverzicht\n"
    "*Deze rij toont de meest kritieke live-statussen in één oogopslag. "
    "Elke badge die rood oplicht vereist onmiddellijke aandacht.*"
)

quick_status_glance = {
    "type": "glance",
    "title": "Live Beveiligingsstatus",
    "show_name": True,
    "show_icon": True,
    "show_state": True,
    "entities": [
        {"entity": "binary_sensor.front_door_beweging",  "name": "Voordeur Beweging",  "icon": "mdi:motion-sensor"},
        {"entity": "binary_sensor.backside_beweging",    "name": "Achterkant Beweging","icon": "mdi:motion-sensor"},
        {"entity": "binary_sensor.front_door_persoon",  "name": "Persoon (Voor)",     "icon": "mdi:account-alert"},
        {"entity": "binary_sensor.backside_persoon",    "name": "Persoon (Achter)",   "icon": "mdi:account-alert"},
        {"entity": "binary_sensor.rt_ax57_02b8_wan_status", "name": "Internet WAN",  "icon": "mdi:wan"},
        {"entity": "binary_sensor.deur_detection",      "name": "Deursensor",         "icon": "mdi:door-open"},
        {"entity": "binary_sensor.rookmelder",          "name": "Rookmelder",         "icon": "mdi:smoke-detector"},
        {"entity": "binary_sensor.sos_wall_button",     "name": "SOS Wandknop",       "icon": "mdi:alert-circle"},
    ],
}

# ─────────────────────────────────────────────
# CAMERA DASHBOARD — shared building blocks
# ─────────────────────────────────────────────

def camera_live_card(prefix, label):
    return {
        "type": "picture-entity",
        "entity": f"camera.{prefix}_vloeiend",
        "name": label,
        "show_name": True,
        "show_state": True,
        "camera_view": "live",
    }

def camera_detection_glance(prefix):
    return {
        "type": "glance",
        "title": "Live Detectie",
        "show_name": True,
        "show_icon": True,
        "show_state": True,
        "entities": [
            {"entity": f"binary_sensor.{prefix}_beweging", "name": "Beweging",     "icon": "mdi:motion-sensor"},
            {"entity": f"binary_sensor.{prefix}_persoon",  "name": "Persoon",      "icon": "mdi:account-alert"},
            {"entity": f"binary_sensor.{prefix}_dier",     "name": "Huisdier",     "icon": "mdi:paw"},
            {"entity": f"binary_sensor.{prefix}_baby_huilt","name": "Baby Huilt",  "icon": "mdi:baby-face"},
            {"entity": f"sensor.{prefix}_dag_nacht_status", "name": "Dag/Nacht",   "icon": "mdi:weather-sunset"},
        ],
    }

# ─────────────────────────────────────────────
# HELPER: PTZ grid for a camera prefix
# ─────────────────────────────────────────────
def ptz_grid(prefix):
    """prefix = 'front_door' or 'backside'"""
    def btn(icon, entity):
        return {
            "type": "button",
            "icon": icon,
            "tap_action": {"action": "call-service", "service": "button.press",
                           "service_data": {"entity_id": entity}},
            "show_name": False,
        }
    return {
        "type": "grid",
        "columns": 3,
        "square": True,
        "cards": [
            {"type": "button", "icon": "mdi:blank", "tap_action": {"action": "none"}, "show_name": False},
            btn("mdi:arrow-up-bold",   f"button.{prefix}_ptz_omhoog"),
            {"type": "button", "icon": "mdi:blank", "tap_action": {"action": "none"}, "show_name": False},
            btn("mdi:arrow-left-bold", f"button.{prefix}_ptz_links"),
            btn("mdi:stop-circle",     f"button.{prefix}_ptz_stop"),
            btn("mdi:arrow-right-bold",f"button.{prefix}_ptz_rechts"),
            {"type": "button", "icon": "mdi:blank", "tap_action": {"action": "none"}, "show_name": False},
            btn("mdi:arrow-down-bold", f"button.{prefix}_ptz_omlaag"),
            {"type": "button", "icon": "mdi:blank", "tap_action": {"action": "none"}, "show_name": False},
        ],
    }


# ─────────────────────────────────────────────
# HELPER: camera toggle entities card
# ─────────────────────────────────────────────
def camera_toggles(prefix, label):
    return {
        "type": "entities",
        "title": f"{label} — Schakelaars & Instellingen",
        "entities": [
            {"entity": f"switch.{prefix}_opnemen",               "name": "Opname"},
            {"entity": f"switch.{prefix}_geluid_opnemen",        "name": "Audio Opnemen"},
            {"entity": f"switch.{prefix}_privacymodus",          "name": "Privacymodus"},
            {"entity": f"switch.{prefix}_automatisch_volgen",    "name": "Automatisch Volgen"},
            {"entity": f"switch.{prefix}_push_notificaties",     "name": "Pushmeldingen"},
            {"entity": f"switch.{prefix}_e_mail_bij_gebeurtenis","name": "E-mail bij Gebeurtenis"},
            {"entity": f"switch.{prefix}_ftp_uploaden",          "name": "FTP Uploaden"},
            {"entity": f"switch.{prefix}_infrared_lights_in_night_mode", "name": "Nachtzicht IR Lichten"},
            {"entity": f"switch.{prefix}_sirene_bij_gebeurtenis","name": "Sirene bij Gebeurtenis"},
            {"entity": f"switch.{prefix}_bewaak_punt_terugkeren","name": "Terug naar Bewakingspunt"},
            {"entity": f"select.{prefix}_dag_nacht_modus",       "name": "Dag/Nachtmodus"},
            {"entity": f"number.{prefix}_ai_persoon_gevoeligheid","name": "Persoon AI Gevoeligheid"},
            {"entity": f"number.{prefix}_ai_huisdier_gevoeligheid","name": "Huisdier AI Gevoeligheid"},
            {"entity": f"number.{prefix}_beweging_gevoeligheid", "name": "Bewegingsgevoeligheid"},
            {"entity": f"number.{prefix}_volume",                "name": "Volume"},
            {"entity": f"number.{prefix}_baby_cry_sensitivity",  "name": "Baby Huil Gevoeligheid"},
            {"entity": f"number.{prefix}_bewaak_punt_terugkeertijd","name": "Bewakingspunt Terugkeertijd (s)"},
            {"entity": f"sensor.{prefix}_dag_nacht_status",      "name": "Huidige Dag/Nachtstatus"},
            {"entity": f"button.{prefix}_bewaak_punt_zet_huidige_positie","name": "Stel Bewakingspunt In op Huidige Positie"},
            {"entity": f"button.{prefix}_bewaak_punt_ga_naar",   "name": "Ga naar Bewakingspunt"},
            {"entity": f"button.{prefix}_ptz_kalibreren",        "name": "Kalibreer PTZ"},
            {"entity": f"light.{prefix}_status_led",             "name": "Status LED"},
            {"entity": f"siren.{prefix}_sirene",                 "name": "Sirene (handmatig)"},
        ],
    }


# ─────────────────────────────────────────────
# BUILD A SINGLE CAMERA TAB VIEW
# ─────────────────────────────────────────────
def camera_view(prefix, label, path, extra_note="", stack_stream_detection=False):
    note_text = (
        f"## 📹 {label} Camera\n"
        "*PTZ-knoppen draaien en kantelen de camera in realtime. "
        "**Automatisch Volgen** laat de camera gedetecteerde bewegingen volgen. "
        "**Privacymodus** bevriest onmiddellijk de stream en schakelt opname uit. "
        "Gevoeligheidssliders hebben effect bij de volgende gedetecteerde gebeurtenis.*"
    )
    if extra_note:
        note_text += f"\n\n---\n⚠️ {extra_note}"

    if stack_stream_detection:
        # Wrap live stream + live detection in a vertical-stack so they are
        # guaranteed to sit in the same column, detection always below the feed.
        #   col-left  : note  →  vertical-stack(stream + detection)
        #   col-mid   : PTZ header  →  PTZ d-pad
        #   col-right : toggles & settings
        stream_block = {
            "type": "vertical-stack",
            "cards": [
                camera_live_card(prefix, label),
                camera_detection_glance(prefix),
            ],
        }
        cards = [
            md(note_text),        # card 1 — note
            stream_block,         # card 2 — stream + detection (stacked)
            md("### PTZ Bediening"),# card 3 — PTZ header
            ptz_grid(prefix),     # card 4 — PTZ d-pad
            camera_toggles(prefix, label),  # card 5 — toggles
        ]
    else:
        #   col-left  : note  →  live stream
        #   col-mid   : live detection  →  PTZ header  →  PTZ d-pad
        #   col-right : toggles & settings
        cards = [
            md(note_text),                    # card 1 — note
            camera_live_card(prefix, label),  # card 2 — live stream
            camera_detection_glance(prefix),  # card 3 — live detection
            md("### PTZ Bediening"),            # card 4 — PTZ header
            ptz_grid(prefix),                 # card 5 — PTZ d-pad
            camera_toggles(prefix, label),    # card 6 — toggles
        ]
    return {
        "title": label,
        "path": path,
        "icon": "mdi:cctv",
        "background": "background: var(--background-image)",
        "cards": cards,
    }

# ─────────────────────────────────────────────
# SECTION 5 — SECURITY & ALERTS
# ─────────────────────────────────────────────
security_note = md(
    "## 🚨 Beveiliging & Meldingen\n"
    "*Rookmelder, deursensor, SOS-knoppen en valdetectieradar. "
    "Apparaten met de status **NIET BESCHIKBAAR** zijn Zigbee-gebaseerd — controleer of de Home Assistant Connect ZBT-2 "
    "coördinator van stroom is voorzien en de Zigbee-integratie actief is. "
    "De sirenes hieronder kunnen handmatig worden geactiveerd in geval van nood.*"
)

security_entities = {
    "type": "entities",
    "title": "Beveiligingsapparaten",
    "entities": [
        {"entity": "binary_sensor.rookmelder",                   "name": "Rookmelder",              "icon": "mdi:smoke-detector-alert"},
        {"entity": "sensor.rookmelder_rookdichtheid",            "name": "Rookdichtheid"},
        {"entity": "sensor.rookmelder_batterij",                 "name": "Rookmelder Batterij",      "icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.deur_detection",               "name": "Deursensor",               "icon": "mdi:door-open"},
        {"entity": "binary_sensor.deur_detection_sabotage",      "name": "Deursensor Sabotage",      "icon": "mdi:shield-alert"},
        {"entity": "sensor.deur_detection_batterij",             "name": "Deursensor Batterij",      "icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.sos_wall_button",              "name": "SOS Wandknop",             "icon": "mdi:alarm-light"},
        {"entity": "sensor.sos_wall_button_batterij",            "name": "SOS Wandknop Batterij",    "icon": "mdi:battery"},
        {"entity": "binary_sensor.tz3000_p3fph1go_ts0215a",     "name": "SOS Draagknop",            "icon": "mdi:alarm-light"},
        {"entity": "sensor.tz3000_p3fph1go_ts0215a_batterij",   "name": "SOS Draagknop Batterij",   "icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.seeed_studio_mr60fda2_kit_8f65d0_falling_information", "name": "Val Gedetecteerd",  "icon": "mdi:human-cane"},
        {"entity": "binary_sensor.seeed_studio_mr60fda2_kit_8f65d0_person_information",  "name": "Persoon in Kamer",  "icon": "mdi:account"},
        {"type": "divider"},
        {"entity": "siren.front_door_sirene",  "name": "Voordeur Sirene (Handmatig)",   "icon": "mdi:alarm-bell"},
        {"entity": "siren.backside_sirene",    "name": "Achterkant Sirene (Handmatig)", "icon": "mdi:alarm-bell"},
        {"type": "divider"},
        {"entity": "automation.siren_webhoek", "name": "Webhook → Sirene Automatisering", "icon": "mdi:webhook"},
    ],
}

# ─────────────────────────────────────────────
# SECTION 6 — HEALTH MONITOR
# ─────────────────────────────────────────────
health_note = md(
    "## ❤️ Gezondheidsmonitor\n"
    "*Gegevens van uw Withings-apparaten: BeamO, BPM Connect, ScanWatch 2 en Body Scan. "
    "Waarden worden bijgewerkt na elke meting — ze streamen niet in realtime. "
    "Bloeddruk en SpO2 weerspiegelen de meest recent opgeslagen meting.*"
)

health_grid = {
    "type": "grid",
    "columns": 2,
    "square": False,
    "cards": [
        {
            "type": "entities",
            "title": "Vitale waarden",
            "entities": [
                {"entity": "sensor.withings_hartslag",           "name": "Hartslag (BPM)"},
                {"entity": "sensor.withings_hartslag_2",         "name": "Hartslag #2"},
                {"entity": "sensor.withings_systolische_bloeddruk", "name": "Bloeddruk (Systolisch)"},
                {"entity": "sensor.withings_diastolische_bloeddruk","name": "Bloeddruk (Diastolisch)"},
                {"entity": "sensor.withings_spo2",               "name": "SpO2 (%)"},
                {"entity": "sensor.withings_spo2_2",             "name": "SpO2 #2 (%)"},
                {"entity": "sensor.withings_lichaamstemperatuur", "name": "Lichaamstemperatuur (°C)"},
                {"entity": "sensor.withings_huidtemperatuur",    "name": "Huidtemperatuur (°C)"},
                {"entity": "sensor.withings_temperatuur",        "name": "Omgevingstemperatuur (°C)"},
                {"entity": "sensor.withings_gewicht",            "name": "Gewicht (kg)"},
            ],
        },
        {
            "type": "entities",
            "title": "Activiteit & Batterijen",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag",      "name": "Stappen Vandaag"},
                {"entity": "sensor.withings_stap_doelstelling",    "name": "Stappendoel"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand","name": "Afstand Vandaag"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand","name": "Actieve Calorieën"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand","name": "Totale Calorieën"},
                {"type": "divider"},
                {"entity": "sensor.beamo_batterij",      "name": "BeamO Batterij",       "icon": "mdi:battery"},
                {"entity": "sensor.body_scan_batterij",  "name": "Body Scan Batterij",   "icon": "mdi:battery"},
                {"entity": "sensor.bpm_connect_batterij","name": "BPM Connect Batterij", "icon": "mdi:battery"},
                {"entity": "sensor.scanwatch_2_batterij","name": "ScanWatch 2 Batterij", "icon": "mdi:battery"},
            ],
        },
    ],
}

# ─────────────────────────────────────────────
# SECTION 7 — NETWORK STATUS
# ─────────────────────────────────────────────
network_note = md(
    "## 🌐 Netwerkstatus\n"
    "*Live statistieken van uw ASUS RT-AX57 router. "
    "Download- en uploadsnelheden worden automatisch bijgewerkt. "
    "Als WAN **offline** weergeeft, is uw internetverbinding verbroken — "
    "camera's blijven lokaal opnemen maar externe toegang en FTP-upload zullen mislukken.*"
)

network_entities = {
    "type": "entities",
    "title": "ASUS RT-AX57 Router",
    "entities": [
        {"entity": "binary_sensor.rt_ax57_02b8_wan_status",    "name": "Internet (WAN)",     "icon": "mdi:wan"},
        {"entity": "sensor.rt_ax57_02b8_extern_ip",            "name": "Extern IP",          "icon": "mdi:ip-network"},
        {"entity": "sensor.rt_ax57_02b8_downloadsnelheid",     "name": "Downloadsnelheid",   "icon": "mdi:download"},
        {"entity": "sensor.rt_ax57_02b8_uploadsnelheid",       "name": "Uploadsnelheid",     "icon": "mdi:upload"},
    ],
}


# ─────────────────────────────────────────────
# MORNING TAB — Withings Health & Body Metrics
# ─────────────────────────────────────────────
morning_intro = md(
    "## 💙 Gezondheid & Lichaamsmetingen\n"
    "*Deze gegevens worden automatisch gesynchroniseerd van uw Withings-apparaten "
    "(BPM Connect, BeamO, Body Scan, ScanWatch 2). "
    "Tik op een meting om de historische grafiek te bekijken.*"
)

morning_view = {
    "title": "Ochtend",
    "path": "morning",
    "icon": "mdi:weather-sunrise",
    # No "type" key → defaults to Masonry layout.
    # Cards are top-level so Masonry distributes them freely across columns.
    "background": "var(--background-image)",
    "cards": [
        # ── Full-width intro (Masonry places one card per row when it fills a slot) ─
        morning_intro,

        # ── Vitals — Masonry column 1 ────────────────────────────────────────────
        {
            "type": "entities",
            "title": "❤️ Vitale waarden",
            "entities": [
                {"entity": "sensor.withings_hartslag",              "name": "Hartslag",                "icon": "mdi:heart-pulse"},
                {"entity": "sensor.withings_hartslag_2",            "name": "Hartslag #2",              "icon": "mdi:heart-pulse"},
                {"type": "divider"},
                {"entity": "sensor.withings_systolische_bloeddruk", "name": "Bloeddruk (Sys)",          "icon": "mdi:blood-bag"},
                {"entity": "sensor.withings_diastolische_bloeddruk","name": "Bloeddruk (Dia)",          "icon": "mdi:blood-bag"},
                {"type": "divider"},
                {"entity": "sensor.withings_spo2",                  "name": "SpO2",                     "icon": "mdi:oxygen-cylinder"},
                {"entity": "sensor.withings_spo2_2",                "name": "SpO2 #2",                  "icon": "mdi:oxygen-cylinder"},
                {"type": "divider"},
                {"entity": "sensor.withings_gewicht",               "name": "Gewicht",                  "icon": "mdi:scale-bathroom"},
                {"entity": "sensor.withings_lichaamstemperatuur",   "name": "Lichaamstemperatuur",       "icon": "mdi:thermometer"},
                {"entity": "sensor.withings_huidtemperatuur",       "name": "Huidtemperatuur",           "icon": "mdi:thermometer-lines"},
                {"entity": "sensor.withings_temperatuur",           "name": "Omgevingstemperatuur",      "icon": "mdi:thermometer"},
            ],
        },

        # ── Activity: ScanWatch Device 1 — Masonry column 2 ─────────────────────
        {
            "type": "entities",
            "title": "🏃 Activiteit — ScanWatch 2 (Apparaat 1)",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag",                    "name": "Stappen Vandaag",    "icon": "mdi:shoe-print"},
                {"entity": "sensor.withings_stap_doelstelling",                  "name": "Stappendoel",        "icon": "mdi:flag-checkered"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand",          "name": "Afstand Vandaag",    "icon": "mdi:map-marker-distance"},
                {"entity": "sensor.withings_hoogteverschil_vandaag",             "name": "Hoogteverschil",     "icon": "mdi:elevation-rise"},
                {"entity": "sensor.withings_actief_gespendeerde_tijd_vandaag",   "name": "Actieve Tijd",       "icon": "mdi:timer"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand", "name": "Actieve Calorieën",  "icon": "mdi:fire"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand",  "name": "Totale Calorieën",   "icon": "mdi:fire-circle"},
            ],
        },

        # ── Activity: ScanWatch — Masonry column 3 ─────────────────────
        {
            "type": "entities",
            "title": "🏃 Activiteit — ScanWatch 2",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag_2",                   "name": "Stappen Vandaag",    "icon": "mdi:shoe-print"},
                {"entity": "sensor.withings_stap_doelstelling_2",                 "name": "Stappendoel",        "icon": "mdi:flag-checkered"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand_2",         "name": "Afstand Vandaag",    "icon": "mdi:map-marker-distance"},
                {"entity": "sensor.withings_hoogteverschil_vandaag_2",            "name": "Hoogteverschil",     "icon": "mdi:elevation-rise"},
                {"entity": "sensor.withings_actief_gespendeerde_tijd_vandaag_2",  "name": "Actieve Tijd",       "icon": "mdi:timer"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand_2","name": "Actieve Calorieën",  "icon": "mdi:fire"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand_2", "name": "Totale Calorieën",   "icon": "mdi:fire-circle"},
            ],
        },

        # ── Device batteries — Masonry fills the shortest column ─────────────────
        {
            "type": "entities",
            "title": "🔋 Apparaatstatus",
            "entities": [
                {"entity": "sensor.beamo_batterij",       "name": "BeamO Batterij",       "icon": "mdi:battery"},
                {"entity": "sensor.body_scan_batterij",   "name": "Body Scan Batterij",   "icon": "mdi:battery"},
                {"entity": "sensor.bpm_connect_batterij", "name": "BPM Connect Batterij", "icon": "mdi:battery"},
                {"entity": "sensor.scanwatch_2_batterij", "name": "ScanWatch 2 Batterij", "icon": "mdi:battery"},
            ],
        },
    ],
}

MAATING_URL_PATH = "dashboard-maating"

maating_config = {
    "title": "Ochtend",
    "views": [morning_view],
}

# ─────────────────────────────────────────────
# MAIN OVERVIEW DASHBOARD  (camera-free)
# ─────────────────────────────────────────────
overview_config = {
    "title": "Beveiliging & Gezondheid",
    "views": [
        {
            "title": "Overzicht",
            "path": "default_view",
            "background": "var(--background-image)",
            "cards": [
                # ── Clock & Weather ──────────────────────────────
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
                },

                # ── Section 1: Quick Status ──────────────────────
                quick_status_note,
                quick_status_glance,

                # ── Section 2: Security & Alerts ─────────────────
                security_note,
                security_entities,

                # ── Section 3: Health Monitor ────────────────────
                health_note,
                health_grid,

                # ── Section 4: Network Status ────────────────────
                network_note,
                network_entities,

            ],
        },
    ],
}

# ─────────────────────────────────────────────
# CAMERAS DASHBOARD  (2 tabs: Front Door / Backside)
# ─────────────────────────────────────────────
CAMERAS_URL_PATH = "dashboard-cameras"

cameras_config = {
    "title": "Camera's",
    "views": [
        camera_view(
            "front_door",
            "Voordeur",
            "front-door",
        ),
        camera_view(
            "backside",
            "Achterkant",
            "backside",
            stack_stream_detection=True,  # forces detection below the stream
        ),
    ],
}


# ─────────────────────────────────────────────
# PUSH ALL DASHBOARDS VIA WEBSOCKET
# Message sequence:
#   id=1  lovelace/config          → read default (confirm storage mode)
#   id=2  lovelace/config/save     → update overview (no url_path = default)
#   id=3  lovelace/dashboards/list → check if cameras dashboard exists
#   id=4  lovelace/dashboards/create (if needed)
#   id=5  lovelace/config/save (url_path=cameras) → write cameras config
#   id=6  lovelace/config/save (url_path=maating) → write health config
# ─────────────────────────────────────────────
def push_dashboards():
    print("=" * 55)
    print("  Pushing dashboards to Home Assistant")
    print("=" * 55)
    print(f"  WebSocket : {WS_URL}")
    print(f"  Overview  : {len(overview_config['views'][0]['cards'])} cards")
    print(f"  Cameras   : {len(cameras_config['views'])} tabs")
    print(f"  Maating   : {len(maating_config['views'][0]['cards'])} cards (health)")
    print()

    state  = {}   # track progress between steps
    results = {}

    def send(ws, payload):
        ws.send(json.dumps(payload))

    def on_open(ws):
        pass

    def on_message(ws, raw):
        msg      = json.loads(raw)
        msg_type = msg.get("type")

        # ── AUTH ──────────────────────────────────────
        if msg_type == "auth_required":
            print("  → Authenticating...")
            send(ws, {"type": "auth", "access_token": TOKEN})

        elif msg_type == "auth_ok":
            print(f"  ✓ Authenticated  (HA {msg.get('ha_version', '?')})")
            # Step 1: probe default config
            send(ws, {"id": 1, "type": "lovelace/config", "force": False})

        elif msg_type == "auth_invalid":
            print("  ✗ Authentication failed — check your long-lived token.")
            results["error"] = "auth_invalid"
            ws.close()

        # ── RESULTS ───────────────────────────────────
        elif msg_type == "result":
            msg_id  = msg.get("id")
            success = msg.get("success", False)

            # ─ id=1: probe overview config ─
            if msg_id == 1:
                if success:
                    print("  ✓ Default dashboard is in storage mode")
                else:
                    err = msg.get("error", {})
                    print(f"  ⚠ Probe: {err.get('code','?')} — proceeding anyway...")

                print("  → [1/3] Saving Overview dashboard (camera sections removed)...")
                send(ws, {
                    "id": 2,
                    "type": "lovelace/config/save",
                    "config": overview_config,
                })

            # ─ id=2: overview saved ─
            elif msg_id == 2:
                if success:
                    print("  ✓ Overview dashboard saved.")
                    print("  → [2/3] Listing existing dashboards...")
                    send(ws, {"id": 3, "type": "lovelace/dashboards/list"})
                else:
                    err = msg.get("error", {})
                    print(f"  ✗ Overview save failed: {err.get('code','?')} — {err.get('message','')}")
                    results["error"] = "overview_save"
                    ws.close()

            # ─ id=3: dashboard list ─
            elif msg_id == 3:
                if success:
                    existing = [d.get("url_path") for d in (msg.get("result") or [])]
                    print(f"  ✓ Found {len(existing)} dashboard(s): {existing or '(none)'}")

                    if CAMERAS_URL_PATH in existing:
                        # Dashboard already exists — skip create, go straight to save
                        print("  ℹ Cameras dashboard already exists — skipping create.")
                        state["skip_create"] = True
                        print("  → [3/3] Saving Cameras dashboard config...")
                        send(ws, {
                            "id": 5,
                            "type": "lovelace/config/save",
                            "url_path": CAMERAS_URL_PATH,
                            "config": cameras_config,
                        })
                    else:
                        print("  → [3/3a] Creating Cameras dashboard entry...")
                        send(ws, {
                            "id": 4,
                            "type": "lovelace/dashboards/create",
                            "url_path": CAMERAS_URL_PATH,
                            "title": "Camera's",
                            "icon": "mdi:cctv",
                            "show_in_sidebar": True,
                            "require_admin": False,
                        })
                else:
                    err = msg.get("error", {})
                    print(f"  ⚠ Could not list dashboards ({err.get('code','?')}), attempting create anyway...")
                    send(ws, {
                        "id": 4,
                        "type": "lovelace/dashboards/create",
                        "url_path": CAMERAS_URL_PATH,
                        "title": "Camera's",
                        "icon": "mdi:cctv",
                        "show_in_sidebar": True,
                        "require_admin": False,
                    })

            # ─ id=4: dashboard created ─
            elif msg_id == 4:
                if success:
                    print("  ✓ Cameras dashboard entry created.")
                else:
                    err = msg.get("error", {})
                    # 'already_exists' is non-fatal
                    if err.get("code") == "already_exists":
                        print("  ℹ Cameras dashboard already existed.")
                    else:
                        print(f"  ⚠ Create warning: {err.get('code','?')} — {err.get('message','')}")

                print("  → [3/3b] Saving Cameras dashboard config (2 tabs)...")
                send(ws, {
                    "id": 5,
                    "type": "lovelace/config/save",
                    "url_path": CAMERAS_URL_PATH,
                    "config": cameras_config,
                })

            # ─ id=5: cameras config saved ─
            elif msg_id == 5:
                if success:
                    print("  ✓ Cameras dashboard config saved (Front Door + Backside tabs).")
                    print("  → [3/3] Saving Maating health dashboard config...")
                    send(ws, {
                        "id": 6,
                        "type": "lovelace/config/save",
                        "url_path": MAATING_URL_PATH,
                        "config": maating_config,
                    })
                else:
                    err = msg.get("error", {})
                    code   = err.get("code", "?")
                    detail = err.get("message", "")
                    print(f"  ✗ Cameras config save failed: {code} — {detail}")
                    results["error"] = code
                    ws.close()

            # ─ id=6: maating health config saved ─
            elif msg_id == 6:
                if success:
                    print("  ✓ Maating health dashboard config saved.")
                    results["all_saved"] = True
                else:
                    err = msg.get("error", {})
                    code   = err.get("code", "?")
                    detail = err.get("message", "")
                    print(f"  ✗ Maating config save failed: {code} — {detail}")
                    results["error"] = code
                ws.close()

        elif msg_type == "event":
            pass

    def on_error(ws, error):
        print(f"  ✗ WebSocket error: {error}")
        results["error"] = str(error)

    def on_close(ws, code, msg):
        print()
        print("=" * 55)
        if results.get("all_saved"):
            print("  ✓ ALL DONE — All 3 dashboards are live!")
            print()
            print("  Next steps:")
            print("  1. Press F5 in your HA browser tab to reload.")
            print("  2. 'Maating' sidebar dashboard now shows Withings health data.")
            print("  3. The 'Cameras' item remains in the sidebar.")
            print("     (Settings → Dashboards if you don't see it yet)")
        else:
            print("  ✗ Push did not complete fully — see errors above.")
        print("=" * 55)

    ws_app = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    try:
        ws_app.run_forever(ping_interval=20, ping_timeout=10)
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\n✗ Could not connect: {e}")
        print("  Is Home Assistant running at homeassistant.local:8123?")


if __name__ == "__main__":
    push_dashboards()

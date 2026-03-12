import json
import time
import websocket  # websocket-client

BASE_URL  = "http://homeassistant.local:8123"
WS_URL    = "ws://homeassistant.local:8123/api/websocket"
TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJhN2Y5ZWYwMzdhYzU0NDZkODU3MzYyYWY2ZGIyMDViNSIsImlhdCI"
    "6MTc3MjYzODQwMCwiZXhwIjoyMDg3OTk4NDAwfQ"
    ".c_EYV8TB3j6vdVt7FVN1_z_gFAuIl44mhm-4XD6cZXA"
)

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
    "## 🔴 Security Overview\n"
    "*This row shows your most critical live states at a glance. "
    "Any badge highlighted in red requires immediate attention.*"
)

quick_status_glance = {
    "type": "glance",
    "title": "Live Security Status",
    "show_name": True,
    "show_icon": True,
    "show_state": True,
    "entities": [
        {"entity": "binary_sensor.front_door_beweging",  "name": "Front Door Motion", "icon": "mdi:motion-sensor"},
        {"entity": "binary_sensor.backside_beweging",    "name": "Backside Motion",   "icon": "mdi:motion-sensor"},
        {"entity": "binary_sensor.front_door_persoon",  "name": "Person (Front)",    "icon": "mdi:account-alert"},
        {"entity": "binary_sensor.backside_persoon",    "name": "Person (Back)",     "icon": "mdi:account-alert"},
        {"entity": "binary_sensor.rt_ax57_02b8_wan_status", "name": "Internet WAN",  "icon": "mdi:wan"},
        {"entity": "binary_sensor.deur_detection",      "name": "Door Sensor",       "icon": "mdi:door-open"},
        {"entity": "binary_sensor.rookmelder",          "name": "Smoke Detector",    "icon": "mdi:smoke-detector"},
        {"entity": "binary_sensor.sos_wall_button",     "name": "SOS Wall Button",   "icon": "mdi:alert-circle"},
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
        "title": "Live Detection",
        "show_name": True,
        "show_icon": True,
        "show_state": True,
        "entities": [
            {"entity": f"binary_sensor.{prefix}_beweging", "name": "Motion",    "icon": "mdi:motion-sensor"},
            {"entity": f"binary_sensor.{prefix}_persoon",  "name": "Person",    "icon": "mdi:account-alert"},
            {"entity": f"binary_sensor.{prefix}_dier",     "name": "Pet",       "icon": "mdi:paw"},
            {"entity": f"binary_sensor.{prefix}_baby_huilt","name": "Baby Cry", "icon": "mdi:baby-face"},
            {"entity": f"sensor.{prefix}_dag_nacht_status", "name": "Day/Night", "icon": "mdi:weather-sunset"},
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
        "title": f"{label} — Toggles & Settings",
        "entities": [
            {"entity": f"switch.{prefix}_opnemen",               "name": "Recording"},
            {"entity": f"switch.{prefix}_geluid_opnemen",        "name": "Record Audio"},
            {"entity": f"switch.{prefix}_privacymodus",          "name": "Privacy Mode"},
            {"entity": f"switch.{prefix}_automatisch_volgen",    "name": "Auto-Track"},
            {"entity": f"switch.{prefix}_push_notificaties",     "name": "Push Notifications"},
            {"entity": f"switch.{prefix}_e_mail_bij_gebeurtenis","name": "Email on Event"},
            {"entity": f"switch.{prefix}_ftp_uploaden",          "name": "FTP Upload"},
            {"entity": f"switch.{prefix}_infrared_lights_in_night_mode", "name": "Night IR Lights"},
            {"entity": f"switch.{prefix}_sirene_bij_gebeurtenis","name": "Siren on Event"},
            {"entity": f"switch.{prefix}_bewaak_punt_terugkeren","name": "Return to Guard Point"},
            {"entity": f"select.{prefix}_dag_nacht_modus",       "name": "Day/Night Mode"},
            {"entity": f"number.{prefix}_ai_persoon_gevoeligheid","name": "Person AI Sensitivity"},
            {"entity": f"number.{prefix}_ai_huisdier_gevoeligheid","name": "Pet AI Sensitivity"},
            {"entity": f"number.{prefix}_beweging_gevoeligheid", "name": "Motion Sensitivity"},
            {"entity": f"number.{prefix}_volume",                "name": "Volume"},
            {"entity": f"number.{prefix}_baby_cry_sensitivity",  "name": "Baby Cry Sensitivity"},
            {"entity": f"number.{prefix}_bewaak_punt_terugkeertijd","name": "Guard Return Delay (s)"},
            {"entity": f"sensor.{prefix}_dag_nacht_status",      "name": "Current Day/Night Status"},
            {"entity": f"button.{prefix}_bewaak_punt_zet_huidige_positie","name": "Set Guard Point Here"},
            {"entity": f"button.{prefix}_bewaak_punt_ga_naar",   "name": "Go to Guard Point"},
            {"entity": f"button.{prefix}_ptz_kalibreren",        "name": "Calibrate PTZ"},
            {"entity": f"light.{prefix}_status_led",             "name": "Status LED"},
            {"entity": f"siren.{prefix}_sirene",                 "name": "Siren (manual)"},
        ],
    }


# ─────────────────────────────────────────────
# BUILD A SINGLE CAMERA TAB VIEW
# ─────────────────────────────────────────────
def camera_view(prefix, label, path, extra_note="", stack_stream_detection=False):
    note_text = (
        f"## 📹 {label} Camera\n"
        "*PTZ buttons pan and tilt the camera in real time. "
        "**Auto-Track** makes the camera follow detected movement. "
        "**Privacy Mode** immediately freezes the stream and disables recording. "
        "Sensitivity sliders take effect on the next detected event.*"
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
            md("### PTZ Control"),# card 3 — PTZ header
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
            md("### PTZ Control"),            # card 4 — PTZ header
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
    "## 🚨 Security & Alerts\n"
    "*Smoke detector, door sensor, SOS buttons, and fall-detection radar. "
    "Devices showing **UNAVAILABLE** are Zigbee-based — check the Home Assistant Connect ZBT-2 "
    "coordinator is powered and the Zigbee integration is running. "
    "The sirens below can be triggered manually in an emergency.*"
)

security_entities = {
    "type": "entities",
    "title": "Security Devices",
    "entities": [
        {"entity": "binary_sensor.rookmelder",                   "name": "Smoke Detector",       "icon": "mdi:smoke-detector-alert"},
        {"entity": "sensor.rookmelder_rookdichtheid",            "name": "Smoke Density"},
        {"entity": "sensor.rookmelder_batterij",                 "name": "Smoke Detector Battery","icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.deur_detection",               "name": "Door Sensor",          "icon": "mdi:door-open"},
        {"entity": "binary_sensor.deur_detection_sabotage",      "name": "Door Sensor Tamper",   "icon": "mdi:shield-alert"},
        {"entity": "sensor.deur_detection_batterij",             "name": "Door Sensor Battery",  "icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.sos_wall_button",              "name": "SOS Wall Button",      "icon": "mdi:alarm-light"},
        {"entity": "sensor.sos_wall_button_batterij",            "name": "SOS Wall Button Battery","icon": "mdi:battery"},
        {"entity": "binary_sensor.tz3000_p3fph1go_ts0215a",     "name": "SOS Carry Button",     "icon": "mdi:alarm-light"},
        {"entity": "sensor.tz3000_p3fph1go_ts0215a_batterij",   "name": "SOS Carry Battery",    "icon": "mdi:battery"},
        {"type": "divider"},
        {"entity": "binary_sensor.seeed_studio_mr60fda2_kit_8f65d0_falling_information", "name": "Fall Detected", "icon": "mdi:human-cane"},
        {"entity": "binary_sensor.seeed_studio_mr60fda2_kit_8f65d0_person_information",  "name": "Person in Room","icon": "mdi:account"},
        {"type": "divider"},
        {"entity": "siren.front_door_sirene",  "name": "Front Door Siren (Manual)", "icon": "mdi:alarm-bell"},
        {"entity": "siren.backside_sirene",    "name": "Backside Siren (Manual)",   "icon": "mdi:alarm-bell"},
        {"type": "divider"},
        {"entity": "automation.siren_webhoek", "name": "Webhook → Siren Automation", "icon": "mdi:webhook"},
    ],
}

# ─────────────────────────────────────────────
# SECTION 6 — HEALTH MONITOR
# ─────────────────────────────────────────────
health_note = md(
    "## ❤️ Health Monitor\n"
    "*Data from your Withings devices: BeamO, BPM Connect, ScanWatch 2, and Body Scan. "
    "Values update after each measurement sync — they do not stream in real-time. "
    "Blood pressure and SpO2 reflect the most recent logged reading.*"
)

health_grid = {
    "type": "grid",
    "columns": 2,
    "square": False,
    "cards": [
        {
            "type": "entities",
            "title": "Vitals",
            "entities": [
                {"entity": "sensor.withings_hartslag",           "name": "Heart Rate (BPM)"},
                {"entity": "sensor.withings_hartslag_2",         "name": "Heart Rate #2"},
                {"entity": "sensor.withings_systolische_bloeddruk", "name": "Blood Pressure (Systolic)"},
                {"entity": "sensor.withings_diastolische_bloeddruk","name": "Blood Pressure (Diastolic)"},
                {"entity": "sensor.withings_spo2",               "name": "SpO2 (%)"},
                {"entity": "sensor.withings_spo2_2",             "name": "SpO2 #2 (%)"},
                {"entity": "sensor.withings_lichaamstemperatuur", "name": "Body Temperature (°C)"},
                {"entity": "sensor.withings_huidtemperatuur",    "name": "Skin Temperature (°C)"},
                {"entity": "sensor.withings_temperatuur",        "name": "Ambient Temperature (°C)"},
                {"entity": "sensor.withings_gewicht",            "name": "Weight (kg)"},
            ],
        },
        {
            "type": "entities",
            "title": "Activity & Batteries",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag",      "name": "Steps Today"},
                {"entity": "sensor.withings_stap_doelstelling",    "name": "Step Goal"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand","name": "Distance Today"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand","name": "Active Calories"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand","name": "Total Calories"},
                {"type": "divider"},
                {"entity": "sensor.beamo_batterij",      "name": "BeamO Battery",      "icon": "mdi:battery"},
                {"entity": "sensor.body_scan_batterij",  "name": "Body Scan Battery",  "icon": "mdi:battery"},
                {"entity": "sensor.bpm_connect_batterij","name": "BPM Connect Battery","icon": "mdi:battery"},
                {"entity": "sensor.scanwatch_2_batterij","name": "ScanWatch 2 Battery","icon": "mdi:battery"},
            ],
        },
    ],
}

# ─────────────────────────────────────────────
# SECTION 7 — NETWORK STATUS
# ─────────────────────────────────────────────
network_note = md(
    "## 🌐 Network Status\n"
    "*Live stats from your ASUS RT-AX57 router. "
    "Download and upload speeds refresh automatically. "
    "If WAN shows **offline**, your internet connection is down — "
    "cameras will still record locally but remote access and FTP upload will fail.*"
)

network_entities = {
    "type": "entities",
    "title": "ASUS RT-AX57 Router",
    "entities": [
        {"entity": "binary_sensor.rt_ax57_02b8_wan_status",    "name": "Internet (WAN)",    "icon": "mdi:wan"},
        {"entity": "sensor.rt_ax57_02b8_extern_ip",            "name": "External IP",       "icon": "mdi:ip-network"},
        {"entity": "sensor.rt_ax57_02b8_downloadsnelheid",     "name": "Download Speed",    "icon": "mdi:download"},
        {"entity": "sensor.rt_ax57_02b8_uploadsnelheid",       "name": "Upload Speed",      "icon": "mdi:upload"},
    ],
}


# ─────────────────────────────────────────────
# MORNING TAB — Withings Health & Body Metrics
# ─────────────────────────────────────────────
morning_intro = md(
    "## 💙 Health & Body Metrics\n"
    "*This data syncs automatically from your Withings devices "
    "(BPM Connect, BeamO, Body Scan, ScanWatch 2). "
    "Tap on any metric to see your historical graph.*"
)

morning_view = {
    "title": "Morning",
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
            "title": "❤️ Vitals",
            "entities": [
                {"entity": "sensor.withings_hartslag",              "name": "Heart Rate",           "icon": "mdi:heart-pulse"},
                {"entity": "sensor.withings_hartslag_2",            "name": "Heart Rate #2",         "icon": "mdi:heart-pulse"},
                {"type": "divider"},
                {"entity": "sensor.withings_systolische_bloeddruk", "name": "Blood Pressure (Sys)",  "icon": "mdi:blood-bag"},
                {"entity": "sensor.withings_diastolische_bloeddruk","name": "Blood Pressure (Dia)",  "icon": "mdi:blood-bag"},
                {"type": "divider"},
                {"entity": "sensor.withings_spo2",                  "name": "SpO2",                  "icon": "mdi:oxygen-cylinder"},
                {"entity": "sensor.withings_spo2_2",                "name": "SpO2 #2",               "icon": "mdi:oxygen-cylinder"},
                {"type": "divider"},
                {"entity": "sensor.withings_gewicht",               "name": "Weight",                "icon": "mdi:scale-bathroom"},
                {"entity": "sensor.withings_lichaamstemperatuur",   "name": "Body Temperature",      "icon": "mdi:thermometer"},
                {"entity": "sensor.withings_huidtemperatuur",       "name": "Skin Temperature",      "icon": "mdi:thermometer-lines"},
                {"entity": "sensor.withings_temperatuur",           "name": "Ambient Temperature",   "icon": "mdi:thermometer"},
            ],
        },

        # ── Activity: ScanWatch Device 1 — Masonry column 2 ─────────────────────
        {
            "type": "entities",
            "title": "🏃 Activity — ScanWatch 2 (Device 1)",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag",                    "name": "Steps Today",    "icon": "mdi:shoe-print"},
                {"entity": "sensor.withings_stap_doelstelling",                  "name": "Step Goal",      "icon": "mdi:flag-checkered"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand",          "name": "Distance Today", "icon": "mdi:map-marker-distance"},
                {"entity": "sensor.withings_hoogteverschil_vandaag",             "name": "Altitude Change","icon": "mdi:elevation-rise"},
                {"entity": "sensor.withings_actief_gespendeerde_tijd_vandaag",   "name": "Active Time",    "icon": "mdi:timer"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand", "name": "Active Calories","icon": "mdi:fire"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand",  "name": "Total Calories", "icon": "mdi:fire-circle"},
            ],
        },

        # ── Activity: ScanWatch — Masonry column 3 ─────────────────────
        {
            "type": "entities",
            "title": "🏃 Activity — ScanWatch 2",
            "entities": [
                {"entity": "sensor.withings_stappen_vandaag_2",                   "name": "Steps Today",    "icon": "mdi:shoe-print"},
                {"entity": "sensor.withings_stap_doelstelling_2",                 "name": "Step Goal",      "icon": "mdi:flag-checkered"},
                {"entity": "sensor.withings_vandaag_afgelegde_afstand_2",         "name": "Distance Today", "icon": "mdi:map-marker-distance"},
                {"entity": "sensor.withings_hoogteverschil_vandaag_2",            "name": "Altitude Change","icon": "mdi:elevation-rise"},
                {"entity": "sensor.withings_actief_gespendeerde_tijd_vandaag_2",  "name": "Active Time",    "icon": "mdi:timer"},
                {"entity": "sensor.withings_actieve_calorieen_vandaag_verbrand_2","name": "Active Calories","icon": "mdi:fire"},
                {"entity": "sensor.withings_totale_calorieen_vandaag_verbrand_2", "name": "Total Calories", "icon": "mdi:fire-circle"},
            ],
        },

        # ── Device batteries — Masonry fills the shortest column ─────────────────
        {
            "type": "entities",
            "title": "🔋 Device Status",
            "entities": [
                {"entity": "sensor.beamo_batterij",       "name": "BeamO Battery",       "icon": "mdi:battery"},
                {"entity": "sensor.body_scan_batterij",   "name": "Body Scan Battery",   "icon": "mdi:battery"},
                {"entity": "sensor.bpm_connect_batterij", "name": "BPM Connect Battery", "icon": "mdi:battery"},
                {"entity": "sensor.scanwatch_2_batterij", "name": "ScanWatch 2 Battery", "icon": "mdi:battery"},
            ],
        },
    ],
}

MAATING_URL_PATH = "dashboard-maating"

maating_config = {
    "title": "Morning",
    "views": [morning_view],
}

# ─────────────────────────────────────────────
# MAIN OVERVIEW DASHBOARD  (camera-free)
# ─────────────────────────────────────────────
overview_config = {
    "title": "Security & Health",
    "views": [
        {
            "title": "Overview",
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
    "title": "Cameras",
    "views": [
        camera_view(
            "front_door",
            "Front Door",
            "front-door",
        ),
        camera_view(
            "backside",
            "Backside",
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
                            "title": "Cameras",
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
                        "title": "Cameras",
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

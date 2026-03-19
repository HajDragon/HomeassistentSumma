#!/usr/bin/env bash
# =============================================================================
# deploy_to_ha.sh — Simulation Manager full deployment script
#
# Run this script ON your Home Assistant host (Terminal SSH add-on, or
# Studio Code Server terminal). It does NOT need to be run over SSH from
# another machine — just paste it into the HA terminal directly.
#
# Usage:
#   bash deploy_to_ha.sh [OPTIONS]
#
# Options:
#   --zip PATH     Path to simulation_manager_deploy.zip
#                  Default: ./simulation_manager_deploy.zip
#   --config DIR   Path to HA config directory
#                  Default: /config
#   --token STR    Long-lived access token for HA REST API
#   --ha-url URL   Home Assistant base URL
#                  Default: http://localhost:8123
#   --seed         Seed the four Mevrouw Goedheid measurement periods
#   --no-restart   Skip the HA Core restart (useful if already restarted)
#   -h / --help    Show this help text
#
# Typical run (already inside HA terminal, zip in /config):
#   TOKEN="<your token>"
#   cd /config && unzip -o simulation_manager_deploy.zip
#   bash deploy_to_ha.sh --token "$TOKEN" --seed
# =============================================================================

set -euo pipefail

# ── Colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()     { error "$*"; exit 1; }

# ── Default values ─────────────────────────────────────────────────────────────
ZIP_PATH="simulation_manager_deploy.zip"
CONFIG_DIR="/config"
HA_URL="http://localhost:8123"
TOKEN=""
DO_SEED=false
DO_RESTART=true

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --zip)        ZIP_PATH="$2";    shift 2 ;;
    --config)     CONFIG_DIR="$2";  shift 2 ;;
    --token)      TOKEN="$2";       shift 2 ;;
    --ha-url)     HA_URL="$2";      shift 2 ;;
    --seed)       DO_SEED=true;     shift   ;;
    --no-restart) DO_RESTART=false; shift   ;;
    -h|--help)
      sed -n '/^# Usage:/,/^# ====/p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0 ;;
    *) die "Unknown argument: $1. Use -h for help." ;;
  esac
done

# Try reading token from file if not set on command line
if [[ -z "$TOKEN" && -f "$HOME/.ha_token" ]]; then
  TOKEN="$(head -n1 "$HOME/.ha_token" | tr -d '[:space:]')"
  info "Token loaded from ~/.ha_token"
fi

# ── Dependency checks ──────────────────────────────────────────────────────────
for cmd in curl unzip python3; do
  command -v "$cmd" &>/dev/null || die "'$cmd' is required but not found."
done

# ── Verify inputs ──────────────────────────────────────────────────────────────
[[ -f "$ZIP_PATH" ]]   || die "Zip file not found: $ZIP_PATH"
[[ -d "$CONFIG_DIR" ]] || die "Config directory not found: $CONFIG_DIR"
[[ -n "$TOKEN" ]]      || die "No token provided. Use --token YOUR_TOKEN"

HEADERS=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Simulation Manager — Deployment Script${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════════${NC}"
echo ""
info "Zip file  : $ZIP_PATH"
info "HA config : $CONFIG_DIR"
info "HA URL    : $HA_URL"
info "Seed data : $DO_SEED"
echo ""

# =============================================================================
# STEP 1 — Extract files from zip
# =============================================================================
echo -e "${BOLD}STEP 1 — Extracting integration & card files${NC}"

INTEGRATION_DIR="$CONFIG_DIR/custom_components/simulation_manager"
CARD_DIR="$CONFIG_DIR/www/simulation-period-card"

mkdir -p "$INTEGRATION_DIR" "$CARD_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

unzip -q "$ZIP_PATH" -d "$TMP_DIR"

cp -v "$TMP_DIR/custom_components/simulation_manager/"* "$INTEGRATION_DIR/"
cp -v "$TMP_DIR/www/simulation-period-card/simulation-period-card.js" "$CARD_DIR/"

success "Files extracted."
echo ""

# =============================================================================
# STEP 2 — Patch configuration.yaml
# =============================================================================
echo -e "${BOLD}STEP 2 — Updating configuration.yaml${NC}"

CONF_FILE="$CONFIG_DIR/configuration.yaml"

if [[ ! -f "$CONF_FILE" ]]; then
  warn "configuration.yaml not found — creating a minimal one."
  echo "# Home Assistant configuration" > "$CONF_FILE"
fi

if grep -q "^simulation_manager" "$CONF_FILE" 2>/dev/null; then
  success "simulation_manager: already present in configuration.yaml — skipping."
else
  printf '\n# Simulation Manager custom integration\nsimulation_manager:\n' >> "$CONF_FILE"
  success "Added 'simulation_manager:' to configuration.yaml."
fi
echo ""

# =============================================================================
# STEP 3 — Restart Home Assistant Core
# =============================================================================
if [[ "$DO_RESTART" == "true" ]]; then
  echo -e "${BOLD}STEP 3 — Restarting Home Assistant Core${NC}"

  if command -v ha &>/dev/null; then
    info "Using 'ha core restart' (Supervisor CLI)..."
    ha core restart
  else
    info "Using REST API to restart HA Core..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "${HA_URL}/api/services/homeassistant/restart" \
      "${HEADERS[@]}")
    [[ "$HTTP_CODE" == "200" ]] || die "Restart request failed (HTTP $HTTP_CODE)."
  fi

  info "Waiting for HA to come back online (max 120 s)..."
  TIMEOUT=120
  ELAPSED=0
  # /manifest.json is served as soon as the HTTP stack is up — much earlier
  # than /api/ which waits for the full integration stack to initialise.
  until curl -sf -o /dev/null "${HA_URL}/manifest.json"; do
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    [[ $ELAPSED -ge $TIMEOUT ]] && die "HA did not come back online within ${TIMEOUT}s."
    info "  ...still waiting (${ELAPSED}s)"
  done
  # Brief extra wait for the API layer to finish loading after HTTP is up
  sleep 5
  success "Home Assistant is back online."
else
  warn "STEP 3 — Restart skipped (--no-restart flag set)."
fi
echo ""

# =============================================================================
# STEP 4 — Register Lovelace JS resource
# =============================================================================
echo -e "${BOLD}STEP 4 — Registering Lovelace card resource${NC}"

CARD_URL="/local/simulation-period-card/simulation-period-card.js"

RESOURCES=$(curl -sf "${HA_URL}/api/lovelace/resources" "${HEADERS[@]}" || echo "[]")

if echo "$RESOURCES" | python3 -c "
import sys, json
res = json.load(sys.stdin)
sys.exit(0 if any(r.get('url') == '$CARD_URL' for r in res) else 1)
" 2>/dev/null; then
  success "Lovelace resource already registered — skipping."
else
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${HA_URL}/api/lovelace/resources" \
    "${HEADERS[@]}" \
    -d "{\"res_type\":\"module\",\"url\":\"${CARD_URL}\"}")

  if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
    success "Lovelace resource registered: $CARD_URL"
  else
    warn "Could not auto-register resource (HTTP $HTTP_CODE)."
    warn "Add manually: Settings → Dashboards → Resources → Add"
    warn "  URL:  $CARD_URL  |  Type: JavaScript Module"
  fi
fi
echo ""

# =============================================================================
# STEP 5 — Verify sensor entity
# =============================================================================
echo -e "${BOLD}STEP 5 — Verifying sensor.simulation_manager${NC}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "${HA_URL}/api/states/sensor.simulation_manager" \
  "${HEADERS[@]}")

if [[ "$HTTP_CODE" == "200" ]]; then
  success "sensor.simulation_manager found — integration is running."
else
  die "sensor.simulation_manager not found (HTTP $HTTP_CODE). Check: Settings → System → Logs"
fi
echo ""

# =============================================================================
# STEP 6 (optional) — Seed Mevrouw Goedheid simulation data (6 periods)
# =============================================================================

_svc() {
  local svc="$1" payload="$2"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${HA_URL}/api/services/simulation_manager/${svc}" \
    "${HEADERS[@]}" -d "$payload")
  [[ "$HTTP_CODE" == "200" ]] || warn "Service $svc returned HTTP $HTTP_CODE"
  sleep 0.3
}

if [[ "$DO_SEED" == "true" ]]; then
  echo -e "${BOLD}STEP 6 — Seeding simulation data (match dashboard)${NC}"

  info "Resetting existing simulation state..."
  _svc "reset_simulation" "{}"

  _svc "switch_period"    '{"period_id":"period_1","label":"Meting 1 (start)","date":"2026-03-01"}'
  _svc "save_measurement" '{"gewicht":68.0,"bloeddruk":"130/80 mmHg","hartfrequentie":72,"ademfrequentie":16,"saturatie":96,"opmerking":"Stabiele situatie na ontslag","timestamp":"2026-03-01T09:00:00+00:00"}'
  success "Meting 1 (start) — 2026-03-01 — seeded."

  _svc "switch_period"    '{"period_id":"period_2","label":"Meting 2 (2 mnd)","date":"2026-03-04"}'
  _svc "save_measurement" '{"gewicht":68.2,"bloeddruk":"132/82 mmHg","hartfrequentie":74,"ademfrequentie":16,"saturatie":96,"opmerking":"Geen klachten","timestamp":"2026-03-04T09:00:00+00:00"}'
  success "Meting 2 (2 mnd) — 2026-03-04 — seeded."

  _svc "switch_period"    '{"period_id":"period_3","label":"Meting 3 (4 mnd)","date":"2026-03-08"}'
  _svc "save_measurement" '{"gewicht":68.7,"bloeddruk":"135/85 mmHg","hartfrequentie":78,"ademfrequentie":17,"saturatie":95,"opmerking":"Licht vermoeid","timestamp":"2026-03-08T09:00:00+00:00"}'
  success "Meting 3 (4 mnd) — 2026-03-08 — seeded."

  _svc "switch_period"    '{"period_id":"period_4","label":"Meting 4 (6 mnd)","date":"2026-03-11"}'
  _svc "save_measurement" '{"gewicht":69.3,"bloeddruk":"138/86 mmHg","hartfrequentie":80,"ademfrequentie":18,"saturatie":95,"opmerking":"Enkels licht gezwollen","timestamp":"2026-03-11T09:00:00+00:00"}'
  success "Meting 4 (6 mnd) — 2026-03-11 — seeded."

  _svc "switch_period"    '{"period_id":"period_5","label":"Meting 5 (8 mnd)","date":"2026-03-15"}'
  _svc "save_measurement" '{"gewicht":70.1,"bloeddruk":"142/88 mmHg","hartfrequentie":86,"ademfrequentie":19,"saturatie":94,"opmerking":"Kortademig bij inspanning","timestamp":"2026-03-15T09:00:00+00:00"}'
  success "Meting 5 (8 mnd) — 2026-03-15 — seeded."

  _svc "switch_period"    '{"period_id":"period_6","label":"Meting 6 (10 mnd)","date":"2026-03-18"}'
  _svc "save_measurement" '{"gewicht":70.8,"bloeddruk":"145/90 mmHg","hartfrequentie":90,"ademfrequentie":20,"saturatie":94,"opmerking":"Meer oedeem in onderbenen","timestamp":"2026-03-18T09:00:00+00:00"}'
  success "Meting 6 (10 mnd) — 2026-03-18 — seeded."

  _svc "switch_period"    '{"period_id":"period_7","label":"Meting 7","date":"2026-03-22"}'
  _svc "save_measurement" '{"gewicht":71.5,"bloeddruk":"150/92 mmHg","hartfrequentie":96,"ademfrequentie":21,"saturatie":93,"opmerking":"Gewicht stijgt snel","timestamp":"2026-03-22T09:00:00+00:00"}'
  success "Meting 7 — 2026-03-22 — seeded."

  _svc "switch_period"    '{"period_id":"period_8","label":"Meting 8","date":"2026-03-25"}'
  _svc "save_measurement" '{"gewicht":72.2,"bloeddruk":"155/95 mmHg","hartfrequentie":102,"ademfrequentie":22,"saturatie":92,"opmerking":"Duidelijke verslechtering","timestamp":"2026-03-25T09:00:00+00:00"}'
  success "Meting 8 — 2026-03-25 — seeded."

  _svc "switch_period" '{"period_id":"period_1"}'
  success "Active period set to Meting 1 (start)."
else
  info "STEP 6 — Skipped. Run with --seed to populate Mevrouw Goedheid data."
fi

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Deployment complete!${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Open your dashboard → 'Simulatie Mevrouw Goedheid' view"
echo "  The custom:simulation-period-card should render with period tabs."
echo ""
echo "  Available services (Developer Tools → Services):"
echo "    simulation_manager.switch_period    (period_id, label, date)"
echo "    simulation_manager.save_measurement (gewicht, spiermassa, vetmassa, bmi)"
echo "    simulation_manager.reset_simulation (no parameters)"
echo ""

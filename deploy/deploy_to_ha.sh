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
# STEP 6 (optional) — Seed Mevrouw Goedheid simulation data
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
  echo -e "${BOLD}STEP 6 — Seeding Mevrouw Goedheid simulation data${NC}"

  info "Resetting existing simulation state..."
  _svc "reset_simulation" "{}"

  _svc "switch_period"    '{"period_id":"period_1","label":"Meting 1 (start)","date":"2026-01-01"}'
  _svc "save_measurement" '{"gewicht":70.0,"spiermassa":29.5,"vetmassa":24.0,"bmi":24.8,"timestamp":"2026-01-01T09:00:00+00:00"}'
  success "Meting 1 (start) — 2026-01-01 — seeded."

  _svc "switch_period"    '{"period_id":"period_2","label":"Meting 2 (2 mnd)","date":"2026-03-01"}'
  _svc "save_measurement" '{"gewicht":72.0,"spiermassa":29.3,"vetmassa":25.5,"bmi":25.5,"timestamp":"2026-03-01T09:00:00+00:00"}'
  success "Meting 2 (2 mnd) — 2026-03-01 — seeded."

  _svc "switch_period"    '{"period_id":"period_3","label":"Meting 3 (4 mnd)","date":"2026-05-01"}'
  _svc "save_measurement" '{"gewicht":74.5,"spiermassa":29.0,"vetmassa":27.0,"bmi":26.4,"timestamp":"2026-05-01T09:00:00+00:00"}'
  success "Meting 3 (4 mnd) — 2026-05-01 — seeded."

  _svc "switch_period"    '{"period_id":"period_4","label":"Meting 4 (6 mnd)","date":"2026-07-01"}'
  _svc "save_measurement" '{"gewicht":77.0,"spiermassa":28.8,"vetmassa":28.5,"bmi":27.3,"timestamp":"2026-07-01T09:00:00+00:00"}'
  success "Meting 4 (6 mnd) — 2026-07-01 — seeded."

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

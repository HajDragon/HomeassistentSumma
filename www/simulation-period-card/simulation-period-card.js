/**
 * simulation-period-card.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Custom Lovelace card for the Simulation Manager integration.
 *
 * Features
 * ────────
 *  • Renders a table of measurements for the *active period only*.
 *  • Period-tab bar for switching periods via simulation_manager.switch_period.
 *  • Reactive: updates instantly when HA pushes a new state over WebSocket —
 *    no polling, no manual refresh.
 *  • "Save Measurement" form to call simulation_manager.save_measurement
 *    directly from the dashboard.
 *  • "Reset" button guarded by a confirmation dialog.
 *
 * Architecture
 * ────────────
 *  The card extends HTMLElement and uses Shadow DOM.
 *  State is consumed via the standard `set hass(hass)` Lovelace contract:
 *  every time HA pushes a new state snapshot, the setter fires, we diff the
 *  relevant entity, and call _render() only when something changed.
 *
 *  No external CDN dependencies — pure browser APIs only.
 *
 * Installation
 * ────────────
 *  1. Copy this file to  <ha-config>/www/simulation-period-card/
 *  2. Add to Lovelace resources:
 *       url: /local/simulation-period-card/simulation-period-card.js
 *       type: module
 *  3. Use card type: custom:simulation-period-card
 * ─────────────────────────────────────────────────────────────────────────────
 */

const DOMAIN     = "simulation_manager";
const ENTITY_ID  = `sensor.${DOMAIN}`;

// ── Stylesheet (injected once into the shadow root) ───────────────────────────
const STYLES = `
  :host {
    display: block;
    font-family: var(--primary-font-family, sans-serif);
  }
  ha-card {
    padding: 0;
    overflow: hidden;
  }
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .card-header .title-icon {
    margin-right: 8px;
  }
  .card-content {
    padding: 12px 16px 16px;
  }

  /* ── Period tabs ── */
  .tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 14px;
  }
  .tab {
    padding: 5px 12px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 20px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    white-space: nowrap;
  }
  .tab:hover {
    background: var(--primary-color);
    color: var(--text-primary-color, #fff);
    border-color: var(--primary-color);
  }
  .tab.active {
    background: var(--primary-color);
    color: var(--text-primary-color, #fff);
    border-color: var(--primary-color);
    font-weight: 600;
  }
  .no-periods {
    color: var(--secondary-text-color);
    font-style: italic;
    font-size: 0.9rem;
    padding: 8px 0;
  }

  /* ── Period header ── */
  .period-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 10px;
  }
  .period-label {
    font-size: 1rem;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .period-date {
    font-size: 0.8rem;
    color: var(--secondary-text-color);
  }

  /* ── Measurements table ── */
  .table-wrapper {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--divider-color, #e0e0e0);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  thead tr {
    background: var(--table-row-background-color, var(--primary-color));
    color: var(--text-primary-color, #fff);
  }
  th {
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
  }
  tbody tr:nth-child(odd) {
    background: var(--table-row-background-color, transparent);
  }
  tbody tr:nth-child(even) {
    background: var(--table-row-alternative-background-color, rgba(0,0,0,0.04));
  }
  td {
    padding: 7px 12px;
    color: var(--primary-text-color);
    white-space: nowrap;
  }
  .empty-msg {
    color: var(--secondary-text-color);
    font-style: italic;
    padding: 10px 0;
    font-size: 0.88rem;
  }

  /* ── Add measurement form ── */
  details {
    margin-top: 14px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 8px;
    overflow: hidden;
  }
  summary {
    padding: 9px 14px;
    background: var(--secondary-background-color, #f5f5f5);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--primary-text-color);
    user-select: none;
    list-style: none;
  }
  summary::before {
    content: "＋ ";
  }
  details[open] summary::before {
    content: "－ ";
  }
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 12px 14px;
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .form-group label {
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .form-group input {
    padding: 6px 8px;
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 6px;
    font-size: 0.9rem;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    width: 100%;
    box-sizing: border-box;
  }
  .form-group input:focus {
    outline: 2px solid var(--primary-color);
    border-color: transparent;
  }
  .form-actions {
    padding: 0 14px 12px;
    display: flex;
    gap: 8px;
  }

  /* ── Buttons ── */
  .btn {
    padding: 7px 16px;
    border: none;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }
  .btn:hover { opacity: 0.85; }
  .btn:active { opacity: 0.70; }
  .btn-primary {
    background: var(--primary-color);
    color: var(--text-primary-color, #fff);
  }
  .btn-danger {
    background: var(--error-color, #db4437);
    color: #fff;
  }
  .btn-outlined {
    background: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
  }

  /* ── Footer ── */
  .card-footer {
    display: flex;
    justify-content: flex-end;
    padding: 0 16px 14px;
    gap: 8px;
  }
  .stat-badge {
    font-size: 0.75rem;
    color: var(--secondary-text-color);
    padding: 4px 10px;
    border-radius: 12px;
    background: var(--secondary-background-color, #f0f0f0);
  }
`;

// ── Card definition ───────────────────────────────────────────────────────────

class SimulationPeriodCard extends HTMLElement {
  // ── Lovelace lifecycle ──────────────────────────────────────────────────────

  /**
   * setConfig is called once by Lovelace when the card is parsed.
   * Throw here to surface config errors in the UI editor.
   */
  setConfig(config) {
    if (!config) throw new Error("simulation-period-card: config is required.");
    this._config = Object.assign(
      {
        title: "Simulatie Perioden",
        columns: ["timestamp", "gewicht", "spiermassa", "vetmassa", "bmi"],
        column_labels: {
          timestamp:  "Datum/Tijd",
          gewicht:    "Gewicht (kg)",
          spiermassa: "Spiermassa (kg)",
          vetmassa:   "Vetmassa (kg)",
          bmi:        "BMI (kg/m²)",
        },
      },
      config
    );

    // Build shadow root once.
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      const style = document.createElement("style");
      style.textContent = STYLES;
      this.shadowRoot.appendChild(style);
      this._container = document.createElement("div");
      this.shadowRoot.appendChild(this._container);
    }
  }

  /**
   * `hass` is set by Lovelace every time ANY entity changes in HA.
   * We diff only the entity we care about to avoid unnecessary re-renders.
   */
  set hass(hass) {
    this._hass = hass;
    const newState = hass.states[ENTITY_ID];
    const newJson  = JSON.stringify(newState);

    if (newJson === this._lastStateJson) return; // Nothing changed — skip render.
    this._lastStateJson = newJson;

    this._activePeriodId = newState?.attributes?.active_period_id ?? null;
    this._periods        = newState?.attributes?.periods        ?? {};
    this._periodOrder    = newState?.attributes?.period_order   ?? [];
    this._totalPeriods   = newState?.attributes?.total_periods  ?? 0;

    this._render();
  }

  // ── Service helpers ─────────────────────────────────────────────────────────

  _callService(service, data = {}) {
    this._hass.callService(DOMAIN, service, data);
  }

  _switchPeriod(periodId) {
    this._callService("switch_period", { period_id: periodId });
  }

  _saveMeasurement() {
    const root = this.shadowRoot;
    const getValue = (id) => {
      const el = root.getElementById(id);
      return el && el.value !== "" ? parseFloat(el.value) : undefined;
    };

    const data = {};
    ["gewicht", "spiermassa", "vetmassa", "bmi"].forEach((field) => {
      const v = getValue(`input_${field}`);
      if (v !== undefined && !isNaN(v)) data[field] = v;
    });

    if (Object.keys(data).length === 0) {
      alert("Voer minimaal één waarde in voordat je opslaat.");
      return;
    }

    this._callService("save_measurement", data);

    // Clear form fields after submit.
    ["gewicht", "spiermassa", "vetmassa", "bmi"].forEach((field) => {
      const el = root.getElementById(`input_${field}`);
      if (el) el.value = "";
    });

    // Collapse the details panel.
    const details = root.querySelector("details");
    if (details) details.open = false;
  }

  _resetSimulation() {
    if (!confirm("Weet je zeker dat je de volledige simulatie wilt resetten? Dit kan niet ongedaan worden gemaakt.")) {
      return;
    }
    this._callService("reset_simulation");
  }

  // ── SVG line chart ──────────────────────────────────────────────────────────
  _renderSvgChart() {
    // 4-period timeline anchored to plan.md dates
    const TIMELINE = [
      { id: 'period_1', shortLabel: "jan '26" },
      { id: 'period_2', shortLabel: "mrt '26" },
      { id: 'period_3', shortLabel: "mei '26" },
      { id: 'period_4', shortLabel: "jul '26" },
    ];
    // Baseline values from plan.md — shown at 40% opacity until a live
    // measurement overwrites them (full opacity, bold labels).
    const FALLBACK = [
      { gewicht: 70.0, spiermassa: 29.5, vetmassa: 24.0, bmi: 24.8 },
      { gewicht: 72.0, spiermassa: 29.3, vetmassa: 25.5, bmi: 25.5 },
      { gewicht: 74.5, spiermassa: 29.0, vetmassa: 27.0, bmi: 26.4 },
      { gewicht: 77.0, spiermassa: 28.8, vetmassa: 28.5, bmi: 27.3 },
    ];
    const METRICS = [
      { key: 'gewicht',    label: 'Gewicht (kg)',    color: '#1976d2' },
      { key: 'spiermassa', label: 'Spiermassa (kg)', color: '#388e3c' },
      { key: 'vetmassa',   label: 'Vetmassa (kg)',   color: '#f57c00' },
      { key: 'bmi',        label: 'BMI',             color: '#7b1fa2' },
    ];

    // Merge live sensor data with fallback values
    const points = TIMELINE.map((t, i) => {
      const p = this._periods[t.id];
      const m = p?.measurements?.length ? p.measurements[p.measurements.length - 1] : null;
      return {
        shortLabel: t.shortLabel,
        live: !!m,
        gewicht:    parseFloat(m?.gewicht    ?? FALLBACK[i].gewicht),
        spiermassa: parseFloat(m?.spiermassa ?? FALLBACK[i].spiermassa),
        vetmassa:   parseFloat(m?.vetmassa   ?? FALLBACK[i].vetmassa),
        bmi:        parseFloat(m?.bmi        ?? FALLBACK[i].bmi),
      };
    });

    const W = 560, H = 210;
    const pad = { top: 30, right: 16, bottom: 38, left: 8 };
    const cW = W - pad.left - pad.right;
    const cH = H - pad.top - pad.bottom;
    const xPos = (i) => pad.left + (i / (TIMELINE.length - 1)) * cW;

    // Per-metric Y scale with 25% margin so lines don't hug edges
    const yScale = {};
    METRICS.forEach(({ key }) => {
      const vals = points.map(p => p[key]);
      const lo = Math.min(...vals), hi = Math.max(...vals);
      const mg = (hi - lo) * 0.25 || 1;
      yScale[key] = { lo: lo - mg, hi: hi + mg };
    });
    const yPos = (val, key) => {
      const { lo, hi } = yScale[key];
      return pad.top + cH - ((val - lo) / (hi - lo)) * cH;
    };

    let s = '';

    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = (pad.top + (i / 4) * cH).toFixed(1);
      s += `<line x1="${pad.left}" y1="${y}" x2="${(pad.left + cW).toFixed(1)}" y2="${y}" stroke="#e0e0e0" stroke-width="0.8"/>`;
    }

    // Vertical guides + date labels
    TIMELINE.forEach((t, i) => {
      const x = xPos(i).toFixed(1);
      if (i > 0) s += `<line x1="${x}" y1="${pad.top}" x2="${x}" y2="${(pad.top + cH).toFixed(1)}" stroke="#e0e0e0" stroke-width="0.8" stroke-dasharray="3,3"/>`;
      s += `<text x="${x}" y="${(pad.top + cH + 14).toFixed(1)}" text-anchor="middle" font-size="10" fill="#757575">${_esc(t.shortLabel)}</text>`;
      s += `<text x="${x}" y="${(pad.top + cH + 26).toFixed(1)}" text-anchor="middle" font-size="9" fill="#aaa">M${i + 1}</text>`;
    });

    // X-axis baseline
    s += `<line x1="${pad.left}" y1="${(pad.top + cH).toFixed(1)}" x2="${(pad.left + cW).toFixed(1)}" y2="${(pad.top + cH).toFixed(1)}" stroke="#bdbdbd" stroke-width="1.5"/>`;

    // Legend row
    const lSpacing = Math.floor(cW / 4);
    METRICS.forEach(({ label, color }, mi) => {
      const lx = pad.left + mi * lSpacing;
      s += `<rect x="${lx}" y="6" width="10" height="10" fill="${color}" rx="2"/>`;
      s += `<text x="${lx + 13}" y="15" font-size="9.5" fill="#424242">${_esc(label)}</text>`;
    });

    // Lines + dots for each metric
    METRICS.forEach(({ key, color }) => {
      const coords = points.map((p, i) => `${xPos(i).toFixed(1)},${yPos(p[key], key).toFixed(1)}`).join(' ');
      s += `<polyline points="${coords}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
      points.forEach((p, i) => {
        const cx = xPos(i).toFixed(1);
        const cy = yPos(p[key], key);
        const op = p.live ? '1' : '0.4';
        s += `<circle cx="${cx}" cy="${cy.toFixed(1)}" r="${p.live ? 5 : 4}" fill="${color}" stroke="white" stroke-width="2" opacity="${op}"/>`;
        const labelY = cy > pad.top + 18 ? cy - 8 : cy + 17;
        s += `<text x="${cx}" y="${labelY.toFixed(1)}" text-anchor="middle" font-size="9" fill="${color}" font-weight="${p.live ? 700 : 400}" opacity="${op}">${p[key].toFixed(1)}</text>`;
      });
    });

    return `
    <div style="overflow-x:auto;margin:0 0 12px;border:1px solid var(--divider-color,#e0e0e0);border-radius:8px;padding:6px 6px 0;background:var(--card-background-color);">
      <svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;font-family:var(--primary-font-family,sans-serif);">
        ${s}
      </svg>
      <div style="font-size:0.72rem;color:var(--secondary-text-color);text-align:right;padding:2px 6px 4px;">
        Lichte punten = standaard simulatiewaarden (plan.md) &nbsp;·&nbsp; Volle punten = live opgeslagen meting
      </div>
    </div>`;
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  _render() {
    if (!this._config || !this._hass) return;

    const cfg          = this._config;
    const activePeriod = this._activePeriodId
      ? this._periods[this._activePeriodId]
      : null;

    // ── Tabs ──────────────────────────────────────────────────────────────────
    const tabsHtml = this._periodOrder.length === 0
      ? `<p class="no-periods">Geen perioden aangemaakt. Roep <code>switch_period</code> aan om te beginnen.</p>`
      : this._periodOrder.map((pid) => {
          const p     = this._periods[pid] ?? {};
          const label = p.label ?? pid;
          const cls   = pid === this._activePeriodId ? "tab active" : "tab";
          return `<button class="${cls}" data-period-id="${_esc(pid)}">${_esc(label)}</button>`;
        }).join("");

    // ── All-periods overview table (one summary row per period) ─────────────
    const columns      = cfg.columns;
    const columnLabels = cfg.column_labels;
    const periodHeaderHtml = "";

    // Skip raw timestamp column — period date is shown in its own column.
    const overviewCols = columns.filter(c => c !== "timestamp");

    const theadHtml = `<thead><tr>
      <th>Periode</th><th>Datum</th>${overviewCols.map(col => `<th>${_esc(columnLabels[col] ?? col)}</th>`).join("")}
    </tr></thead>`;

    const tbodyHtml = this._periodOrder.length === 0
      ? `<tbody><tr><td colspan="${overviewCols.length + 2}" style="padding:10px 12px;color:var(--secondary-text-color);font-style:italic;">
           Geen perioden. Klik op een Meting-knop om te starten.
         </td></tr></tbody>`
      : `<tbody>${this._periodOrder.map(pid => {
          const p    = this._periods[pid] ?? {};
          const last = p.measurements?.length ? p.measurements[p.measurements.length - 1] : null;
          const act  = pid === this._activePeriodId;
          const sty  = act ? ' style="font-weight:700;background:rgba(var(--rgb-primary-color,25,118,210),0.1)"' : '';
          return `<tr${sty}>
            <td>${_esc(p.label ?? pid)}${act ? " ◀" : ""}</td>
            <td>${_esc(p.date ?? "—")}</td>
            ${overviewCols.map(col => `<td>${last ? _esc(String(last[col] ?? "—")) : "—"}</td>`).join("")}
          </tr>`;
        }).join("")}</tbody>`;

    const tableHtml = `
      <div class="table-wrapper">
        <table>${theadHtml}${tbodyHtml}</table>
      </div>`;

    // ── Add measurement form ───────────────────────────────────────────────────
    const formHtml = `
      <details>
        <summary>Meting toevoegen aan actieve periode</summary>
        <div class="form-grid">
          ${[
            ["input_gewicht",    "Gewicht (kg)",    "70.0"],
            ["input_spiermassa", "Spiermassa (kg)", "29.5"],
            ["input_vetmassa",   "Vetmassa (kg)",   "24.0"],
            ["input_bmi",        "BMI (kg/m²)",     "24.8"],
          ].map(([id, label, ph]) => `
            <div class="form-group">
              <label for="${id}">${label}</label>
              <input type="number" id="${id}" step="0.1" min="0" placeholder="${ph}" />
            </div>`).join("")}
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" id="btn-save">Opslaan</button>
        </div>
      </details>`;

    // ── Footer ────────────────────────────────────────────────────────────────
    const totalMeasurements = this._periodOrder.reduce(
      (sum, pid) => sum + (this._periods[pid]?.measurements?.length ?? 0), 0
    );
    const footerHtml = `
      <div class="card-footer">
        <span class="stat-badge">${this._totalPeriods} periode(n)</span>
        <span class="stat-badge">${totalMeasurements} meting(en)</span>
        <button class="btn btn-danger" id="btn-reset">Reset simulatie</button>
      </div>`;

    // ── Compose & inject ──────────────────────────────────────────────────────
    const chartHtml = this._renderSvgChart();
    this._container.innerHTML = `
      <ha-card>
        <div class="card-header">
          <span>
            <ha-icon class="title-icon" icon="mdi:chart-timeline-variant"></ha-icon>
            ${_esc(cfg.title)}
          </span>
        </div>
        <div class="card-content">
          <div class="tabs" id="tabs-container">${tabsHtml}</div>
          ${chartHtml}
          ${tableHtml}
          ${activePeriod ? formHtml : ""}
        </div>
        ${footerHtml}
      </ha-card>`;

    // ── Bind events  (after innerHTML — refs are fresh each render) ───────────
    this._container.querySelectorAll(".tab[data-period-id]").forEach((btn) => {
      btn.addEventListener("click", () => this._switchPeriod(btn.dataset.periodId));
    });

    const saveBtn  = this._container.querySelector("#btn-save");
    const resetBtn = this._container.querySelector("#btn-reset");
    if (saveBtn)  saveBtn.addEventListener("click",  () => this._saveMeasurement());
    if (resetBtn) resetBtn.addEventListener("click", () => this._resetSimulation());
  }

  // ── Required Lovelace static ────────────────────────────────────────────────

  static getConfigElement() {
    // No visual editor — plain YAML config only.
    return null;
  }

  static getStubConfig() {
    return {
      title: "Simulatie Perioden",
      columns: ["timestamp", "gewicht", "spiermassa", "vetmassa", "bmi"],
    };
  }
}

// ── Utility: safe HTML escaping ───────────────────────────────────────────────

function _esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Register ─────────────────────────────────────────────────────────────────

customElements.define("simulation-period-card", SimulationPeriodCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type:        "simulation-period-card",
  name:        "Simulation Period Card",
  description: "Displays body-scan measurements per simulation period with reactive period switching.",
  preview:     false,
});

console.info(
  "%c SIMULATION-PERIOD-CARD %c v1.1.0 ",
  "color:#fff;background:#1976d2;font-weight:700;padding:2px 4px;border-radius:3px 0 0 3px",
  "color:#1976d2;background:#e3f2fd;font-weight:700;padding:2px 4px;border-radius:0 3px 3px 0"
);

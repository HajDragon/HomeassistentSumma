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

// ── External stylesheet path (served from HA's `/local/` → `www/`) ─────────
const CSS_PATH = "/local/simulation-period-card/simulation-period-card.css";

// Minimal fallback styles used only if the external CSS fails to load.
const FALLBACK_STYLES = `:host{display:block;font-family:var(--primary-font-family,sans-serif)}.card-content{padding:12px 16px 16px}`;

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
        // Optional map of metric-key → HA entity_id for live slider preview.
        // When set, the card shows a pulsing amber row with unsaved slider
        // values while the 1-second debounce automation is pending.
        // Example:  live_input_entities:
        //              gewicht:    input_number.goedheid_gewicht
        //              spiermassa: input_number.goedheid_spiermassa
        //              vetmassa:   input_number.goedheid_vetmassa
        //              bmi:        input_number.goedheid_bmi
        live_input_entities: null,
      },
      config
    );

    // Preserve chart filter across re-renders; null = show all metrics.
    if (this._chartFilter === undefined) this._chartFilter = null;

    // Build shadow root once and load external stylesheet from `/local/`.
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });

      // Attempt to fetch the external CSS served from HA's `www/` folder
      // (available at /local/). If that fails, fall back to a tiny embedded
      // stylesheet so the card remains usable.
      try {
        fetch(CSS_PATH)
          .then((r) => {
            if (!r.ok) throw new Error("CSS fetch failed");
            return r.text();
          })
          .then((css) => {
            const style = document.createElement("style");
            style.textContent = css;
            this.shadowRoot.appendChild(style);
          })
          .catch(() => {
            const style = document.createElement("style");
            style.textContent = FALLBACK_STYLES;
            this.shadowRoot.appendChild(style);
          });
      } catch (e) {
        const style = document.createElement("style");
        style.textContent = FALLBACK_STYLES;
        this.shadowRoot.appendChild(style);
      }

      this._container = document.createElement("div");
      this.shadowRoot.appendChild(this._container);

      // Tooltip overlay — position:fixed so it escapes any overflow:hidden ancestor.
      this._tooltip = document.createElement("div");
      this._tooltip.style.cssText = [
        "position:fixed",
        "pointer-events:none",
        "background:rgba(30,30,30,0.88)",
        "color:#fff",
        "padding:6px 10px",
        "border-radius:6px",
        "font-size:0.78rem",
        "line-height:1.6",
        "white-space:nowrap",
        "z-index:9999",
        "display:none",
        "box-shadow:0 2px 8px rgba(0,0,0,0.3)",
      ].join(";");
      this.shadowRoot.appendChild(this._tooltip);
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

    // ── Live entity tracking ──────────────────────────────────────────────
    // When live_input_entities is configured, snapshot the current slider
    // states on every hass update.  A change in live values forces a re-render
    // even if sensor.simulation_manager hasn't changed yet (i.e. while the 1s
    // debounce automation is counting down).
    let liveChanged = false;
    const liveCfg = this._config?.live_input_entities;
    if (liveCfg && typeof liveCfg === "object") {
      const snapshot = {};
      Object.entries(liveCfg).forEach(([key, entityId]) => {
        snapshot[key] = parseFloat(hass.states[entityId]?.state ?? 0) || 0;
      });
      const liveJson = JSON.stringify(snapshot);
      if (liveJson !== this._lastLiveJson) {
        this._lastLiveJson = liveJson;
        this._liveValues   = snapshot;  // stored for _render()
        liveChanged = true;
      }
    } else {
      this._liveValues = null;
    }

    if (newJson === this._lastStateJson && !liveChanged) return; // nothing to do
    this._lastStateJson = newJson;

    this._activePeriodId = newState?.attributes?.active_period_id ?? null;
    this._periods        = newState?.attributes?.periods        ?? {};
    // Sort numerically by the trailing integer in the period ID so that
    // Period 10 always appears after Period 9, not before Period 2.
    this._periodOrder = [...(newState?.attributes?.period_order ?? [])].sort(
      (a, b) => _extractPeriodNum(a) - _extractPeriodNum(b)
    );
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
    // Fixed metric definitions — the only non-dynamic part, and intentionally so:
    // these are the four body-scan fields defined in the service schema.
    const METRICS = [
      { key: 'gewicht',    label: 'Gewicht',    unit: 'kg',           color: '#1976d2' },
      { key: 'spiermassa', label: 'Spiermassa', unit: 'kg',           color: '#388e3c' },
      { key: 'vetmassa',   label: 'Vetmassa',   unit: 'kg',           color: '#f57c00' },
      { key: 'bmi',        label: 'BMI',        unit: 'kg/m\u00b2',   color: '#7b1fa2' },
    ];

    // Build period data dynamically from the already-sorted _periodOrder.
    // Zero is treated as "no data": all four body-scan metrics are physically
    // impossible at zero, so 0 means the field was not recorded that period.
    const points = this._periodOrder.map((pid) => {
      const p    = this._periods[pid] ?? {};
      const last = p.measurements?.length
        ? p.measurements[p.measurements.length - 1]
        : null;
      const row = { label: p.label ?? pid, date: p.date ?? '' };
      METRICS.forEach(({ key }) => {
        const raw = last ? parseFloat(last[key] ?? 0) : null;
        row[key] = raw !== null && raw > 0 ? raw : null;
      });
      return row;
    });

    // All metrics with at least one data point — drives filter buttons + empty-state check.
    const allActiveMetrics = METRICS.filter(({ key }) =>
      points.some((p) => p[key] !== null)
    );

    if (allActiveMetrics.length === 0) {
      return `<div style="margin:0 0 12px;padding:20px 14px;border:1px solid var(--divider-color,#e0e0e0);border-radius:8px;background:var(--secondary-background-color,#f5f5f5);color:var(--secondary-text-color);font-size:0.85rem;text-align:center;">
        Nog geen metingen opgeslagen &#8212; de grafiek verschijnt zodra je de eerste meting toevoegt.
      </div>`;
    }

    // Narrow to the selected metric; fall back to all when the filter no longer matches any data.
    const filtered = this._chartFilter
      ? allActiveMetrics.filter(({ key }) => key === this._chartFilter)
      : allActiveMetrics;
    const activeMetrics = filtered.length > 0 ? filtered : allActiveMetrics;

    const n   = points.length;
    const W   = 680, H = 300;
    const pad = { top: 44, right: 20, bottom: 54, left: 12 };
    const cW  = W - pad.left - pad.right;
    const cH  = H - pad.top  - pad.bottom;
    // When only one period exists, centre it horizontally.
    const xPos = (i) =>
      pad.left + (n > 1 ? (i / (n - 1)) * cW : cW / 2);

    // Per-metric Y scale derived from live data only, with 25 % headroom.
    const yScale = {};
    activeMetrics.forEach(({ key }) => {
      const vals = points.map((p) => p[key]).filter((v) => v !== null);
      const lo = Math.min(...vals), hi = Math.max(...vals);
      const mg = (hi - lo) * 0.35 || 2;
      yScale[key] = { lo: lo - mg, hi: hi + mg };
    });
    const yPos = (val, key) => {
      const { lo, hi } = yScale[key];
      return pad.top + cH - ((val - lo) / (hi - lo)) * cH;
    };

    let s = '';

    // Horizontal grid lines.
    for (let i = 0; i <= 4; i++) {
      const y = (pad.top + (i / 4) * cH).toFixed(1);
      s += `<line x1="${pad.left}" y1="${y}" x2="${(pad.left + cW).toFixed(1)}" y2="${y}" stroke="#e0e0e0" stroke-width="0.8"/>`;
    }

    // Vertical guides + x-axis labels (YYYY-MM from period date, or "M{n}").
    points.forEach((pt, i) => {
      const x    = xPos(i).toFixed(1);
      const xLbl = pt.date ? pt.date.slice(0, 7) : `M${i + 1}`;
      if (i > 0)
        s += `<line x1="${x}" y1="${pad.top}" x2="${x}" y2="${(pad.top + cH).toFixed(1)}" stroke="#e0e0e0" stroke-width="0.8" stroke-dasharray="3,3"/>`;
      s += `<text x="${x}" y="${(pad.top + cH + 14).toFixed(1)}" text-anchor="middle" font-size="10" fill="#757575">${_esc(xLbl)}</text>`;
      s += `<text x="${x}" y="${(pad.top + cH + 26).toFixed(1)}" text-anchor="middle" font-size="9" fill="#aaa">M${i + 1}</text>`;
    });

    // X-axis baseline.
    s += `<line x1="${pad.left}" y1="${(pad.top + cH).toFixed(1)}" x2="${(pad.left + cW).toFixed(1)}" y2="${(pad.top + cH).toFixed(1)}" stroke="#bdbdbd" stroke-width="1.5"/>`;

    // Legend row — only for metrics that have data.
    const lSpacing = Math.floor(cW / activeMetrics.length);
    activeMetrics.forEach(({ label, unit, color }, mi) => {
      const lx = pad.left + mi * lSpacing;
      s += `<rect x="${lx}" y="8" width="10" height="10" fill="${color}" rx="2"/>`;
      s += `<text x="${lx + 13}" y="17" font-size="9.5" fill="#ffffff">${_esc(`${label} (${unit})`)}</text>`;
    });

    // Lines + dots — skips periods with no data for that metric.
    activeMetrics.forEach(({ key, label, unit, color }) => {
      const live = points
        .map((p, i) => (p[key] !== null ? { val: p[key], i } : null))
        .filter(Boolean);

      // Polyline connecting all live points (drawn only when ≥ 2 exist).
      if (live.length > 1) {
        const pts = live
          .map(({ val, i }) => `${xPos(i).toFixed(1)},${yPos(val, key).toFixed(1)}`)
          .join(' ');
        s += `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>`;
      }

      // Dots + value labels for each live point.
      live.forEach(({ val, i }) => {
        const cx     = xPos(i).toFixed(1);
        const cy     = yPos(val, key);
        const period = points[i].label;
        s += `<circle cx="${cx}" cy="${cy.toFixed(1)}" r="6" fill="${color}" stroke="white" stroke-width="2" class="chart-dot" data-metric="${_esc(label)}" data-val="${val.toFixed(2)}" data-unit="${_esc(unit)}" data-period="${_esc(period)}"/>`;
        const labelY = cy > pad.top + 20 ? cy - 10 : cy + 20;
        s += `<text x="${cx}" y="${labelY.toFixed(1)}" text-anchor="middle" font-size="10" fill="${color}" font-weight="700">${val.toFixed(1)}</text>`;
      });
    });

    // ── Invisible hit strips — one per period column, drawn last (topmost) ────
    // Because SVG has no true z-index, the last element in DOM order receives
    // mouse events first.  By drawing these transparent <rect>s after all
    // dots and lines, they sit on top and catch every hover regardless of
    // which metric dot is visually on top.
    // Each strip encodes ALL metrics at that period as JSON so the tooltip
    // handler can aggregate them into one panel — solving the overlap problem.
    const colSpacing = n > 1 ? cW / (n - 1) : cW;
    const stripHalfW = Math.max(18, colSpacing / 2);
    points.forEach((pt, i) => {
      const metricsAtPoint = activeMetrics
        .filter(({ key }) => pt[key] !== null)
        .map(({ key, label, unit, color }) => ({
          label, unit, color, val: pt[key].toFixed(2),
        }));
      if (metricsAtPoint.length === 0) return;
      const x = xPos(i);
      s += `<rect class="chart-strip"
        x="${(x - stripHalfW).toFixed(1)}" y="${pad.top}"
        width="${(stripHalfW * 2).toFixed(1)}" height="${cH}"
        fill="transparent"
        data-period="${_esc(pt.label)}"
        data-date="${_esc(pt.date)}"
        data-metrics="${_esc(JSON.stringify(metricsAtPoint))}"
        style="cursor:crosshair"/>`;
    });

    // ── Per-metric filter buttons ─────────────────────────────────────────────
    // Only shown when 2+ metrics have data.  Each metric button is coloured
    // with that metric's chart colour so the button visually matches its line.
    // The "Alle" button uses the HA primary colour (via .active CSS class).
    const filterHtml = allActiveMetrics.length >= 1 ? `
      <div class="chart-filters">
        <button class="chart-filter-btn${!this._chartFilter ? ' active' : ''}" data-filter="">Alle</button>
        ${allActiveMetrics.map(({ key, label, color }) => {
          const isActive = this._chartFilter === key;
          return `<button class="chart-filter-btn" data-filter="${_esc(key)}" style="${
            isActive
              ? `background:${color};color:#fff;border-color:${color}`
              : `border-color:${color};color:${color}`
          }">${_esc(label)}</button>`;
        }).join('')}
      </div>` : '';

    return `
      ${filterHtml}
      <div style="overflow-x:auto;margin:0 0 12px;border:1px solid var(--divider-color,#e0e0e0);border-radius:8px;padding:8px 8px 0;background:var(--card-background-color);">
        <svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;font-family:var(--primary-font-family,sans-serif);min-width:360px;min-height:220px;">
          ${s}
        </svg>
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

          // ── Live preview for the active period ──────────────────────────
          // While the 1 s debounce automation is pending, _liveValues holds
          // the current slider states.  When any live value differs from the
          // last saved measurement by more than the step size (0.05), we show
          // a pulsing amber row so the teacher sees their edit immediately —
          // before the automation actually writes to simulation_manager.
          let liveRowHtml = "";
          if (act && this._liveValues) {
            const lv = this._liveValues;
            const hasDiff = overviewCols.some((col) => {
              if (!(col in lv)) return false;
              const lastVal = last ? parseFloat(last[col] ?? 0) : 0;
              return Math.abs((lv[col] ?? 0) - lastVal) > 0.05;
            });
            if (hasDiff) {
              liveRowHtml = `<tr class="live-preview">
                <td>${_esc(p.label ?? pid)} <span class="live-badge">◎ actueel</span></td>
                <td>${_esc(p.date ?? "—")}</td>
                ${overviewCols.map(col => {
                  const v = col in lv ? lv[col].toFixed(1) : (last ? _esc(String(last[col] ?? "—")) : "—");
                  return `<td>${v}</td>`;
                }).join("")}
              </tr>`;
            }
          }

          return liveRowHtml + `<tr${sty}>
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

    // Chart metric filter buttons
    this._container.querySelectorAll(".chart-filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._chartFilter = btn.dataset.filter || null;
        this._render();
      });
    });

    const saveBtn  = this._container.querySelector("#btn-save");
    const resetBtn = this._container.querySelector("#btn-reset");
    if (saveBtn)  saveBtn.addEventListener("click",  () => this._saveMeasurement());
    if (resetBtn) resetBtn.addEventListener("click", () => this._resetSimulation());

    // ── Tooltip bindings (SVG hit strips — one per period column) ─────────────
    // Each strip covers the full chart height for its period and carries all
    // metrics as JSON in data-metrics.  This means hovering anywhere in the
    // column — even where multiple dots overlap at the same pixel — always
    // shows every variable's value in one aggregated tooltip.
    if (this._tooltip) {
      const tip = this._tooltip;
      this._container.querySelectorAll(".chart-strip").forEach((strip) => {
        strip.addEventListener("mouseenter", () => {
          let metrics;
          try { metrics = JSON.parse(strip.dataset.metrics || "[]"); }
          catch { metrics = []; }
          tip.innerHTML = "";
          // Period / date header row
          const header = document.createElement("div");
          header.style.cssText = "font-weight:700;margin-bottom:4px;padding-bottom:3px;border-bottom:1px solid rgba(255,255,255,0.3)";
          header.textContent = strip.dataset.period +
            (strip.dataset.date ? "\u00a0\u00b7\u00a0" + strip.dataset.date.slice(0, 7) : "");
          tip.appendChild(header);
          // One row per metric with a colour swatch
          metrics.forEach((m) => {
            const row = document.createElement("div");
            row.style.cssText = "display:flex;align-items:center;gap:6px;margin-top:2px";
            const swatch = document.createElement("span");
            swatch.style.cssText =
              `display:inline-block;width:8px;height:8px;border-radius:50%;background:${m.color};flex-shrink:0`;
            const text = document.createElement("span");
            text.textContent = `${m.label}: ${m.val}\u00a0${m.unit}`;
            row.appendChild(swatch);
            row.appendChild(text);
            tip.appendChild(row);
          });
          tip.style.display = "block";
        });
        strip.addEventListener("mousemove", (e) => {
          tip.style.left = (e.clientX + 14) + "px";
          tip.style.top  = (e.clientY - 44) + "px";
        });
        strip.addEventListener("mouseleave", () => {
          tip.style.display = "none";
        });
      });
    }
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

/**
 * _extractPeriodNum(pid) → integer
 *
 * Parses the trailing integer from a period ID string so that sorting is
 * numeric rather than lexicographic.  Lexicographic order would place
 * "period_10" before "period_2"; numeric order is always correct.
 *
 * Examples:
 *   "period_1"   → 1
 *   "period_10"  → 10
 *   "period_100" → 100
 *   "custom_abc" → 0  (fallback — non-numeric IDs sort to the front)
 *
 * Complexity: O(1) per call → overall sort is O(n log n) for n periods,
 * which scales to 100+ periods without any hardcoding.
 */
function _extractPeriodNum(pid) {
  const match = String(pid).match(/(\d+)$/);
  return match ? parseInt(match[1], 10) : 0;
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
  "%c SIMULATION-PERIOD-CARD %c v1.7.0 ",
  "color:#fff;background:#1976d2;font-weight:700;padding:2px 4px;border-radius:3px 0 0 3px",
  "color:#1976d2;background:#e3f2fd;font-weight:700;padding:2px 4px;border-radius:0 3px 3px 0"
);

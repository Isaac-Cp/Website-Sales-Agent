def render_dashboard_shell():
    return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Website Sales Agent Dashboard</title>
    <style>
      :root {
        --bg: #f5efe5;
        --ink: #17212e;
        --muted: #64748b;
        --panel: rgba(255, 252, 246, 0.88);
        --line: rgba(23, 33, 46, 0.08);
        --teal: #0f766e;
        --teal-deep: #134e4a;
        --gold: #d97706;
        --danger: #b91c1c;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(217, 119, 6, 0.18), transparent 24%),
          radial-gradient(circle at top right, rgba(15, 118, 110, 0.18), transparent 22%),
          linear-gradient(180deg, #fff9f0 0%, var(--bg) 55%, #eadfce 100%);
      }

      .shell { width: min(1400px, calc(100% - 24px)); margin: 0 auto; padding: 22px 0 40px; }
      .hero, .panel { border: 1px solid var(--line); border-radius: 28px; box-shadow: 0 18px 40px rgba(15, 23, 42, 0.10); }
      .hero { padding: 28px; color: #f8fafc; background: linear-gradient(135deg, rgba(19, 78, 74, 0.98), rgba(23, 33, 46, 0.96)); }
      .eyebrow {
        display: inline-flex;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.12);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 12px;
      }

      h1 { margin: 14px 0 10px; font-size: clamp(34px, 5vw, 58px); line-height: 1.02; letter-spacing: -0.04em; }
      .hero p { max-width: 780px; margin: 0; color: rgba(248, 250, 252, 0.82); line-height: 1.7; }
      .hero-meta, .hero-actions, .tag-row, .config-grid { display: flex; flex-wrap: wrap; gap: 10px; }
      .hero-meta { margin-top: 18px; }
      .hero-row { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
      .badge, .tag, .button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 14px; border-radius: 999px; font-size: 13px; font-weight: 700; }
      .badge, .tag { background: rgba(255, 255, 255, 0.12); color: #f8fafc; }
      .button { border: 0; cursor: pointer; text-decoration: none; font: inherit; }
      .button.primary { background: linear-gradient(180deg, #fbbf24, #f59e0b); color: #0c1f1c; }
      .button.secondary { background: rgba(255, 255, 255, 0.10); color: #f8fafc; }

      .grid { display: grid; grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr); gap: 18px; margin-top: 18px; }
      .stack { display: grid; gap: 18px; }
      .panel { background: var(--panel); padding: 22px; backdrop-filter: blur(8px); }
      .panel h2 { margin: 0; font-size: 18px; }
      .kicker { margin: 0 0 6px; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
      .panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 14px; }
      .muted { color: var(--muted); }

      .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
      .metric { padding: 18px; border-radius: 22px; background: rgba(255, 255, 255, 0.65); border: 1px solid rgba(23, 33, 46, 0.06); }
      .metric-label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
      .metric-value { margin-top: 10px; font-size: clamp(26px, 3vw, 38px); font-weight: 800; letter-spacing: -0.05em; }
      .metric-note { margin-top: 10px; color: var(--muted); font-size: 14px; line-height: 1.5; }
      .teal { color: var(--teal-deep); }
      .gold { color: var(--gold); }
      .danger { color: var(--danger); }

      .split, .triple { display: grid; gap: 16px; }
      .split { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .triple { grid-template-columns: repeat(3, minmax(0, 1fr)); }

      .list { display: grid; gap: 10px; }
      .bar-row, .timeline-item, .example { padding: 12px 0; border-bottom: 1px solid rgba(23, 33, 46, 0.06); }
      .bar-row:last-child, .timeline-item:last-child, .example:last-child { border-bottom: 0; }
      .bar-wrap { height: 9px; border-radius: 999px; background: rgba(23, 33, 46, 0.08); overflow: hidden; margin-top: 8px; }
      .bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--teal), #14b8a6); }

      table { width: 100%; border-collapse: collapse; }
      th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid rgba(23, 33, 46, 0.06); vertical-align: top; }
      th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
      .table-wrap { overflow: auto; }
      .row-link { cursor: pointer; transition: background 0.15s ease; }
      .row-link:hover, .row-link.active { background: rgba(15, 118, 110, 0.08); }

      .pill { display: inline-flex; align-items: center; justify-content: center; padding: 7px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
      .pill.good { background: rgba(15, 118, 110, 0.12); color: var(--teal-deep); }
      .pill.warn { background: rgba(217, 119, 6, 0.14); color: #9a5b00; }
      .pill.bad { background: rgba(185, 28, 28, 0.12); color: var(--danger); }
      .pill.soft { background: rgba(23, 33, 46, 0.08); color: var(--ink); }

      .config-item { min-width: 160px; padding: 14px 16px; border-radius: 20px; background: rgba(255, 255, 255, 0.62); border: 1px solid rgba(23, 33, 46, 0.06); }
      .config-item .label { margin-bottom: 8px; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
      .warning-list { display: grid; gap: 12px; }
      .warning-item { padding: 14px 16px; border-radius: 20px; background: rgba(255, 255, 255, 0.62); border: 1px solid rgba(23, 33, 46, 0.06); }
      .warning-item.warn { background: rgba(217, 119, 6, 0.10); border-color: rgba(217, 119, 6, 0.18); }
      .warning-item.error { background: rgba(185, 28, 28, 0.08); border-color: rgba(185, 28, 28, 0.14); }
      .warning-item.info { background: rgba(15, 118, 110, 0.08); border-color: rgba(15, 118, 110, 0.14); }
      .output-log {
        margin-top: 12px;
        padding: 14px;
        border-radius: 18px;
        background: rgba(23, 33, 46, 0.92);
        color: #dbe7f3;
        font-family: "Consolas", "IBM Plex Mono", monospace;
        font-size: 12px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .readiness-shell { display: grid; gap: 16px; grid-template-columns: minmax(280px, 0.95fr) minmax(0, 1.05fr); }
      .focus-card {
        padding: 22px;
        border-radius: 24px;
        color: #f8fafc;
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.96), rgba(19, 78, 74, 0.96));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
      }
      .focus-card.warn { background: linear-gradient(135deg, rgba(180, 83, 9, 0.96), rgba(146, 64, 14, 0.96)); }
      .focus-card.bad { background: linear-gradient(135deg, rgba(153, 27, 27, 0.96), rgba(127, 29, 29, 0.96)); }
      .focus-card h3 { margin: 0 0 8px; font-size: 28px; letter-spacing: -0.04em; }
      .focus-card p { margin: 0; color: rgba(248, 250, 252, 0.82); line-height: 1.65; }
      .check-list, .action-list, .funnel-steps { display: grid; gap: 12px; }
      .check-item, .action-item {
        padding: 14px 16px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(23, 33, 46, 0.06);
      }
      .check-item { display: grid; grid-template-columns: 12px minmax(0, 1fr); gap: 12px; align-items: start; }
      .check-dot { width: 12px; height: 12px; border-radius: 999px; margin-top: 4px; background: rgba(100, 116, 139, 0.45); }
      .check-item.good .check-dot { background: var(--teal); }
      .check-item.warn .check-dot { background: var(--gold); }
      .check-item.bad .check-dot { background: var(--danger); }
      .action-item.info { background: rgba(15, 118, 110, 0.08); border-color: rgba(15, 118, 110, 0.14); }
      .action-item.warn { background: rgba(217, 119, 6, 0.10); border-color: rgba(217, 119, 6, 0.18); }
      .action-item.error { background: rgba(185, 28, 28, 0.08); border-color: rgba(185, 28, 28, 0.14); }
      .funnel-steps { margin-top: 16px; }
      .funnel-step { display: grid; grid-template-columns: minmax(84px, 108px) minmax(0, 1fr) auto; gap: 12px; align-items: center; }
      .funnel-bar { height: 12px; border-radius: 999px; background: rgba(23, 33, 46, 0.08); overflow: hidden; }
      .funnel-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--teal), #2dd4bf); }
      .command-line {
        margin-top: 12px;
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(23, 33, 46, 0.08);
        color: var(--ink);
        font-family: "Consolas", "IBM Plex Mono", monospace;
        font-size: 12px;
        line-height: 1.5;
        word-break: break-word;
      }
      .empty, .loading, .error { padding: 18px; border-radius: 20px; }
      .empty, .loading { background: rgba(255, 255, 255, 0.55); color: var(--muted); }
      .error { background: rgba(185, 28, 28, 0.08); color: var(--danger); }

      @media (max-width: 1180px) {
        .grid { grid-template-columns: 1fr; }
        .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .readiness-shell { grid-template-columns: 1fr; }
      }

      @media (max-width: 760px) {
        .shell { width: min(100%, calc(100% - 14px)); padding-top: 12px; }
        .metrics, .split, .triple { grid-template-columns: 1fr; }
        .hero { padding: 22px; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div class="hero-row">
          <div>
            <div class="eyebrow">Bot Control Surface</div>
            <h1>Website Sales Agent Dashboard</h1>
            <p>Monitor what the bot has stored, where leads are in the pipeline, which outreach angles are working, and what needs attention next.</p>
            <div class="hero-meta" id="heroMeta"><span class="badge">Loading dashboard...</span></div>
          </div>
          <div class="hero-actions">
            <button class="button primary" id="refreshButton" type="button">Refresh Data</button>
            <button class="button secondary" id="runBotButton" type="button">Run Bot Now</button>
            <a class="button secondary" href="/health">Health JSON</a>
            <a class="button secondary" href="/status">Status JSON</a>
          </div>
        </div>
      </section>

      <div class="grid">
        <section class="stack">
          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Overview</p>
                <h2>Bot Snapshot</h2>
              </div>
              <div class="muted" id="lastRefresh">Waiting for first refresh</div>
            </div>
            <div class="metrics" id="overviewGrid"><div class="loading">Loading overview metrics...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Command Center</p>
                <h2>What The Bot Needs Next</h2>
              </div>
            </div>
            <div id="actionCenter"><div class="loading">Loading readiness and next actions...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Delivery Funnel</p>
                <h2>Outreach Health</h2>
              </div>
              <div class="tag-row" id="healthRates"></div>
            </div>
            <div class="triple" id="healthGrid"><div class="loading">Loading outreach health...</div></div>
            <div id="healthFunnel"><div class="loading">Loading outreach funnel...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Pipeline</p>
                <h2>Status and Sequence Flow</h2>
              </div>
            </div>
            <div class="split">
              <div>
                <p class="muted">Status distribution</p>
                <div class="list" id="statusDistribution"></div>
              </div>
              <div>
                <p class="muted">Sequence stages</p>
                <div class="list" id="stageDistribution"></div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Live Activity</p>
                <h2>Recent Bot Events</h2>
              </div>
              <div class="muted">Auto-refresh every 30 seconds</div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr><th>When</th><th>Lead</th><th>Event</th><th>Summary</th></tr>
                </thead>
                <tbody id="eventsTable"><tr><td colspan="4" class="loading">Loading events...</td></tr></tbody>
              </table>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Queues</p>
                <h2>Due Follow-ups</h2>
              </div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr><th>Lead</th><th>Status</th><th>Contact</th><th>Due</th><th>Score</th></tr>
                </thead>
                <tbody id="followupsTable"><tr><td colspan="5" class="loading">Loading follow-up queue...</td></tr></tbody>
              </table>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Lead Monitor</p>
                <h2>Recent and Priority Leads</h2>
              </div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr><th>Lead</th><th>Status</th><th>Location</th><th>Contact</th><th>Updated</th></tr>
                </thead>
                <tbody id="leadsTable"><tr><td colspan="5" class="loading">Loading leads...</td></tr></tbody>
              </table>
            </div>
          </section>
        </section>

        <aside class="stack">
          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Automation</p>
                <h2>Bot Runtime</h2>
              </div>
            </div>
            <div id="automationPanel"><div class="loading">Loading bot runtime...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Alerts</p>
                <h2>What Needs Attention</h2>
              </div>
            </div>
            <div id="warningsPanel"><div class="loading">Loading dashboard warnings...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Inspector</p>
                <h2>Lead Detail</h2>
              </div>
            </div>
            <div id="leadInspector"><div class="empty">Select a lead row to inspect strategy, signals, timeline, and generated email context.</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Coverage</p>
                <h2>Market Distribution</h2>
              </div>
            </div>
            <div class="split">
              <div>
                <p class="muted">Top cities</p>
                <div class="list" id="citiesDistribution"></div>
              </div>
              <div>
                <p class="muted">Top niches</p>
                <div class="list" id="nichesDistribution"></div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Attribution</p>
                <h2>Best Performing Angles</h2>
              </div>
            </div>
            <div class="split">
              <div>
                <p class="muted">Personas</p>
                <div id="personaAttribution"></div>
              </div>
              <div>
                <p class="muted">Hooks</p>
                <div id="hookAttribution"></div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Playbook</p>
                <h2>Top Training Examples</h2>
              </div>
            </div>
            <div id="examplesList"><div class="loading">Loading examples...</div></div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <p class="kicker">Runtime</p>
                <h2>Bot Configuration</h2>
              </div>
            </div>
            <div class="config-grid" id="runtimeConfig"><div class="loading">Loading runtime configuration...</div></div>
            <p class="muted" id="executionNote"></p>
          </section>
        </aside>
      </div>
    </main>
    <script>
      const REFRESH_INTERVAL_MS = 30000;
      const state = { payload: null, selectedLeadId: null };

      function escapeHtml(value) {
        return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
      }

      function formatNumber(value) {
        const number = Number(value ?? 0);
        return Number.isFinite(number) ? new Intl.NumberFormat().format(number) : '--';
      }

      function formatCompact(value) {
        const number = Number(value ?? 0);
        return Number.isFinite(number) ? new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(number) : '--';
      }

      function formatPercent(value) {
        const number = Number(value ?? 0);
        return Number.isFinite(number) ? `${number.toFixed(1)}%` : '--';
      }

      function formatDate(value) {
        if (!value) return '--';
        const date = new Date(String(value).replace(' ', 'T'));
        return Number.isNaN(date.getTime()) ? escapeHtml(value) : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
      }

      function formatRelative(value) {
        if (!value) return '--';
        const date = new Date(String(value).replace(' ', 'T'));
        if (Number.isNaN(date.getTime())) return '--';
        const delta = Math.round((date.getTime() - Date.now()) / 60000);
        if (Math.abs(delta) < 1) return 'just now';
        if (Math.abs(delta) < 60) return delta > 0 ? `in ${delta}m` : `${Math.abs(delta)}m ago`;
        const hours = Math.round(delta / 60);
        if (Math.abs(hours) < 24) return hours > 0 ? `in ${hours}h` : `${Math.abs(hours)}h ago`;
        const days = Math.round(hours / 24);
        return days > 0 ? `in ${days}d` : `${Math.abs(days)}d ago`;
      }

      function formatScore(value, percentMode = true) {
        const number = Number(value);
        if (!Number.isFinite(number)) return '--';
        if (percentMode || number > 1.2) return `${Math.round(number)} / 100`;
        return `${Math.round(number * 100)} / 100`;
      }

      function formatBytes(value) {
        const number = Number(value);
        if (!Number.isFinite(number) || number <= 0) return '--';
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = number;
        let unit = 0;
        while (size >= 1024 && unit < units.length - 1) {
          size /= 1024;
          unit += 1;
        }
        return `${size.toFixed(size >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
      }

      function formatUptime(value) {
        const seconds = Number(value ?? 0);
        if (!Number.isFinite(seconds)) return '--';
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
      }

      function pillClass(status) {
        const text = String(status || '').toLowerCase();
        if (['healthy', 'opened', 'interested', 'sale_closed', 'appointment_booked', 'running', 'sleeping', 'ready'].includes(text)) return 'good';
        if (['followup_sent', 'manual_queue', 'appointment_requested', 'needs_follow_up', 'queued', 'starting', 'attention'].includes(text)) return 'warn';
        if (['bounced', 'unsubscribed', 'blacklisted', 'failed', 'not_interested', 'error', 'blocked'].includes(text)) return 'bad';
        return 'soft';
      }

      function toneClass(status) {
        const text = String(status || '').toLowerCase();
        if (['healthy', 'good', 'ready', 'running', 'sleeping'].includes(text)) return 'good';
        if (['error', 'bad', 'blocked'].includes(text)) return 'bad';
        return 'warn';
      }

      function metric(label, value, note, tone) {
        return `<article class="metric"><div class="metric-label">${escapeHtml(label)}</div><div class="metric-value ${tone || ''}">${escapeHtml(value)}</div><div class="metric-note">${escapeHtml(note)}</div></article>`;
      }

      function barList(items, valueKey = 'count') {
        if (!items || !items.length) return '<div class="empty">No data yet.</div>';
        const max = Math.max(...items.map((item) => Number(item[valueKey] ?? 0)), 1);
        return items.map((item) => {
          const value = Number(item[valueKey] ?? 0);
          const width = Math.max(8, Math.round((value / max) * 100));
          return `<div class="bar-row"><div><strong>${escapeHtml(item.label || 'Unknown')}</strong><div class="bar-wrap"><div class="bar" style="width:${width}%"></div></div></div><div class="muted">${escapeHtml(formatNumber(value))}</div></div>`;
        }).join('');
      }

      function attributionList(items) {
        if (!items || !items.length) return '<div class="empty">No attribution data yet.</div>';
        return items.map((item) => `<div class="bar-row"><div><strong>${escapeHtml(item.label)}</strong><div class="muted">${escapeHtml(formatNumber(item.sent))} sent, ${escapeHtml(formatNumber(item.conversions))} conversions</div></div><div class="muted">${escapeHtml(formatPercent(item.conversion_rate))}</div></div>`).join('');
      }

      function contactSummary(lead) {
        const parts = [];
        if (lead.email) parts.push(lead.email);
        if (lead.phone) parts.push(lead.phone);
        return parts.length ? parts.join(' | ') : 'No direct contact';
      }

      function mergeLeadViews(payload) {
        const ids = new Map();
        [...(payload.top_leads || []), ...(payload.recent_leads || []), ...(payload.due_followups || [])].forEach((lead) => {
          if (lead && lead.id && !ids.has(lead.id)) ids.set(lead.id, lead);
        });
        return [...ids.values()].slice(0, 14);
      }

      function renderHero(payload) {
        const automation = payload.automation || {};
        document.getElementById('heroMeta').innerHTML = [
          `Mode: ${escapeHtml(payload.runtime.mode || 'web-dashboard')}`,
          `Uptime: ${escapeHtml(formatUptime(payload.runtime.uptime_seconds))}`,
          `Bot: ${escapeHtml(automation.status || 'unknown')}`,
          `DB: ${escapeHtml(payload.runtime.database?.backend || '--')} / ${escapeHtml(payload.runtime.database?.target || '--')}`,
          `Generated: ${escapeHtml(formatDate(payload.generated_at))}`,
        ].map((text) => `<span class="badge">${text}</span>`).join('');
        document.getElementById('lastRefresh').textContent = `Last refresh: ${formatDate(payload.generated_at)}`;
      }

      function renderOverview(payload) {
        const runtime = payload.runtime;
        const overview = payload.overview;
        const quality = payload.quality;
        const emailWindow = runtime.email_window || {};
        document.getElementById('overviewGrid').innerHTML = [
          metric('Total leads', formatCompact(overview.total_leads), 'Tracked in the lead database.', 'teal'),
          metric('With email', formatCompact(overview.with_email), 'Leads with a direct email contact.'),
          metric('With website', formatCompact(overview.with_website), 'Businesses with a discovered site.'),
          metric('Due follow-ups', formatCompact(overview.due_followups), 'Leads ready for another touch.', overview.due_followups ? 'gold' : ''),
          metric('Daily actions', `${formatNumber(overview.daily_actions)} / ${formatNumber(runtime.max_daily_actions)}`, `${formatNumber(overview.daily_remaining)} sends remain today.`),
          metric('High-value leads', formatCompact(overview.high_value), 'Leads marked as strong opportunities.', overview.high_value ? 'teal' : ''),
          metric('Blacklisted', formatCompact(overview.blacklisted), 'Leads excluded from further outreach.', overview.blacklisted ? 'danger' : ''),
          metric('Parent companies', formatCompact(overview.parent_companies), 'Shared-site organizations deduped.'),
          metric('Lead score avg', formatScore(quality.lead_score, true), 'Average score on scored leads.'),
          metric('Opportunity avg', formatScore(quality.opportunity_score, true), 'Average opportunity score stored.'),
          metric('PageSpeed avg', formatScore(quality.pagespeed_score, false), 'Average website performance score.'),
          metric('Email window', `${escapeHtml(emailWindow.start || '--')} - ${escapeHtml(emailWindow.end || '--')}`, emailWindow.is_open === null ? 'Window state unavailable.' : emailWindow.is_open ? 'Sending window is open.' : 'Sending window is closed.', emailWindow.is_open ? 'teal' : 'gold'),
        ].join('');
      }

      function renderActionCenter(payload) {
        const readiness = payload.readiness || {};
        const automation = payload.automation || {};
        const blockers = readiness.blockers || [];
        const checks = readiness.checks || [];
        const actionItems = payload.action_items || [];
        const statusTone = toneClass(readiness.status);
        const statusLabel = readiness.status === 'ready' ? 'Live Outreach Ready' : readiness.status === 'blocked' ? 'Sending Is Blocked' : 'Bot Needs Attention';

        document.getElementById('actionCenter').innerHTML = `
          <div class="readiness-shell">
            <article class="focus-card ${statusTone}">
              <p class="kicker" style="color:rgba(248,250,252,0.72);">Send readiness</p>
              <h3>${escapeHtml(statusLabel)}</h3>
              <p>${escapeHtml(readiness.summary || 'No readiness summary is available yet.')}</p>
              <div class="tag-row" style="margin-top:16px;">
                <span class="badge">Runner ${escapeHtml(automation.status || 'unknown')}</span>
                <span class="badge">Next ${escapeHtml(formatRelative(automation.next_run_at))}</span>
                <span class="badge">Last ${escapeHtml(formatRelative(automation.last_run_finished_at || automation.last_run_started_at))}</span>
              </div>
              ${blockers.length ? `<div style="margin-top:16px;color:rgba(248,250,252,0.82);font-size:14px;line-height:1.6;">${escapeHtml(blockers.slice(0, 3).join(' | '))}</div>` : ''}
            </article>
            <div class="stack" style="gap:12px;">
              <div class="check-list">
                ${checks.length ? checks.map((check) => `
                  <article class="check-item ${escapeHtml(check.status || 'warn')}">
                    <div class="check-dot"></div>
                    <div>
                      <div style="font-weight:700;margin-bottom:4px;">${escapeHtml(check.label || 'Check')}</div>
                      <div class="muted">${escapeHtml(check.detail || '')}</div>
                    </div>
                  </article>
                `).join('') : '<div class="empty">No readiness checks yet.</div>'}
              </div>
              <div class="action-list">
                ${actionItems.length ? actionItems.map((item) => `
                  <article class="action-item ${escapeHtml(item.level || 'info')}">
                    <div style="font-weight:700;margin-bottom:6px;">${escapeHtml(item.title || 'Action')}</div>
                    <div class="muted">${escapeHtml(item.message || '')}</div>
                  </article>
                `).join('') : '<div class="empty">No action items right now.</div>'}
              </div>
            </div>
          </div>
        `;
      }

      function renderHealth(payload) {
        const health = payload.health;
        const steps = [
          { label: 'Sent', value: health.sent_total, note: 'Base volume' },
          { label: 'Opened', value: health.opened_total, note: formatPercent(health.open_rate) },
          { label: 'Replies', value: health.reply_total, note: formatPercent(health.reply_rate) },
          { label: 'Conversions', value: health.conversion_total, note: formatPercent(health.conversion_rate) },
        ];
        const maxValue = Math.max(...steps.map((step) => Number(step.value ?? 0)), 1);
        document.getElementById('healthGrid').innerHTML = [
          metric('Sent', formatCompact(health.sent_total), 'Total sent events on record.', 'teal'),
          metric('Opened', formatCompact(health.opened_total), 'Recorded open or receipt signals.'),
          metric('Replies', formatCompact(health.reply_total), 'Reply outcomes classified by IMAP.', 'gold'),
          metric('Clicks', formatCompact(health.click_total), 'Tracked interest signals.'),
          metric('Conversions', formatCompact(health.conversion_total), 'Meetings, requests, or closed deals.', 'teal'),
          metric('Risk signals', formatCompact(health.risk_total), 'Bounces and unsubscribes to watch.', health.risk_total ? 'danger' : ''),
        ].join('');
        document.getElementById('healthRates').innerHTML = [
          `Open rate ${formatPercent(health.open_rate)}`,
          `Reply rate ${formatPercent(health.reply_rate)}`,
          `Conversion rate ${formatPercent(health.conversion_rate)}`,
        ].map((text) => `<span class="tag" style="background:rgba(15,118,110,0.10);color:#134e4a;">${escapeHtml(text)}</span>`).join('');
        document.getElementById('healthFunnel').innerHTML = `
          <div class="funnel-steps">
            ${steps.map((step) => {
              const value = Number(step.value ?? 0);
              const width = Math.max(value ? 12 : 6, Math.round((value / maxValue) * 100));
              return `
                <div class="funnel-step">
                  <div>
                    <strong>${escapeHtml(step.label)}</strong>
                    <div class="muted">${escapeHtml(step.note)}</div>
                  </div>
                  <div class="funnel-bar"><div class="funnel-fill" style="width:${width}%"></div></div>
                  <div><strong>${escapeHtml(formatNumber(value))}</strong></div>
                </div>
              `;
            }).join('')}
          </div>
        `;
      }

      function renderPipeline(payload) {
        document.getElementById('statusDistribution').innerHTML = barList(payload.pipeline.statuses);
        document.getElementById('stageDistribution').innerHTML = barList(payload.pipeline.stages);
      }

      function renderDistributions(payload) {
        document.getElementById('citiesDistribution').innerHTML = barList(payload.distributions.cities);
        document.getElementById('nichesDistribution').innerHTML = barList(payload.distributions.niches);
      }

      function renderAttributions(payload) {
        document.getElementById('personaAttribution').innerHTML = attributionList(payload.attribution.personas);
        document.getElementById('hookAttribution').innerHTML = attributionList(payload.attribution.hooks);
      }

      function renderAutomation(payload) {
        const automation = payload.automation || {};
        const output = (automation.output_tail || []).slice(-8).join('\n');
        document.getElementById('automationPanel').innerHTML = `
          <div class="tag-row" style="margin-bottom:12px;">
            <span class="pill ${pillClass(automation.status)}">${escapeHtml(automation.status || 'unknown')}</span>
            <span class="tag" style="background:rgba(23,33,46,0.08);color:#17212e;">Autostart ${automation.enabled ? 'on' : 'off'}</span>
          </div>
          <div class="config-grid" style="margin-bottom:12px;">
            <div class="config-item"><div class="label">Message</div><strong>${escapeHtml(automation.message || 'No status message')}</strong></div>
            <div class="config-item"><div class="label">Last run</div><strong>${escapeHtml(formatDate(automation.last_run_finished_at || automation.last_run_started_at))}</strong></div>
            <div class="config-item"><div class="label">Emails last run</div><strong>${escapeHtml(formatNumber(automation.last_run_emails_sent || 0))}</strong></div>
            <div class="config-item"><div class="label">Next run</div><strong>${escapeHtml(formatDate(automation.next_run_at))}</strong></div>
            <div class="config-item"><div class="label">Run duration</div><strong>${escapeHtml(formatUptime(automation.last_duration_seconds || 0))}</strong></div>
            <div class="config-item"><div class="label">Failures</div><strong>${escapeHtml(formatNumber(automation.consecutive_failures || 0))}</strong></div>
            <div class="config-item"><div class="label">Run cadence</div><strong>${escapeHtml(formatUptime(automation.loop_interval_seconds || 0))}</strong></div>
            <div class="config-item"><div class="label">Timeout</div><strong>${escapeHtml(formatUptime(automation.run_timeout_seconds || 0))}</strong></div>
          </div>
          ${automation.last_error ? `<div class="warning-item error"><strong>Last error</strong><div class="muted">${escapeHtml(automation.last_error)}</div></div>` : ''}
          ${(automation.command || []).length ? `<div class="command-line">${escapeHtml((automation.command || []).join(' '))}</div>` : ''}
          ${output ? `<div class="output-log">${escapeHtml(output)}</div>` : '<div class="empty">No bot output captured yet.</div>'}
        `;
      }

      function renderWarnings(payload) {
        const warnings = payload.warnings || [];
        if (!warnings.length) {
          document.getElementById('warningsPanel').innerHTML = '<div class="empty">No urgent warnings right now.</div>';
          return;
        }
        document.getElementById('warningsPanel').innerHTML = `<div class="warning-list">${warnings.map((warning) => `
          <article class="warning-item ${escapeHtml(warning.level || 'warn')}">
            <div style="font-weight:700;margin-bottom:6px;">${escapeHtml(warning.title || 'Notice')}</div>
            <div class="muted">${escapeHtml(warning.message || '')}</div>
          </article>
        `).join('')}</div>`;
      }

      function renderExamples(payload) {
        const examples = payload.training_examples || [];
        if (!examples.length) {
          document.getElementById('examplesList').innerHTML = '<div class="empty">Training examples will appear here after successful outreach is captured.</div>';
          return;
        }
        document.getElementById('examplesList').innerHTML = examples.map((example) => `
          <article class="example">
            <div class="tag-row" style="margin-bottom:10px;">
              <span class="pill ${pillClass(example.outcome_type)}">${escapeHtml(example.outcome_type || 'unknown')}</span>
              <span class="tag" style="background:rgba(23,33,46,0.08);color:#17212e;">${escapeHtml(example.persona || 'persona unknown')}</span>
            </div>
            <div style="font-weight:700;margin-bottom:8px;">${escapeHtml(example.subject || 'Untitled example')}</div>
            <div class="muted">${escapeHtml(example.body_preview || 'No body preview stored.')}</div>
          </article>
        `).join('');
      }

      function renderRuntime(payload) {
        const runtime = payload.runtime;
        const integrations = runtime.integrations || {};
        document.getElementById('runtimeConfig').innerHTML = [
          ['Database', `${runtime.database?.backend || '--'} / ${runtime.database?.target || '--'}`],
          ['Database size', formatBytes(runtime.database_size_bytes)],
          ['Bot autostart', runtime.bot_autostart_enabled ? 'Enabled' : 'Disabled'],
          ['Validation', runtime.validation_provider || '--'],
          ['Default tech', runtime.default_tech || '--'],
          ['Parallel workers', formatNumber(runtime.parallel_workers)],
          ['Batch size', formatNumber(runtime.batch_size)],
          ['SMTP ready', integrations.smtp_ready ? `Yes (${formatNumber(integrations.smtp_accounts || 0)} accounts)` : 'No'],
          ['IMAP tracking', integrations.imap_ready ? 'Enabled' : 'Not configured'],
          ['LLMs', [integrations.groq ? 'Groq' : '', integrations.openai ? 'OpenAI' : ''].filter(Boolean).join(' / ') || 'None'],
          ['Research APIs', [integrations.serpapi ? 'SerpAPI' : '', integrations.hunter ? 'Hunter' : '', integrations.builtwith ? 'BuiltWith' : '', integrations.proxycurl ? 'Proxycurl' : '', integrations.yelp ? 'Yelp' : ''].filter(Boolean).join(' / ') || 'None'],
        ].map(([label, value]) => `<div class="config-item"><div class="label">${escapeHtml(label)}</div><strong>${escapeHtml(value)}</strong></div>`).join('');
        document.getElementById('executionNote').textContent = runtime.execution_note || '';
      }

      function renderEvents(payload) {
        const rows = payload.recent_events || [];
        if (!rows.length) {
          document.getElementById('eventsTable').innerHTML = '<tr><td colspan="4" class="empty">No recent bot events yet.</td></tr>';
          return;
        }
        document.getElementById('eventsTable').innerHTML = rows.map((event) => `
          <tr class="row-link ${state.selectedLeadId === event.lead_id ? 'active' : ''}" data-lead-id="${escapeHtml(event.lead_id || '')}">
            <td><div>${escapeHtml(formatDate(event.timestamp))}</div><div class="muted">${escapeHtml(formatRelative(event.timestamp))}</div></td>
            <td><div><strong>${escapeHtml(event.business_name || 'Unlinked lead')}</strong></div><div class="muted">${escapeHtml(event.city || 'Unknown city')} | ${escapeHtml(event.niche || 'Unknown niche')}</div></td>
            <td><span class="pill ${pillClass(event.event_type)}">${escapeHtml((event.event_type || '').replaceAll('_', ' '))}</span></td>
            <td>${escapeHtml(event.summary || '')}</td>
          </tr>
        `).join('');
      }

      function renderFollowups(payload) {
        const rows = payload.due_followups || [];
        if (!rows.length) {
          document.getElementById('followupsTable').innerHTML = '<tr><td colspan="5" class="empty">No follow-ups are due right now.</td></tr>';
          return;
        }
        document.getElementById('followupsTable').innerHTML = rows.map((lead) => `
          <tr class="row-link ${state.selectedLeadId === lead.id ? 'active' : ''}" data-lead-id="${escapeHtml(lead.id)}">
            <td><div><strong>${escapeHtml(lead.business_name || 'Unnamed lead')}</strong></div><div class="muted">${escapeHtml(lead.niche || 'Unknown niche')} | ${escapeHtml(lead.city || 'Unknown city')}</div></td>
            <td><span class="pill ${pillClass(lead.status)}">${escapeHtml(lead.status || 'new')}</span></td>
            <td>${escapeHtml(contactSummary(lead))}</td>
            <td><div>${escapeHtml(formatDate(lead.next_action_due))}</div><div class="muted">${escapeHtml(formatRelative(lead.next_action_due))}</div></td>
            <td>${escapeHtml(formatScore(lead.lead_score ?? lead.opportunity_score, true))}</td>
          </tr>
        `).join('');
      }

      function renderLeads(payload) {
        const leads = mergeLeadViews(payload);
        if (!leads.length) {
          document.getElementById('leadsTable').innerHTML = '<tr><td colspan="5" class="empty">No leads have been saved yet.</td></tr>';
          return;
        }
        document.getElementById('leadsTable').innerHTML = leads.map((lead) => `
          <tr class="row-link ${state.selectedLeadId === lead.id ? 'active' : ''}" data-lead-id="${escapeHtml(lead.id)}">
            <td><div><strong>${escapeHtml(lead.business_name || 'Unnamed lead')}</strong></div><div class="muted">${escapeHtml(lead.sequence_stage || 'initial')} sequence</div></td>
            <td><span class="pill ${pillClass(lead.status)}">${escapeHtml(lead.status || 'new')}</span></td>
            <td>${escapeHtml(lead.city || 'Unknown city')}<div class="muted">${escapeHtml(lead.niche || 'Unknown niche')}</div></td>
            <td>${escapeHtml(contactSummary(lead))}</td>
            <td><div>${escapeHtml(formatDate(lead.updated_at))}</div><div class="muted">${escapeHtml(formatRelative(lead.updated_at))}</div></td>
          </tr>
        `).join('');
      }

      function renderLeadDetail(detail) {
        if (!detail || !detail.lead) {
          document.getElementById('leadInspector').innerHTML = '<div class="empty">Lead detail is unavailable.</div>';
          return;
        }
        const lead = detail.lead;
        const issues = (lead.audit_issues || []).map((issue) => `<span class="tag" style="background:rgba(217,119,6,0.12);color:#9a5b00;">${escapeHtml(issue)}</span>`).join('') || '<span class="muted">No audit issues stored.</span>';
        const personas = (detail.recent_personas || []).map((persona) => `<span class="tag" style="background:rgba(15,118,110,0.10);color:#134e4a;">${escapeHtml(persona)}</span>`).join('') || '<span class="muted">No persona history yet.</span>';
        const services = (lead.services || []).map((service) => `<span class="tag" style="background:rgba(23,33,46,0.08);color:#17212e;">${escapeHtml(service)}</span>`).join('') || '<span class="muted">No extracted services stored.</span>';
        const timeline = (detail.timeline || []).length ? detail.timeline.slice(-10).reverse().map((item) => `<div class="timeline-item"><div class="tag-row"><span class="pill ${pillClass(item.event)}">${escapeHtml((item.event || '').replaceAll('_', ' '))}</span><span class="muted">${escapeHtml(formatDate(item.timestamp))}</span></div><div style="margin-top:8px;"><strong>${escapeHtml(item.summary || '')}</strong></div></div>`).join('') : '<div class="empty">No event timeline has been recorded for this lead yet.</div>';

        document.getElementById('leadInspector').innerHTML = `
          <div class="tag-row" style="margin-bottom:12px;">
            <span class="pill ${pillClass(lead.status)}">${escapeHtml(lead.status || 'new')}</span>
            ${lead.high_value ? '<span class="tag" style="background:rgba(15,118,110,0.10);color:#134e4a;">High value</span>' : ''}
            ${lead.blacklisted ? '<span class="tag" style="background:rgba(185,28,28,0.10);color:#b91c1c;">Blacklisted</span>' : ''}
          </div>
          <h3 style="margin:0 0 8px;font-size:24px;letter-spacing:-0.03em;">${escapeHtml(lead.business_name || 'Unnamed lead')}</h3>
          <p class="muted" style="margin:0 0 16px;">${escapeHtml(lead.niche || 'Unknown niche')} in ${escapeHtml(lead.city || 'Unknown city')}</p>

          <div class="config-grid" style="margin-bottom:16px;">
            <div class="config-item"><div class="label">Primary email</div><strong>${escapeHtml(lead.email || 'None found')}</strong></div>
            <div class="config-item"><div class="label">Phone</div><strong>${escapeHtml(lead.phone || 'None found')}</strong></div>
            <div class="config-item"><div class="label">Next action due</div><strong>${escapeHtml(formatDate(lead.next_action_due))}</strong></div>
            <div class="config-item"><div class="label">Lead score</div><strong>${escapeHtml(formatScore(lead.lead_score ?? lead.opportunity_score, true))}</strong></div>
          </div>

          <div class="panel" style="padding:16px;margin-bottom:16px;background:rgba(255,255,255,0.55);">
            <p class="kicker">Strategy</p>
            <div style="font-weight:700;margin-bottom:10px;">${escapeHtml(lead.strategy || 'No strategy stored yet.')}</div>
            <div class="tag-row">${issues}</div>
          </div>

          <div class="panel" style="padding:16px;margin-bottom:16px;background:rgba(255,255,255,0.55);">
            <p class="kicker">Signals</p>
            <div class="tag-row" style="margin-bottom:10px;">${services}</div>
            <div class="muted">${escapeHtml(lead.local_market_signal || 'No local market signal stored.')}</div>
          </div>

          <div class="panel" style="padding:16px;margin-bottom:16px;background:rgba(255,255,255,0.55);">
            <p class="kicker">Recent personas</p>
            <div class="tag-row">${personas}</div>
          </div>

          <div class="panel" style="padding:16px;margin-bottom:16px;background:rgba(255,255,255,0.55);">
            <p class="kicker">Last generated email</p>
            <div style="font-weight:700;margin-bottom:8px;">${escapeHtml(detail.last_generated_email?.subject || 'No generated email stored yet.')}</div>
            <div class="muted" style="white-space:pre-wrap;">${escapeHtml(detail.last_generated_email?.body_preview || 'No body preview stored yet.')}</div>
          </div>

          <div><p class="kicker">Timeline</p><div>${timeline}</div></div>
        `;
      }

      async function fetchJson(url) {
        const response = await fetch(url, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`Request failed: ${response.status}`);
        return response.json();
      }

      async function postJson(url) {
        const response = await fetch(url, { method: 'POST', headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`Request failed: ${response.status}`);
        return response.json();
      }

      async function loadLeadDetail(leadId, scrollToPanel = false) {
        if (!leadId) return;
        state.selectedLeadId = Number(leadId);
        try {
          const detail = await fetchJson(`/api/dashboard/leads/${state.selectedLeadId}`);
          renderLeadDetail(detail);
          renderEvents(state.payload || { recent_events: [] });
          renderFollowups(state.payload || { due_followups: [] });
          renderLeads(state.payload || { recent_leads: [], top_leads: [], due_followups: [] });
          if (scrollToPanel) document.getElementById('leadInspector').scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) {
          document.getElementById('leadInspector').innerHTML = `<div class="error">Failed to load lead detail: ${escapeHtml(error.message)}</div>`;
        }
      }

      async function loadDashboard() {
        const button = document.getElementById('refreshButton');
        button.disabled = true;
        button.textContent = 'Refreshing...';
        try {
          const payload = await fetchJson('/api/dashboard');
          state.payload = payload;
          renderHero(payload);
          renderOverview(payload);
          renderActionCenter(payload);
          renderHealth(payload);
          renderPipeline(payload);
          renderDistributions(payload);
          renderAttributions(payload);
          renderAutomation(payload);
          renderWarnings(payload);
          renderExamples(payload);
          renderRuntime(payload);
          renderEvents(payload);
          renderFollowups(payload);
          renderLeads(payload);

          if (!state.selectedLeadId) {
            const firstLead = (payload.due_followups && payload.due_followups[0]) || (payload.recent_leads && payload.recent_leads[0]) || (payload.top_leads && payload.top_leads[0]);
            if (firstLead && firstLead.id) state.selectedLeadId = firstLead.id;
          }
          if (state.selectedLeadId) await loadLeadDetail(state.selectedLeadId, false);
        } catch (error) {
          document.getElementById('overviewGrid').innerHTML = `<div class="error">Failed to load dashboard: ${escapeHtml(error.message)}</div>`;
        } finally {
          button.disabled = false;
          button.textContent = 'Refresh Data';
        }
      }

      document.addEventListener('click', (event) => {
        const row = event.target.closest('[data-lead-id]');
        if (!row) return;
        const leadId = row.getAttribute('data-lead-id');
        if (leadId) loadLeadDetail(leadId, true);
      });

      document.getElementById('refreshButton').addEventListener('click', loadDashboard);
      document.getElementById('runBotButton').addEventListener('click', async () => {
        const button = document.getElementById('runBotButton');
        button.disabled = true;
        button.textContent = 'Queueing...';
        try {
          await postJson('/api/bot/run-now');
          await loadDashboard();
        } catch (error) {
          document.getElementById('warningsPanel').innerHTML = `<div class="error">Failed to queue bot run: ${escapeHtml(error.message)}</div>`;
        } finally {
          button.disabled = false;
          button.textContent = 'Run Bot Now';
        }
      });
      loadDashboard();
      window.setInterval(loadDashboard, REFRESH_INTERVAL_MS);
    </script>
  </body>
</html>
'''

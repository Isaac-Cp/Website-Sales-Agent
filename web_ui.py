def render_dashboard_shell():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Website Sales Agent Dashboard</title>
  <style>
    :root{--bg:#f7f0e4;--bg2:#e9decd;--ink:#162233;--muted:#66788d;--panel:rgba(255,255,255,.82);--line:rgba(22,34,51,.09);--good:#0f766e;--goodbg:rgba(15,118,110,.1);--info:#2563eb;--infobg:rgba(37,99,235,.1);--warn:#d97706;--warnbg:rgba(217,119,6,.12);--bad:#c2410c;--badbg:rgba(194,65,12,.12);--shadow:0 18px 48px rgba(22,34,51,.08)}
    *{box-sizing:border-box}body{margin:0;min-height:100vh;color:var(--ink);font-family:"Avenir Next","Trebuchet MS","Segoe UI",sans-serif;background:radial-gradient(circle at top left,rgba(15,118,110,.12),transparent 26%),radial-gradient(circle at top right,rgba(217,119,6,.16),transparent 22%),linear-gradient(180deg,#fffaf3 0%,var(--bg) 55%,var(--bg2) 100%)}
    .shell{width:min(1480px,calc(100% - 20px));margin:0 auto;padding:18px 0 40px}
    .hero,.panel{border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}
    .hero{padding:28px;color:#f8fafc;background:linear-gradient(140deg,rgba(13,56,70,.98),rgba(22,34,51,.98))}
    .hero-grid,.layout,.dual,.split,.metrics,.proof,.stack,.checks,.bars,.days,.runs,.notices,.timeline,.examples{display:grid;gap:16px}
    .hero-grid{grid-template-columns:minmax(0,1.35fr) minmax(280px,.9fr)}
    .layout{grid-template-columns:minmax(0,1.42fr) minmax(340px,.88fr);margin-top:18px}
    .panel{padding:22px;background:var(--panel);backdrop-filter:blur(8px)}
    .sticky{position:sticky;top:88px}
    .eyebrow,.badge,.pill,.btn,.tag{display:inline-flex;align-items:center;gap:8px;padding:9px 12px;border-radius:999px;font-weight:700}
    .eyebrow{background:rgba(255,255,255,.12);text-transform:uppercase;letter-spacing:.08em;font-size:11px}
    .badge,.tag{background:rgba(255,255,255,.12);color:#f8fafc;font-size:13px}
    .pill{font-size:12px;padding:8px 11px}
    .pill.good{color:var(--good);background:var(--goodbg)}.pill.info{color:var(--info);background:var(--infobg)}.pill.warn{color:#9a5b00;background:var(--warnbg)}.pill.bad{color:var(--bad);background:var(--badbg)}.pill.soft{color:var(--ink);background:rgba(22,34,51,.08)}
    h1{margin:16px 0 12px;font-size:clamp(34px,5vw,62px);line-height:.97;letter-spacing:-.05em}h2{margin:0;font-size:20px;letter-spacing:-.03em}h3{margin:0}
    .hero p{max-width:760px;color:rgba(248,250,252,.83);line-height:1.7}
    .row,.badges,.actions,.toolbar-row,.controls,.tags{display:flex;flex-wrap:wrap;gap:10px}
    .hero-card,.card,.mini{padding:18px;border-radius:22px;border:1px solid var(--line);background:rgba(255,255,255,.68)}
    .hero-card{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.12)}
    .hero-card p{margin:8px 0 0}
    .sec{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.sec p{margin:0 0 6px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
    .muted{color:var(--muted)}
    .toolbar{position:sticky;top:10px;z-index:20;margin-top:18px;background:rgba(255,251,246,.94)}
    .field,.select{min-width:120px;padding:11px 12px;border-radius:16px;border:1px solid rgba(22,34,51,.16);background:rgba(255,255,255,.88);font:inherit;color:var(--ink)}.search{min-width:260px;flex:1 1 260px}
    .btn{border:0;cursor:pointer;text-decoration:none;font:inherit}.btn.primary{background:linear-gradient(180deg,#fde68a,#f59e0b);color:#10201f}.btn.secondary{background:rgba(255,255,255,.12);color:#f8fafc}.btn.ghost{background:rgba(22,34,51,.08);color:var(--ink)}
    .metrics{grid-template-columns:repeat(5,minmax(0,1fr))}.proof{grid-template-columns:repeat(4,minmax(0,1fr))}.split{grid-template-columns:repeat(2,minmax(0,1fr))}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
    .focus{padding:22px;border-radius:24px;color:#f8fafc;background:linear-gradient(140deg,rgba(15,118,110,.98),rgba(14,88,102,.96))}.focus.warn{background:linear-gradient(140deg,rgba(180,83,9,.98),rgba(146,64,14,.96))}.focus.bad{background:linear-gradient(140deg,rgba(154,52,18,.98),rgba(127,29,29,.96))}.focus h3{margin:10px 0 8px;font-size:clamp(28px,4vw,44px);line-height:.98;letter-spacing:-.05em}.focus p{margin:0;color:rgba(248,250,252,.84)}
    .label{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.value{margin-top:10px;font-size:clamp(24px,3vw,38px);font-weight:800;letter-spacing:-.05em}.note{margin-top:10px;color:var(--muted);line-height:1.55}
    .highlight{color:#f8fafc;background:linear-gradient(140deg,rgba(13,56,70,.96),rgba(15,118,110,.94));border-color:rgba(255,255,255,.08)}.highlight .label,.highlight .note{color:rgba(248,250,252,.82)}
    .item,.run,.notice,.timeline-item,.example,.detail,.barrow,.funnelrow{padding:14px 16px;border-radius:18px;border:1px solid var(--line);background:rgba(255,255,255,.64)}
    .check{display:grid;grid-template-columns:12px minmax(0,1fr);gap:12px;align-items:start}.dot{width:12px;height:12px;border-radius:999px;margin-top:4px;background:rgba(102,119,140,.45)}.good .dot{background:var(--good)}.info .dot{background:var(--info)}.warn .dot{background:var(--warn)}.bad .dot{background:var(--bad)}
    .tone-good{background:var(--goodbg)}.tone-info{background:var(--infobg)}.tone-warn{background:var(--warnbg)}.tone-bad{background:var(--badbg)}
    .barrow{display:grid;grid-template-columns:minmax(90px,150px) minmax(0,1fr) auto;gap:12px;align-items:center}.funnelrow{display:grid;grid-template-columns:minmax(120px,160px) minmax(0,1fr) auto;gap:12px;align-items:center}
    .track,.mini-track{height:12px;border-radius:999px;background:rgba(22,34,51,.08);overflow:hidden}.fill,.mini-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,var(--good),#2dd4bf)}.mini-fill.reply{background:linear-gradient(90deg,var(--info),#60a5fa)}.mini-fill.warn{background:linear-gradient(90deg,var(--warn),#fbbf24)}.mini-fill.convert{background:linear-gradient(90deg,#15803d,#4ade80)}
    .days{grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}.day h3{margin:0 0 12px;font-size:16px}.mini-row{display:grid;grid-template-columns:56px auto minmax(0,1fr);gap:10px;align-items:center;margin-top:9px}.mini-row:first-of-type{margin-top:0}.mini-label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
    .table{overflow:auto;border:1px solid var(--line);border-radius:20px;background:rgba(255,255,255,.56)}table{width:100%;border-collapse:collapse}th,td{padding:12px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}tr:last-child td{border-bottom:0}
    .click{cursor:pointer;transition:background .14s ease}.click:hover,.click.active{background:rgba(15,118,110,.08)}
    .code,.log{padding:14px;border-radius:18px;background:rgba(22,34,51,.94);color:#dbe6ef;font-family:"Consolas","IBM Plex Mono",monospace;font-size:12px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
    .empty,.loading,.error{padding:16px;border-radius:18px}.empty,.loading{color:var(--muted);background:rgba(255,255,255,.56)}.error{color:var(--bad);background:var(--badbg)}
    .dark-mode {
      --bg: #1a1a1a;
      --bg2: #2a2a2a;
      --ink: #e0e0e0;
      --muted: #a0a0a0;
      --panel: rgba(42,42,42,.82);
      --line: rgba(224,224,224,.09);
      --good: #4ade80;
      --goodbg: rgba(74,222,128,.1);
      --info: #60a5fa;
      --infobg: rgba(96,165,250,.1);
      --warn: #fbbf24;
      --warnbg: rgba(251,191,36,.12);
      --bad: #f87171;
      --badbg: rgba(248,113,113,.12);
      --shadow: 0 18px 48px rgba(0,0,0,.3);
    }
    .dark-mode .hero {
      background: linear-gradient(140deg, rgba(26,26,26,.98), rgba(42,42,42,.98));
    }
    .dark-mode .focus {
      background: linear-gradient(140deg, rgba(74,222,128,.98), rgba(15,118,110,.96));
    }
    .dark-mode .focus.warn {
      background: linear-gradient(140deg, rgba(251,191,36,.98), rgba(217,119,6,.96));
    }
    .dark-mode .focus.bad {
      background: linear-gradient(140deg, rgba(248,113,113,.98), rgba(194,65,12,.96));
    }
    .dark-mode .highlight {
      background: linear-gradient(140deg, rgba(26,26,26,.96), rgba(74,222,128,.94));
    }
    .export-btn, .dark-toggle {
      margin-left: 10px;
    }
    @media (max-width:1260px){.hero-grid,.layout,.metrics,.proof,.split,.grid2{grid-template-columns:1fr}.sticky,.toolbar{position:static}}
    @media (max-width:760px){.shell{width:min(100%,calc(100% - 14px));padding-top:10px}.hero,.panel{border-radius:22px}.hero{padding:22px}.barrow,.funnelrow,.mini-row{grid-template-columns:1fr}.actions{flex-direction:column;gap:8px}.toolbar-row{flex-direction:column;gap:8px}.field,.select{min-width:100%}}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>📊 Sales Agent Dashboard</h1>
      <p>Monitor your automated outreach, track performance, and manage leads in real-time.</p>
      <div class="actions">
        <button class="btn primary" id="refreshBtn">🔄 Refresh</button>
        <button class="btn secondary" id="runBtn">▶️ Run Bot</button>
        <button class="btn secondary export-btn" id="exportLeadsBtn">📥 Export Leads</button>
        <button class="btn secondary export-btn" id="exportEventsBtn">📊 Export Events</button>
        <button class="btn secondary dark-toggle" id="darkModeToggle">🌙 Dark Mode</button>
        <a class="btn secondary" href="/health">❤️ Health</a>
        <a class="btn secondary" href="/status">📈 Status</a>
      </div>
    </section>

    <div class="filters" id="filters">
      <input class="field search" id="search" type="search" placeholder="Search leads, cities, niches...">
      <select class="select" id="status"><option value="">All Statuses</option></select>
      <select class="select" id="city"><option value="">All Cities</option></select>
      <select class="select" id="niche"><option value="">All Niches</option></select>
      <select class="select" id="etype"><option value="">All Events</option></select>
      <input class="field" id="dateFrom" type="date" placeholder="From">
      <input class="field" id="dateTo" type="date" placeholder="To">
      <button class="btn" id="clearFilters">🗑️ Clear</button>
    </div>

    <div class="grid">
      <div class="card">
        <h2>📈 Key Metrics</h2>
        <div id="metrics"></div>
      </div>
      <div class="card">
        <h2>🎯 Outreach Proof</h2>
        <div id="proof"></div>
      </div>
      <div class="card">
        <h2>📊 Activity Timeline</h2>
        <div class="chart"><canvas id="activityChart"></canvas></div>
      </div>
      <div class="card">
        <h2>📋 Lead Funnel</h2>
        <div id="funnel"></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>🏗️ Pipeline</h2>
        <div id="pipeline"></div>
      </div>
      <div class="card">
        <h2>🎨 Attribution</h2>
        <div id="attribution"></div>
      </div>
    </div>

    <div class="card">
      <h2>📅 Recent Events</h2>
      <div class="table"><table><thead><tr><th>When</th><th>Event</th><th>Lead</th><th>Summary</th></tr></thead><tbody id="events"></tbody></table></div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>⏰ Due Follow-ups</h2>
        <div class="table"><table><thead><tr><th>Lead</th><th>Status</th><th>Contact</th><th>Due</th></tr></thead><tbody id="followups"></tbody></table></div>
      </div>
      <div class="card">
        <h2>👥 Lead Workspace</h2>
        <div class="table"><table><thead><tr><th>Lead</th><th>Status</th><th>Location</th><th>Contact</th><th>Updated</th></tr></thead><tbody id="leads"></tbody></table></div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>⚙️ Bot Controls</h2>
        <div id="controls"></div>
      </div>
      <div class="card">
        <h2>🔧 Diagnostics</h2>
        <div id="diag"></div>
      </div>
    </div>

    <div class="card">
      <h2>🚨 Notices</h2>
      <div id="notices"></div>
    </div>

    <div class="card">
      <h2>🏃 Run History</h2>
      <div id="runs"></div>
    </div>

    <div class="card">
      <h2>🔍 Lead Detail</h2>
      <div id="detail"></div>
    </div>
  </main>
  <script>
    const state={payload:null,leadId:null,search:'',status:'',city:'',niche:'',eventType:'',dateFrom:'',dateTo:''},REFRESH=30000;
    const $=id=>document.getElementById(id);
    const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
    const num=v=>Number.isFinite(Number(v))?new Intl.NumberFormat().format(Number(v)):'--';
    const pct=v=>Number.isFinite(Number(v))?`${Number(v).toFixed(1)}%`:'--';
    const rel=v=>{const d=v?new Date(v):null;if(!d||Number.isNaN(d.getTime()))return'unknown';const s=Math.round((d.getTime()-Date.now())/1000),a=Math.abs(s);if(a<60)return s>=0?'in under a minute':'under a minute ago';const m=Math.round(s/60);if(Math.abs(m)<60)return m>=0?`in ${Math.abs(m)} min`:`${Math.abs(m)} min ago`;const h=Math.round(m/60);if(Math.abs(h)<24)return h>=0?`in ${Math.abs(h)} hr`:`${Math.abs(h)} hr ago`;const day=Math.round(h/24);return day>=0?`in ${Math.abs(day)} day${Math.abs(day)===1?'':'s'}`:`${Math.abs(day)} day${Math.abs(day)===1?'':'s'} ago`};
    const date=v=>{const d=v?new Date(v):null;return!d||Number.isNaN(d.getTime())?(v?String(v):'--'):d.toLocaleString()};
    const shortDate=v=>{const d=v?new Date(v):null;return!d||Number.isNaN(d.getTime())?(v?String(v):'--'):d.toLocaleDateString(undefined,{month:'short',day:'numeric'})};
    const uptime=s=>{const t=Math.max(0,Number(s||0)),d=Math.floor(t/86400),h=Math.floor((t%86400)/3600),m=Math.floor((t%3600)/60);return d?`${d}d ${h}h`:h?`${h}h ${m}m`:`${m}m`};
    const first=(...v)=>{for(const x of v){if(x===null||x===undefined)continue;const t=String(x).trim();if(t)return t}return''};
    const tone=v=>{const x=String(v||'').toLowerCase();if(['good','success','ready','active','working','live_send'].includes(x))return'good';if(['info','queued','sleeping'].includes(x))return'info';if(['warn','warning','attention','warming','generated_only'].includes(x))return'warn';if(['bad','error','blocked','disabled','idle','none','runner_only'].includes(x))return'bad';return'soft'};
    const pill=v=>tone(v)==='bad'?'bad':tone(v)==='warn'?'warn':tone(v)==='info'?'info':tone(v)==='good'?'good':'soft';
    const merge=p=>{const seen=new Set(),out=[];for(const g of [p.lead_feed||[],p.due_followups||[],p.recent_leads||[],p.top_leads||[]])for(const l of g){if(!l||!l.id||seen.has(l.id))continue;seen.add(l.id);out.push(l)}return out};
    const proofLabel=l=>l==='live_send'?'Live send proven':l==='generated_only'?'Generating only':l==='runner_only'?'Runner active, no send proof':'No proof yet';
    const contact=l=>first(l.email,l.phone,'No direct contact');
    const leadMatch=l=>{if(!l)return false;const q=state.search.trim().toLowerCase();if(q&&!`${l.business_name||''} ${l.city||''} ${l.niche||''} ${l.email||''} ${l.phone||''} ${l.status||''} ${l.sequence_stage||''}`.toLowerCase().includes(q))return false;if(state.status&&String(l.status||'').toLowerCase()!==state.status.toLowerCase())return false;if(state.city&&String(l.city||'').toLowerCase()!==state.city.toLowerCase())return false;if(state.niche&&String(l.niche||'').toLowerCase()!==state.niche.toLowerCase())return false;if(state.dateFrom&&l.updated_at&&new Date(l.updated_at)<new Date(state.dateFrom))return false;if(state.dateTo&&l.updated_at&&new Date(l.updated_at)>new Date(state.dateTo+'T23:59:59'))return false;return true};
    const eventMatch=e=>{if(!e)return false;const q=state.search.trim().toLowerCase();if(q&&!`${e.business_name||''} ${e.city||''} ${e.niche||''} ${e.event_type||''} ${e.summary||''}`.toLowerCase().includes(q))return false;if(state.status&&String(e.status||'').toLowerCase()!==state.status.toLowerCase())return false;if(state.city&&String(e.city||'').toLowerCase()!==state.city.toLowerCase())return false;if(state.niche&&String(e.niche||'').toLowerCase()!==state.niche.toLowerCase())return false;if(state.eventType&&String(e.event_type||'').toLowerCase()!==state.eventType.toLowerCase())return false;if(state.dateFrom&&e.timestamp&&new Date(e.timestamp)<new Date(state.dateFrom))return false;if(state.dateTo&&e.timestamp&&new Date(e.timestamp)>new Date(state.dateTo+'T23:59:59'))return false;return true};
    async function get(url){const r=await fetch(url,{headers:{Accept:'application/json'}});if(!r.ok)throw new Error(`Request failed: ${r.status}`);return r.json()}
    function exportToCSV(data, filename) {
      const headers = Object.keys(data[0] || {});
      const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${String(row[h] || '').replace(/"/g, '""')}"`).join(','))].join('\\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }

    function exportLeads() {
      if (!state.payload) return;
      const leads = merge(state.payload).filter(leadMatch);
      exportToCSV(leads, 'leads.csv');
    }

    function exportEvents() {
      if (!state.payload) return;
      const events = (state.payload.recent_events || []).filter(eventMatch);
      exportToCSV(events, 'events.csv');
    }

    function toggleDarkMode() {
      document.body.classList.toggle('dark-mode');
      const btn = $('darkModeToggle');
      btn.textContent = document.body.classList.contains('dark-mode') ? '☀️ Light Mode' : '🌙 Dark Mode';
    }

    // Auto-refresh function
    function startAutoRefresh(){
      setInterval(async () => {
        try {
          const p = await get('/api/dashboard');
          state.payload = p;
          rerender();
        } catch (e) {
          console.error('Auto-refresh failed:', e);
        }
      }, REFRESH);
    }

    function renderHero(p){
      const r=p.readiness||{},pr=p.proof_of_outreach||{},a=p.automation||{},d=p.deployment_diagnostics||{},rt=p.runtime||{};
      const badges=[['Readiness',r.status||'unknown',tone(r.status)],['Outreach proof',proofLabel(pr.proof_level),pr.proof_level],['Runner',a.status||'unknown',a.status],['Storage',d.database_persistent?'Persistent':'Ephemeral',d.database_persistent?'good':'warn'],['Copy mode',d.optional_warnings&&d.optional_warnings.length?'Fallback templates':'LLM-ready',d.optional_warnings&&d.optional_warnings.length?'warn':'good']];
      $('heroBadges').innerHTML=badges.map(([l,v,t])=>`<span class="badge" style="${tone(t)!=='soft'?`background:${t==='good'||t==='live_send'?'rgba(15,118,110,.18)':t==='info'?'rgba(37,99,235,.18)':t==='warn'||t==='generated_only'?'rgba(217,119,6,.18)':'rgba(194,65,12,.18)'};`:''}">${esc(l)}: ${esc(v)}</span>`).join('');
      $('heroHeadline').textContent=pr.proof_level==='live_send'?'Live outreach is proven.':r.status==='blocked'?'The dashboard is live, but outreach is blocked.':r.status==='attention'?'The bot can run, but it still needs attention.':'The dashboard is watching a healthy bot loop.';
      $('heroNarrative').textContent=pr.proof_level==='live_send'?`Last verified live send was ${rel(pr.last_live_send?.timestamp)} for ${pr.last_live_send?.business_name||'a lead'}.`:pr.proof_level==='generated_only'?'The bot is generating outreach, but the latest stored proof is not a confirmed live send yet.':d.dry_run?'The app is in DRY_RUN, so it can generate previews without delivering real emails.':r.summary||'Waiting for enough data to describe the loop.';
      $('lastRefresh').textContent=`Last refreshed ${date(p.generated_at)} · uptime ${uptime(rt.uptime_seconds)}`;
    }

    function renderFilters(p){
      const f=p.filters||{};
      $('filters').innerHTML=`<div class="toolbar-row"><input class="field search" id="search" type="search" placeholder="Search lead, city, niche, email, or event summary" value="${esc(state.search)}"><select class="select" id="status"><option value="">All statuses</option>${(f.statuses||[]).map(v=>`<option value="${esc(v)}" ${state.status===v?'selected':''}>${esc(v)}</option>`).join('')}</select><select class="select" id="city"><option value="">All cities</option>${(f.cities||[]).map(v=>`<option value="${esc(v)}" ${state.city===v?'selected':''}>${esc(v)}</option>`).join('')}</select><select class="select" id="niche"><option value="">All niches</option>${(f.niches||[]).map(v=>`<option value="${esc(v)}" ${state.niche===v?'selected':''}>${esc(v)}</option>`).join('')}</select><select class="select" id="etype"><option value="">All events</option>${(f.event_types||[]).map(v=>`<option value="${esc(v.replaceAll('_',' '))}" ${state.eventType===v?'selected':''}>${esc(v.replaceAll('_',' '))}</option>`).join('')}</select><input class="field" id="dateFrom" type="date" placeholder="From date" value="${esc(state.dateFrom)}"><input class="field" id="dateTo" type="date" placeholder="To date" value="${esc(state.dateTo)}"><button class="btn ghost" id="clearFilters" type="button">Clear filters</button></div>`;
      $('search').addEventListener('input',e=>{state.search=e.target.value;rerender()});$('status').addEventListener('change',e=>{state.status=e.target.value;rerender()});$('city').addEventListener('change',e=>{state.city=e.target.value;rerender()});$('niche').addEventListener('change',e=>{state.niche=e.target.value;rerender()});$('etype').addEventListener('change',e=>{state.eventType=e.target.value;rerender()});$('dateFrom').addEventListener('change',e=>{state.dateFrom=e.target.value;rerender()});$('dateTo').addEventListener('change',e=>{state.dateTo=e.target.value;rerender()});
      $('clearFilters').addEventListener('click',()=>{state.search='';state.status='';state.city='';state.niche='';state.eventType='';state.dateFrom='';state.dateTo='';renderFilters(p);rerender()});
    }

    function renderCommand(p){
      const r=p.readiness||{},pr=p.proof_of_outreach||{},actions=p.action_items||[],checks=r.checks||[],cls=tone(r.status)==='warn'?'warn':tone(r.status)==='bad'?'bad':'';
      $('command').innerHTML=`<div class="split"><article class="focus ${cls}"><div class="eyebrow">Top story</div><h3>${esc(pr.pulse_title||'Waiting for outreach proof')}</h3><p>${esc(pr.pulse_message||r.summary||'')}</p><div class="tags" style="margin-top:16px"><span class="pill ${pill(r.status)}">${esc(r.status||'unknown')}</span><span class="pill ${pill(pr.proof_level)}">${esc(proofLabel(pr.proof_level))}</span></div></article><div class="stack"><article class="card"><div class="sec" style="margin-bottom:12px"><div><p>System checks</p><h2>What the app verified</h2></div></div><div class="checks">${checks.length?checks.map(i=>`<div class="check ${tone(i.status)}"><span class="dot"></span><div><strong>${esc(i.label||'Check')}</strong><div class="muted" style="margin-top:6px">${esc(i.detail||'')}</div></div></div>`).join(''):'<div class="empty">No readiness checks were returned.</div>'}</div></article><article class="card"><div class="sec" style="margin-bottom:12px"><div><p>Next actions</p><h2>Best next moves</h2></div></div><div class="stack">${actions.length?actions.map(i=>`<div class="item tone-${tone(i.level)}"><strong>${esc(i.title||'Action')}</strong><div class="muted" style="margin-top:6px">${esc(i.message||'')}</div></div>`).join(''):'<div class="empty">No immediate action items. The bot is not surfacing urgent follow-up work right now.</div>'}</div></article></div></div>`;
    }

    function renderMetrics(p){
      const o=p.overview||{},h=p.health||{},items=[['Leads stored',num(o.total_leads),`${num(o.high_value)} high-value`],['Leads with email',num(o.with_email),`${num(o.with_phone)} with phone`],['Emails sent',num(h.sent_total),`${pct(h.open_rate)} open · ${pct(h.reply_rate)} reply`],['Replies',num(h.reply_total),`${num(h.conversion_total)} conversions`],['Due follow-ups',num(o.due_followups),`${num(o.daily_remaining)} remaining`]];
      $('metrics').innerHTML=items.map(([l,v,n])=>`<div class="metric"><div><div class="value">${v}</div><div class="label">${l}</div></div><div class="label">${n}</div></div>`).join('');
    }

    function renderProof(p){
      const pr=p.proof_of_outreach||{},cards=[['Outreach status',proofLabel(pr.proof_level),pr.pulse_message||'',pr.proof_level],['Latest run',date(pr.last_run?.finished_at||pr.last_run?.started_at),pr.last_run?`${num(pr.last_run.emails_sent||0)} sent · ${pr.last_run.status||''}`:'No run',pr.last_run?.status],['Latest live send',pr.last_live_send?.business_name||'None',pr.last_live_send?.timestamp?date(pr.last_live_send.timestamp):'',pr.last_live_send?.timestamp?'good':'bad'],['Latest reply',pr.last_reply?.business_name||'None',pr.last_reply?.timestamp?date(pr.last_reply.timestamp):'',pr.last_reply?.timestamp?'good':'soft']];
      $('proof').innerHTML=cards.map(([l,v,n,t])=>`<div class="metric"><div><div class="value">${esc(v)}</div><div class="label">${esc(l)}</div></div><div class="status ${tone(t)}">${esc(t)}</div></div>`).join('');
    }
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    // Existing code...
    function renderDays(p){
      const rows=p.activity_series||[];if(!rows.length)return;
      const ctx = document.getElementById('activityChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: rows.map(i => shortDate(i.label)),
          datasets: [{
            label: 'Leads',
            data: rows.map(i => i.leads),
            borderColor: '#10b981',
            fill: false
          }, {
            label: 'Sent',
            data: rows.map(i => i.sent),
            borderColor: '#3b82f6',
            fill: false
          }, {
            label: 'Replies',
            data: rows.map(i => i.replies),
            borderColor: '#f59e0b',
            fill: false
          }, {
            label: 'Conversions',
            data: rows.map(i => i.conversions),
            borderColor: '#ef4444',
            fill: false
          }]
        },
        options: {
          responsive: true,
          scales: { y: { beginAtZero: true } }
        }
      });
    }

    function renderFunnel(p){
      const rows=p.outreach_funnel||[];if(!rows.length){$('funnel').innerHTML='<div class="empty">No funnel data is available yet.</div>';$('funnelNote').textContent='No funnel summary available.';return}
      const base=Math.max(1,Number(rows[0].count||0));$('funnelNote').textContent=`${num(rows.at(-1).count||0)} final conversion stage event(s) are stored out of ${num(base)} lead(s).`;
      $('funnel').innerHTML=`<div class="bars">${rows.map((i,idx)=>{const prev=idx===0?base:Number(rows[idx-1].count||0),w=Math.max(6,(Number(i.count||0)/base)*100),step=prev?`${((Number(i.count||0)/prev)*100).toFixed(1)}% of previous`:'starting point';return`<div class="funnelrow"><strong>${esc(i.label)}</strong><div class="track"><div class="fill" style="width:${w}%"></div></div><div style="text-align:right"><div><strong>${esc(num(i.count||0))}</strong></div><div class="muted">${esc(step)}</div></div></div>`}).join('')}</div>`;
    }

    function barList(rows,mode,title){
      if(!rows.length)return`<article class="mini"><div class="sec" style="margin-bottom:12px"><div><p>${esc(title)}</p><h2>No data yet</h2></div></div><div class="empty">This part of the dashboard will populate after more activity is stored.</div></article>`;
      const max=Math.max(1,...rows.map(r=>Number(mode==='count'?r.count:r.sent)||0));
      // Add pie chart for niches
      let chartHtml = '';
      if(title === 'Top niches' && rows.length > 0){
        chartHtml = `<canvas id="nicheChart" width="200" height="200"></canvas>`;
        setTimeout(() => {
          const ctx = document.getElementById('nicheChart').getContext('2d');
          new Chart(ctx, {
            type: 'pie',
            data: {
              labels: rows.map(r => r.label),
              datasets: [{
                data: rows.map(r => r.count),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
              }]
            }
          });
        }, 100);
      }
      return`<article class="mini"><div class="sec" style="margin-bottom:12px"><div><p>${esc(title)}</p><h2>${esc(title)}</h2></div></div>${chartHtml}<div class="bars">${rows.map(r=>{const primary=Number(mode==='count'?r.count:r.sent)||0,extra=mode==='count'?'':`<div class="muted">Reply ${pct(r.reply_rate)} · Convert ${pct(r.conversion_rate)}</div>`;return`<div class="barrow"><strong>${esc(r.label||'Unknown')}</strong><div><div class="track"><div class="fill" style="width:${Math.max(6,(primary/max)*100)}%"></div></div>${extra}</div><div style="text-align:right"><strong>${esc(num(primary))}</strong></div></div>`}).join('')}</div></article>`
    }
    function renderPipeline(p){const pipe=p.pipeline||{},dist=p.distributions||{};$('pipeline').innerHTML=`${barList(pipe.statuses||[],'count','Statuses')}${barList(pipe.stages||[],'count','Sequence stages')}${barList(dist.cities||[],'count','Top cities')}${barList(dist.niches||[],'count','Top niches')}`}
    function renderAttribution(p){const a=p.attribution||{};$('attribution').innerHTML=`${barList(a.personas||[],'rate','Winning personas')}${barList(a.hooks||[],'rate','Winning hooks')}<article class="mini"><div class="sec" style="margin-bottom:12px"><div><p>Conversion Rates</p><h2>By Niche</h2></div></div><canvas id="conversionChart" width="300" height="200"></canvas></article>`; setTimeout(() => { const ctx = document.getElementById('conversionChart').getContext('2d'); const niches = a.hooks || []; new Chart(ctx, { type: 'bar', data: { labels: niches.map(n => n.label), datasets: [{ label: 'Conversion Rate (%)', data: niches.map(n => (n.conversion_rate || 0) * 100), backgroundColor: '#4ade80' }] }, options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } } }); }, 100);}

    function renderControls(p){
      const a=p.automation||{},rt=p.runtime||{},interval=Math.max(60,Number(a.loop_interval_seconds||900)),tail=(a.output_tail||[]).slice(-12);
      $('controls').innerHTML=`<div class="stack"><div class="grid2"><div class="detail"><div class="label">Runner status</div><strong>${esc(a.status||'unknown')}</strong></div><div class="detail"><div class="label">Next run</div><strong>${esc(date(a.next_run_at))}</strong></div><div class="detail"><div class="label">Last run</div><strong>${esc(date(a.last_run_finished_at||a.last_run_started_at))}</strong></div><div class="detail"><div class="label">Last send delta</div><strong>${esc(num(a.last_run_emails_sent||0))}</strong></div></div><div class="controls"><button class="btn primary" id="runNowControl" type="button">Run now</button><button class="btn ghost" id="pauseControl" type="button">Pause auto</button><button class="btn ghost" id="resumeControl" type="button">Resume auto</button></div><div class="controls"><input class="field" id="intervalInput" type="number" min="60" step="60" value="${esc(interval)}"><button class="btn ghost" id="intervalBtn" type="button">Update interval</button></div><div class="detail"><div class="label">Runner note</div><strong>${esc(a.message||'No runner note.')}</strong>${a.last_error?`<div class="muted" style="margin-top:8px;color:var(--bad)">${esc(a.last_error)}</div>`:''}</div><div class="detail"><div class="label">Command</div><div class="code">${esc((a.command||[]).join(' ')||'Command unavailable')}</div></div><div class="detail"><div class="label">Runtime note</div><div class="muted">${esc(rt.execution_note||'')}</div></div><div class="detail"><div class="label">Latest output tail</div><div class="log">${esc(tail.length?tail.join('\\n'):'No bot output captured yet.')}</div></div></div>`;
      $('runNowControl').addEventListener('click',queueRun);$('pauseControl').addEventListener('click',()=>control('/api/bot/pause'));$('resumeControl').addEventListener('click',()=>control('/api/bot/resume'));$('intervalBtn').addEventListener('click',()=>control(`/api/bot/interval/${Math.max(60,Number($('intervalInput').value||interval))}`));
    }

    function renderDiag(p){
      const d=p.deployment_diagnostics||{},rt=p.runtime||{},items=[['Live send ready',d.live_send_ready?'Yes':'No',d.live_send_ready?'The main delivery conditions are satisfied.':'One or more conditions still prevent confident live sending.',d.live_send_ready?'good':'warn'],['Dry run mode',d.dry_run?'Enabled':'Off',d.dry_run?'The bot can generate outreach but will not send real emails.':'Live sending is allowed if the other checks also pass.',d.dry_run?'bad':'good'],['SMTP',d.smtp_ready?'Configured':'Missing',d.smtp_ready?'A sending account is available.':'Without SMTP credentials, zero real emails will go out.',d.smtp_ready?'good':'bad'],['Email window',d.email_window_open===false?'Closed':d.email_window_open===true?'Open':'Unknown',`Configured window: ${rt.email_window?.start||'--'} - ${rt.email_window?.end||'--'}.`,d.email_window_open===false?'warn':d.email_window_open===true?'good':'soft'],['Lead contact coverage',`${num(d.lead_contacts||0)} / ${num(d.total_leads||0)}`,'Live outreach only scales after leads have direct contacts.',Number(d.lead_contacts||0)>0?'good':'warn'],['Database storage',d.database_persistent?'Persistent':'Ephemeral',d.database_path||'No database path stored.',d.database_persistent?'good':'warn'],['Copy generation',d.optional_warnings&&d.optional_warnings.length?'Fallback templates':'LLM-ready',d.optional_warnings&&d.optional_warnings.length?'Missing LLM keys lowers copy quality, but should not block sending now.':'The app can use configured LLMs for stronger personalization.',d.optional_warnings&&d.optional_warnings.length?'warn':'good']],issues=[...(d.blocking_issues||[]),...(d.attention_issues||[])];
      $('diag').innerHTML=`<div class="stack">${items.map(([l,v,n,t])=>`<div class="card"><div class="label">${esc(l)}</div><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-top:10px"><strong>${esc(v)}</strong><span class="pill ${pill(t)}">${esc(t==='bad'?'Blocker':t==='warn'?'Watch':t==='good'?'Good':'Info')}</span></div><div class="note">${esc(n)}</div></div>`).join('')}<div class="detail"><div class="label">Current blockers and watch items</div>${issues.length?`<div class="stack">${issues.map(x=>`<div class="notice ${d.blocking_issues&&d.blocking_issues.includes(x)?'tone-bad':'tone-warn'}">${esc(x)}</div>`).join('')}</div>`:'<div class="empty">No active blockers are being surfaced right now.</div>'}</div></div>`;
    }

    function renderNotices(p){
      const items=[...(p.warnings||[]).map(i=>({...i,source:'warning'})),...(p.notifications||[]).map(i=>({...i,source:'notification'}))];
      $('notices').innerHTML=items.length?`<div class="notices">${items.map(i=>`<article class="notice tone-${tone(i.level)}"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start"><strong>${esc(i.title||i.source||'Notice')}</strong><span class="pill ${pill(i.level)}">${esc(i.source||'notice')}</span></div><div class="muted" style="margin-top:8px">${esc(i.message||'')}</div>${i.timestamp?`<div class="muted" style="margin-top:8px">${esc(date(i.timestamp))} · ${esc(rel(i.timestamp))}</div>`:''}</article>`).join('')}</div>`:'<div class="empty">No warnings or notifications yet.</div>';
    }

    function renderRuns(p){
      const rows=p.automation?.recent_runs||[];
      $('runs').innerHTML=rows.length?`<div class="runs">${rows.map(r=>`<article class="run"><div class="tags"><span class="pill ${pill(r.status)}">${esc(r.status||'unknown')}</span><span class="pill soft">${esc(r.trigger||'scheduled')}</span><span class="pill soft">${esc(uptime(r.duration_seconds||0))}</span></div><div style="margin-top:12px"><strong>${esc(num(r.emails_sent||0))} email(s) sent</strong></div><div class="muted" style="margin-top:8px">Started ${esc(date(r.started_at))} and finished ${esc(date(r.finished_at))}.</div>${r.error?`<div class="notice tone-bad" style="margin-top:12px">${esc(r.error)}</div>`:''}${(r.output_tail||[]).length?`<div class="log" style="margin-top:12px">${esc((r.output_tail||[]).join('\\n'))}</div>`:''}</article>`).join('')}</div>`:'<div class="empty">Run history will appear after the bot completes a session.</div>';
    }

    function renderExamples(p){
      const rows=p.training_examples||[];
      $('examples').innerHTML=rows.length?`<div class="examples">${rows.map(i=>`<article class="example"><div class="tags"><span class="pill ${pill(i.outcome_type)}">${esc(i.outcome_type||'example')}</span><span class="pill soft">${esc(i.persona||'persona unknown')}</span></div><div style="margin-top:12px"><strong>${esc(i.subject||'Untitled example')}</strong></div><div class="muted" style="margin-top:8px">${esc(i.body_preview||'No preview stored.')}</div></article>`).join('')}</div>`:'<div class="empty">Examples will appear once the bot has stored successful outreach patterns.</div>';
    }
    function renderEvents(p){
      const rows=(p.recent_events||[]).filter(eventMatch);
      $('events').innerHTML=rows.length?rows.map(i=>`<tr class="click ${state.leadId===i.lead_id?'active':''}" data-lead-id="${esc(i.lead_id||'')}"><td><div>${esc(date(i.timestamp))}</div><div class="muted">${esc(rel(i.timestamp))}</div></td><td><span class="pill ${pill(i.event_type)}">${esc((i.event_type||'').replaceAll('_',' '))}</span></td><td><div><strong>${esc(i.business_name||'Unknown lead')}</strong></div><div class="muted">${esc(first(i.city,'Unknown city'))} · ${esc(first(i.niche,'Unknown niche'))}</div></td><td>${esc(i.summary||'')}</td></tr>`).join(''):'<tr><td colspan="4" class="empty">No events match the current filters.</td></tr>';
    }
    function renderFollowups(p){
      const rows=(p.due_followups||[]).filter(leadMatch);
      $('followups').innerHTML=rows.length?rows.map(l=>`<tr class="click ${state.leadId===l.id?'active':''}" data-lead-id="${esc(l.id)}"><td><div><strong>${esc(l.business_name||'Unnamed lead')}</strong></div><div class="muted">${esc(first(l.niche,'Unknown niche'))} · ${esc(first(l.city,'Unknown city'))}</div></td><td><span class="pill ${pill(l.status)}">${esc(l.status||'new')}</span></td><td>${esc(contact(l))}</td><td><div>${esc(date(l.next_action_due))}</div><div class="muted">${esc(rel(l.next_action_due))}</div></td></tr>`).join(''):'<tr><td colspan="4" class="empty">No follow-ups match the current filters.</td></tr>';
    }
    function renderLeads(p){
      const rows=merge(p).filter(leadMatch);
      $('leads').innerHTML=rows.length?rows.map(l=>`<tr class="click ${state.leadId===l.id?'active':''}" data-lead-id="${esc(l.id)}"><td><div><strong>${esc(l.business_name||'Unnamed lead')}</strong></div><div class="muted">${esc(first(l.sequence_stage,'initial'))} sequence</div></td><td><span class="pill ${pill(l.status)}">${esc(l.status||'new')}</span></td><td>${esc(first(l.city,'Unknown city'))}<div class="muted">${esc(first(l.niche,'Unknown niche'))}</div></td><td>${esc(contact(l))}</td><td><div>${esc(date(l.updated_at))}</div><div class="muted">${esc(rel(l.updated_at))}</div></td></tr>`).join(''):'<tr><td colspan="5" class="empty">No leads match the current filters.</td></tr>';
    }

    function renderDetail(d){
      if(!d||!d.lead){$('detail').innerHTML='<div class="empty">Select a lead to inspect its history, draft context, and recent outcomes.</div>';return}
      const l=d.lead,issues=(l.audit_issues||[]).length?(l.audit_issues||[]).map(x=>`<span class="pill warn">${esc(x)}</span>`).join(''):'<span class="muted">No audit issues stored.</span>',services=(l.services||[]).length?(l.services||[]).map(x=>`<span class="pill soft">${esc(x)}</span>`).join(''):'<span class="muted">No services stored.</span>',personas=(d.recent_personas||[]).length?(d.recent_personas||[]).map(x=>`<span class="pill info">${esc(x)}</span>`).join(''):'<span class="muted">No persona history stored.</span>',outs=(d.recent_outcomes||[]).length?d.recent_outcomes.slice(0,6).map(i=>`<div class="timeline-item"><div class="tags"><span class="pill ${pill(i.type)}">${esc((i.type||'').replaceAll('_',' '))}</span><span class="muted">${esc(rel(i.timestamp))}</span></div><div style="margin-top:8px">${esc(i.summary||'')}</div></div>`).join(''):'<div class="empty">No recent outcomes recorded for this lead.</div>',timeline=(d.timeline||[]).length?d.timeline.slice(-10).reverse().map(i=>`<div class="timeline-item"><div class="tags"><span class="pill ${pill(i.event)}">${esc((i.event||'').replaceAll('_',' '))}</span><span class="muted">${esc(date(i.timestamp))}</span></div><div style="margin-top:8px">${esc(i.summary||'')}</div></div>`).join(''):'<div class="empty">No event timeline stored for this lead yet.</div>';
      $('detail').innerHTML=`<div class="stack"><div class="tags"><span class="pill ${pill(l.status)}">${esc(l.status||'new')}</span>${l.high_value?'<span class="pill good">High value</span>':''}${l.blacklisted?'<span class="pill bad">Blacklisted</span>':''}</div><div><h2 style="margin:0 0 6px">${esc(l.business_name||'Unnamed lead')}</h2><div class="muted">${esc(first(l.niche,'Unknown niche'))} in ${esc(first(l.city,'Unknown city'))}</div></div><div class="grid2"><div class="detail"><div class="label">Primary email</div><strong>${esc(first(l.email,'None found'))}</strong></div><div class="detail"><div class="label">Phone</div><strong>${esc(first(l.phone,'None found'))}</strong></div><div class="detail"><div class="label">Next action due</div><strong>${esc(date(l.next_action_due))}</strong></div><div class="detail"><div class="label">Lead score</div><strong>${esc(Number.isFinite(Number(l.lead_score??l.opportunity_score))?Number(l.lead_score??l.opportunity_score).toFixed(Number(l.lead_score??l.opportunity_score)%1===0?0:1):'--')}</strong></div></div><div class="detail"><div class="label">Strategy</div><strong>${esc(first(l.strategy,'No strategy stored yet.'))}</strong><div class="tags" style="margin-top:10px">${issues}</div></div><div class="detail"><div class="label">Signals</div><div class="tags">${services}</div><div class="muted" style="margin-top:10px">${esc(first(l.local_market_signal,'No local market signal stored.'))}</div></div><div class="detail"><div class="label">Recent personas</div><div class="tags">${personas}</div></div><div class="detail"><div class="label">Last generated email</div><strong>${esc(first(d.last_generated_email?.subject,'No generated email stored yet.'))}</strong><div class="muted" style="white-space:pre-wrap;margin-top:10px">${esc(first(d.last_generated_email?.body_preview,'No body preview stored yet.'))}</div></div>${d.last_prompt_payload?`<div class="detail"><div class="label">Latest prompt payload</div><div class="code">${esc(d.last_prompt_payload)}</div></div>`:''}<div class="detail"><div class="label">Recent outcomes</div><div class="timeline">${outs}</div></div><div class="detail"><div class="label">Timeline</div><div class="timeline">${timeline}</div></div></div>`;
    }

    async function control(url){try{await post(url);await load()}catch(e){$('notices').innerHTML=`<div class="error">Control action failed: ${esc(e.message)}</div>`}}
    async function queueRun(){const a=$('runBtn'),b=$('runNowControl');if(a){a.disabled=true;a.textContent='Queueing...'}if(b){b.disabled=true;b.textContent='Queueing...'}try{await post('/api/bot/run-now');await load()}catch(e){$('notices').innerHTML=`<div class="error">Failed to queue bot run: ${esc(e.message)}</div>`}finally{if(a){a.disabled=false;a.textContent='Run bot now'}if(b){b.disabled=false;b.textContent='Run now'}}}
    async function loadDetail(id,scroll=false){if(!id)return;state.leadId=Number(id);try{renderDetail(await get(`/api/dashboard/leads/${state.leadId}`));renderEvents(state.payload||{recent_events:[]});renderFollowups(state.payload||{due_followups:[]});renderLeads(state.payload||{lead_feed:[]});if(scroll)$('detail').scrollIntoView({behavior:'smooth',block:'start'})}catch(e){$('detail').innerHTML=`<div class="error">Failed to load lead detail: ${esc(e.message)}</div>`}}
    function rerender(){if(!state.payload)return;const ve=(state.payload.recent_events||[]).filter(eventMatch).length,vl=merge(state.payload).filter(leadMatch).length,vf=(state.payload.due_followups||[]).filter(leadMatch).length;$('filterSummary').textContent=`${vl} lead(s), ${vf} due follow-up(s), and ${ve} event(s) match the current filters.`;renderEvents(state.payload);renderFollowups(state.payload);renderLeads(state.payload)}
    async function load(){const b=$('refreshBtn');if(b){b.disabled=true;b.textContent='🔄 Refreshing...'}try{const p=await get('/api/dashboard');state.payload=p;renderFilters(p);renderMetrics(p);renderProof(p);renderDays(p);renderFunnel(p);renderPipeline(p);renderAttribution(p);renderControls(p);renderDiag(p);renderNotices(p);renderRuns(p);renderExamples(p);rerender();if(!state.leadId){const firstLead=(p.due_followups&&p.due_followups[0])||(p.lead_feed&&p.lead_feed[0])||(p.recent_leads&&p.recent_leads[0]);if(firstLead&&firstLead.id)state.leadId=firstLead.id}state.leadId?await loadDetail(state.leadId,false):renderDetail(null)}catch(e){console.error(e)}finally{if(b){b.disabled=false;b.textContent='🔄 Refresh'}}}
    document.addEventListener('click',e=>{const row=e.target.closest('[data-lead-id]');if(!row)return;const id=row.getAttribute('data-lead-id');if(id)loadDetail(id,true)});
    $('refreshBtn').addEventListener('click',load);$('runBtn').addEventListener('click',queueRun);$('exportLeadsBtn').addEventListener('click', exportLeads);$('exportEventsBtn').addEventListener('click', exportEvents);$('darkModeToggle').addEventListener('click', toggleDarkMode);load();window.setInterval(load,REFRESH);
  </script>
</body>
</html>
'''

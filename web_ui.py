from html import escape


def render_homepage(status):
    service_name = escape(str(status.get("service", "website-sales-agent")))
    service_state = escape(str(status.get("status", "unknown"))).title()
    running = "Online" if status.get("running", True) else "Offline"

    daily_actions = status.get("daily_actions")
    daily_actions_label = str(daily_actions) if daily_actions is not None else "Unavailable"

    error = status.get("error")
    error_block = ""
    if error:
        error_block = f"""
        <section class="panel panel-alert">
          <h2>Startup Note</h2>
          <p>{escape(str(error))}</p>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Website Sales Agent</title>
    <style>
      :root {{
        --bg: #f7f1e8;
        --bg-accent: #fffaf2;
        --ink: #1f2937;
        --muted: #5b6473;
        --panel: rgba(255, 255, 255, 0.86);
        --panel-border: rgba(31, 41, 55, 0.08);
        --accent: #0f766e;
        --accent-strong: #115e59;
        --warm: #d97706;
        --alert-bg: #fff4e5;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI", "Trebuchet MS", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(217, 119, 6, 0.12), transparent 32%),
          radial-gradient(circle at top right, rgba(15, 118, 110, 0.16), transparent 28%),
          linear-gradient(180deg, var(--bg-accent) 0%, var(--bg) 100%);
      }}

      .shell {{
        width: min(1080px, calc(100% - 32px));
        margin: 0 auto;
        padding: 40px 0 56px;
      }}

      .hero {{
        padding: 28px;
        border-radius: 28px;
        background: linear-gradient(140deg, rgba(17, 94, 89, 0.96), rgba(31, 41, 55, 0.94));
        color: #f8fafc;
        box-shadow: 0 22px 50px rgba(15, 23, 42, 0.18);
      }}

      .eyebrow {{
        display: inline-block;
        margin-bottom: 14px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.12);
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 12px;
      }}

      h1 {{
        margin: 0 0 12px;
        font-size: clamp(34px, 6vw, 56px);
        line-height: 1.02;
      }}

      .hero p {{
        margin: 0;
        max-width: 700px;
        color: rgba(248, 250, 252, 0.82);
        font-size: 18px;
        line-height: 1.6;
      }}

      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin-top: 24px;
      }}

      .panel {{
        padding: 22px;
        border: 1px solid var(--panel-border);
        border-radius: 22px;
        background: var(--panel);
        backdrop-filter: blur(6px);
        box-shadow: 0 18px 38px rgba(15, 23, 42, 0.08);
      }}

      .panel h2 {{
        margin: 0 0 10px;
        font-size: 15px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }}

      .metric {{
        font-size: clamp(28px, 4vw, 40px);
        font-weight: 700;
        line-height: 1.1;
      }}

      .subtle {{
        margin-top: 8px;
        color: var(--muted);
        line-height: 1.6;
      }}

      .panel-alert {{
        margin-top: 18px;
        background: var(--alert-bg);
      }}

      .links {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 16px;
      }}

      .links a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 120px;
        padding: 12px 16px;
        border-radius: 999px;
        color: #f8fafc;
        background: var(--accent);
        text-decoration: none;
        font-weight: 600;
        transition: transform 0.15s ease, background 0.15s ease;
      }}

      .links a.alt {{
        color: var(--accent-strong);
        background: rgba(15, 118, 110, 0.1);
      }}

      .links a:hover {{
        transform: translateY(-1px);
        background: var(--accent-strong);
      }}

      .links a.alt:hover {{
        background: rgba(15, 118, 110, 0.18);
      }}

      .footer {{
        margin-top: 18px;
        color: var(--muted);
        font-size: 14px;
      }}
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <span class="eyebrow">Live Deployment</span>
        <h1>{service_name}</h1>
        <p>
          This deployment is up and responding. The web app now serves a browser-friendly
          homepage at the root URL while keeping health and status endpoints available
          for Render and monitoring tools.
        </p>
        <div class="links">
          <a href="/status">View Runtime Status</a>
          <a class="alt" href="/health">Open Health Check</a>
        </div>
      </section>

      <section class="grid">
        <article class="panel">
          <h2>Service Status</h2>
          <div class="metric">{service_state}</div>
          <div class="subtle">The API process is responding to incoming requests.</div>
        </article>

        <article class="panel">
          <h2>Web App</h2>
          <div class="metric">{running}</div>
          <div class="subtle">The FastAPI server is bound for browser traffic on Render.</div>
        </article>

        <article class="panel">
          <h2>Daily Actions</h2>
          <div class="metric">{escape(daily_actions_label)}</div>
          <div class="subtle">This reflects the current action count reported by the app.</div>
        </article>
      </section>

      {error_block}

      <section class="panel" style="margin-top: 18px;">
        <h2>Available Endpoints</h2>
        <p class="subtle">
          Use <strong>/health</strong> for simple uptime checks, <strong>/status</strong> for runtime details,
          and <strong>/ws/logs</strong> for websocket log streaming.
        </p>
        <p class="footer">
          If you want a fuller product UI next, we can add forms, lead dashboards, and outreach controls on top of this deploy.
        </p>
      </section>
    </main>
  </body>
</html>
"""

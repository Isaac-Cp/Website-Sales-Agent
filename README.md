# Sales Agent Dashboard

## Deployment

To deploy this application, ensure the following environment variables are set:

- `DATABASE_URL`: Connection string for PostgreSQL database (e.g., `postgresql://user:pass@host:port/db`). If not set, it falls back to SQLite, but data will be lost on restarts in cloud environments.

- Other required env vars: SMTP_EMAIL, SMTP_PASSWORD, etc.

For persistent data, use a managed PostgreSQL service like Neon, Supabase, or Railway.

## Running Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`
3. Run: `python main.py --web`

## Dashboard Features

- Real-time metrics
- Lead management
- Email campaign tracking
- Dark mode support
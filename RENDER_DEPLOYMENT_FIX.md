# Why Emails Aren't Sending on Render Free Tier

## Problem Summary

The code is storing data in Render but falling back to **DRY_RUN mode** (preview-only), preventing actual email sends. There are three root causes:

### 1. **SMTP Validation Timeout**
Render free tier (256MB RAM, 0.1 CPU) is too slow to:
- Establish SMTP connections within timeout windows
- Validate email credentials at startup
- Complete SMTP connection pool tests

**Result**: SMTP validation fails → DRY_RUN mode enabled

### 2. **Resource Starvation**
- Browser operations (Selenium) can't complete with 256MB RAM and 0.1 CPU
- Network operations timeout
- Bot process crashes or never fully initializes
- Automatic fallback to DRY_RUN

### 3. **Non-Persistent Storage**
- SQLite data is stored but lost on every container restart
- Free tier cycles containers frequently
- Dashboard shows data existing, but it's not actually persisting

## How to Fix This

### Option A: Upgrade Render Plan (Recommended)
Switch to **Render's Standard Plan**:
- **2GB RAM** (8x more) - enough for browser + SMTP pool
- **2 CPU cores** (20x more) - operations complete quickly
- **100GB Persistent Disk** - data survives restarts
- **Monthly cost**: ~$12-15 USD

**Steps**:
```bash
1. Settings → Plan → Upgrade to Standard
2. Add persistent disk mount at /data
3. Set DATABASE_URL to PostgreSQL on Render (free tier available)
4. Keep existing code unchanged
```

### Option B: Reduce Resource Consumption (Free Tier Only)
If staying on free tier, optimize code:
```python
# In config.py - Reduce concurrent operations
PARALLEL_WORKERS = 2  # Was 6 (reduces memory)
SESSION_QUERIES = 5   # Was 20 (faster cycles)
SMTP_TIMEOUT = 5      # Was 12 (faster detection of issues)

# Skip browser operations
BATCH_SIZE = 1        # Send emails immediately instead of buffering
```

### Option C: Use Hobby-tier PostgreSQL + Render Standard
```
DATABASE_URL=postgresql://[user]:[pass]@[host]/[db]
DB_FILE=/dev/null  # Disable SQLite fallback
```

## Environment Variables for Paid Tier

Once on paid tier, set these in Render:

```
# Database (persistent)
DATABASE_URL=postgresql://user:pass@neon.tech/mydb

# Required for email sending
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Recommended
DRY_RUN=false
BOT_AUTOSTART=true
MAX_DAILY_ACTIONS=100  # Start conservatively
```

## Monitoring the Fix

After upgrading, check the dashboard:
- ✅ **Deployment Diagnostics** → "live_send_ready: true"
- ✅ **Database** → "Persistent: Yes"
- ✅ **SMTP** → "Configured: X accounts"
- ✅ **Bot runs** should show emails_sent > 0

## Testing Locally Before Uploading

```bash
# Test SMTP connection locally
python -c "
import config
from mailer import build_smtp_pool
accounts = config.get_smtp_accounts()
pool = build_smtp_pool(accounts)
print('SMTP pool ready:', pool.mailers)
"

# Run a test bot cycle
python main.py --dry-run --query 'Plumber near Chicago, IL' --limit 3

# Check dashboard
python main.py --serve  # Then visit http://localhost:8000
```

## Cost Analysis

**Free tier (current)**: $0/month
- ❌ Emails not sending (DRY_RUN fallback)
- ❌ Data lost on restarts

**Standard tier**: $12/month
- ✅ Emails send reliably
- ✅ 2GB RAM + 2 CPU cores
- ✅ 100GB persistent disk
- ✅ Production-ready

**With PostgreSQL addon**: +$7/month
- ✅ Scales to millions of leads
- ✅ No more data loss
- ✅ Full redundancy

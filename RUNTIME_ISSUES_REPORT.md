# Runtime Issues & Deployment Analysis Report

**Generated:** April 8, 2026  
**Last Run Status:** PARTIAL SUCCESS (3/10 emails sent)

---

## 🔴 CRITICAL ISSUES

### 1. **Email Validation Rejection**
- **Issue:** `contact@robertandsonselectricalsydney.com` marked as INVALID (score=30)
- **Root Cause:** Email validation is too strict, failing legitimate addresses
- **Impact:** Valid leads are skipped, reducing email sends
- **Risk Level:** HIGH
- **Recommendation:** 
  - Review [validator.py](validator.py#L250-L300) scoring thresholds
  - Check if syntax validation is incorrectly flagging valid emails
  - Consider lowering score threshold or enabling `allow_risky=True` by default

---

## 🟡 WARNINGS & POTENTIAL FAILURES

### 2. **SMTP Account Authentication Failures**
**Non-Working Email Account:**
- `wave84@gmail.com` — **Authentication Failed** (535 Bad Credentials)

**Details:**
- Error occurred during 2nd email send attempt
- Account was marked as "bad" and rotated out
- System correctly fallback to `crimsonvibes45@gmail.com`

**Risk Level:** MEDIUM  
**Action Items:**
- [ ] Verify Gmail app-specific password is correct in .env
- [ ] Check if password contains special characters that need escaping
- [ ] Regenerate Gmail app password if older than 90 days
- [ ] Consider removing/replacing the account in rotation

**File:** [.env](.env) — Check `SMTP_ACCOUNTS` configuration  
**Code:** [mailer.py](mailer.py#L115-L125) — Auth error handling

---

### 3. **Email Quality Scoring Logic**
**Potential Problem:** Emails are being generated with low scores (Score=4)

**What Happens:**
- LLM generates email content
- Quality gate checks: `if score < 2: skip`
- **Current threshold is very permissive** (anything ≥2 passes)
- One email was rejected (score=30 from validator, not LLM)

**Risk Level:** MEDIUM  
**Issue:**  
- Quality threshold of 2 is essentially no gate
- LLM might generate poor quality content that isn't caught
- No visibility into why scores are so low

**Recommendation:**
- Increase threshold to 5+
- Add logging to track score distribution
- Review [llm_helper.py](llm_helper.py#L1700-L1750) score_email() function

---

### 4. **Error Handling Gaps in send_10_emails.py**

**Silent Failures:**
- LLM generation has broad exception handler (line 150):
  ```python
  except Exception as e:
      print(f"  [LLM] Generation failed: {e}. Using fallback template.")
  ```
  - This swallows all errors and uses fallback
  - Makes debugging harder if Groq API is down

- Email validation has no retry logic (line 189):
  ```python
  v_res = mailer.assess_email(email, smtp_probe=False, allow_risky=True, check_catch_all=False)
  ```
  - SMTP probe disabled (to avoid hangs, per comment)
  - This means validation is less thorough

**Risk Level:** MEDIUM-HIGH  
**Recommendation:**
- Add specific exception types (e.g., `except groq.APIError`)
- Log which accounts are being tested
- Consider re-enabling SMTP probe with timeout

---

## 🟢 ISSUES THAT ARE WORKING CORRECTLY

### ✅ SMTP Account Rotation
- System correctly rotates between 5 accounts
- Bad accounts are marked and excluded
- Fallback mechanism works properly

### ✅ SSL Bypass Configuration
- `.env` correctly has `SMTP_SSL_BYPASS_HOSTS=192.178.223.108`
- SSL errors from previous run are resolved
- Self-signed certificate no longer blocking connections

### ✅ Database Status Tracking
- Leads marked as "emailed" after sending
- Daily send count tracked correctly (25 limit working)
- Unsent lead filtering working ([send_10_emails.py](send_10_emails.py#L52-L65))

### ✅ Persona System
- 6 personas available and rotating properly
- No errors in persona selection

---

## 📊 NON-WORKING EMAILS (Last Run)

| # | Email | Business | Status | Reason |
|---|-------|----------|--------|--------|
| 1 | contact@robertandsonselectricalsydney.com | Robert & Sons Electrical | **SKIPPED** | INVALID (score=30) - syntax or domain check failed |

**Note:** This is the ONLY email that failed validation. 3 other emails sent successfully.

---

## 🚀 DEPLOYMENT CHECKLIST

### Before Production Deployment:

- [ ] **Fix:** Verify `wave84@gmail.com` credentials or remove from SMTP rotation
- [ ] **Review:** Email validation thresholds in [validator.py](validator.py#L250-L300)
- [ ] **Test:** Run quality scoring on sample emails to check score distribution
- [ ] **Check:** LLM API key (GROQ_API_KEY) has sufficient quota
- [ ] **Verify:** Database backup before large scraping/sending runs
- [ ] **Monitor:** Log quality scores and skip reasons for analysis
- [ ] **Configure:** Consider disabling `allow_risky=True` once validation is more reliable
- [ ] **Test:** SSL bypass works for all configured SMTP hosts

### Recommended Changes:

1. **validator.py** - Add debug logging for why emails are marked INVALID
2. **send_10_emails.py** - Increase LLM score threshold from 2 to 5
3. **llm_helper.py** - Review score_email() logic and thresholds
4. **.env** - Update/verify SMTP account credentials
5. **mailer.py** - Add account health monitoring/alerts

---

## 🔧 Code Issues to Fix

### Priority 1 (Critical):
```python
# In send_10_emails.py line 176-177
if score < 2:  # ← This is too permissive, should be >= 5
    print(f"  [QA] Email quality too low (score={score}). Skipping.")
```

### Priority 2 (High):
```python
# In validator.py line 79-80
if classification == "INVALID":  # ← Add logging why it's invalid
    # Need to trace root cause of email rejection
```

### Priority 3 (Medium):
```python
# In mailer.py - Add account health tracking
# Current: Accounts marked bad but no persistent state
# Need: JSON file or DB table tracking failed attempts
```

---

## 📈 Metrics from Last Run

- **Total Leads Processed:** 4
- **Emails Sent:** 3 / 10 (30% success rate)
- **Emails Rejected:** 1 (25% of attempts)
- **SMTP Accounts Used:** 3 (p2mise@gmail.com, crimsonvibes45@gmail.com, wave84-rotated)
- **SMTP Accounts Failed:** 1 (wave84@gmail.com - auth failure)
- **Database Status:**
  - Scraped: 104
  - Emailed: 32 (including today's 3)
  - Unsent/Available: 4 (depleted today)

---

## 🎯 Next Steps

1. **Immediate:** Investigate `contact@robertandsonselectricalsydney.com` validation failure
2. **Short-term:** Fix SMTP account credentials and re-run test
3. **Medium-term:** Increase email quality gate threshold and add logging
4. **Long-term:** Rebuild database with more leads before scaling sends

# Email Setup and Administration Guide

This guide covers configuring, troubleshooting, and recovering the CVW email system.
Normal user instructions are in the companion guide: [Using Email](../all/using_email.md).

---

## How Email Works

The app sends email via the **Mailgun HTTP API**. Mailgun acts as a relay —
email appears to come from `info@cvwdev.org` (or the production domain) and is
delivered through Mailgun's servers, bypassing port restrictions on the VPS.

Configuration lives in `/opt/cvwapp/.env` on the DigitalOcean server.

---

## Initial Setup (new domain or server)

### 1. Create a Mailgun account
Go to [mailgun.com](https://mailgun.com) and create a free account.
The free tier allows 1,000 emails/month.

### 2. Add and verify the domain
1. In Mailgun: **Sending → Domains → Add New Domain**
2. Enter the domain (e.g. `cvwdev.org` or `centralvawoodturners.org`)
3. Select region **US**
4. Use Mailgun's automated DNS setup if offered, or add records manually in Cloudflare:
   - Two TXT records (SPF and DKIM)
   - Two MX records: `mxa.mailgun.org` and `mxb.mailgun.org` (priority 10)
   - All records must be **DNS only** (grey cloud in Cloudflare, not proxied)
5. Click **Verify DNS Settings** in Mailgun — domain should show **Active**

### 3. Create a sending key
1. In Mailgun: **Sending → Domains → click the domain → Sending Keys**
2. Click **Add Sending Key**
3. Copy the generated key immediately — it is only shown once

### 4. Test the key from the server
SSH into the server and run (all one line):

```bash
curl -s --user 'api:YOUR_KEY' https://api.mailgun.net/v3/YOUR_DOMAIN/messages -F from='CVW <info@YOUR_DOMAIN>' -F to='your@email.com' -F subject='Test' -F text='Test from Mailgun'
```

A successful response looks like: `{"id": "<...>", "message": "Queued. Thank you."}`
A `Forbidden` response means the key is wrong or doesn't have sending permission.

### 5. Configure the app
SSH into the server:

```bash
ssh root@104.236.111.180
nano /opt/cvwapp/.env
```

Set these values:
```
MAILGUN_API_KEY=your-sending-key-here
MAILGUN_DOMAIN=cvwdev.org
MAILGUN_FROM=CVW <info@cvwdev.org>
```

Restart the app:
```bash
cd /opt/cvwapp
docker compose down && docker compose up -d
```

---

## Switching Domains (e.g. cvwdev.org → centralvawoodturners.org)

1. Add and verify the new domain in Mailgun (steps 2–3 above)
2. SSH into the server and update `.env`:
   ```bash
   nano /opt/cvwapp/.env
   ```
   Change `MAILGUN_DOMAIN` and `MAILGUN_FROM` to the new domain.
   Create a new sending key for the new domain and update `MAILGUN_API_KEY`.
3. Restart:
   ```bash
   cd /opt/cvwapp
   docker compose down && docker compose up -d
   ```

---

## Troubleshooting

### "Email not configured" error in the app
The `.env` file is missing `MAILGUN_API_KEY` or `MAILGUN_DOMAIN`, or the app
hasn't been restarted since they were added.

**Fix:** Check `.env`, then restart:
```bash
cd /opt/cvwapp && docker compose down && docker compose up -d
```

### Sends hang with no response
Usually means the app is trying SMTP instead of Mailgun (e.g. `MAILGUN_API_KEY`
is blank but `SMTP_HOST` is set), and port 587 is blocked by DigitalOcean.

**Fix:** Ensure `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` are set in `.env`.

### 403 Forbidden from Mailgun
The API key is wrong, expired, or doesn't have sending permission.

**Fix:**
1. Go to Mailgun: **Sending → Domains → your domain → Sending Keys**
2. Create a new key
3. Test with curl (see step 4 above)
4. Update `.env` and restart the app

### Email not arriving (but no error)
1. Check Mailgun logs: **Sending → Logs** — look for the message and its status
2. Check spam folder
3. Verify the recipient email address is correct in the member record

### Mailgun free tier limits
The free tier allows 1,000 emails/month. For a club this is typically sufficient.
Check usage in Mailgun: **Sending → Overview**.

---

## Viewing Email History in the App

Go to **Email → Log** in the dashboard to see all sends with recipient count,
subject, status, and any error details.

---

## All Commands Reference (run on server via SSH)

| Task | Command |
|------|---------|
| SSH into server | `ssh root@104.236.111.180` |
| Edit config | `nano /opt/cvwapp/.env` |
| Restart app | `cd /opt/cvwapp && docker compose down && docker compose up -d` |
| View app logs | `cd /opt/cvwapp && docker compose logs --tail=30` |
| Test Mailgun key | `curl -s --user 'api:KEY' https://api.mailgun.net/v3/DOMAIN/messages -F from='CVW <info@DOMAIN>' -F to='test@email.com' -F subject='Test' -F text='Test'` |

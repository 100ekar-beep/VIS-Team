# VIS Team App (Site Data / JMS / Team Request)

Login-protected Streamlit app for the field team. Login with mobile number +
password (stays logged in via a browser cookie until you Logout). Sites
allocated to you are matched automatically via `site_data."Team Name"`.

## Pages

1. **Login** (`app.py`)
2. **📍 Site Data** — all your sites in a searchable list (table or mobile
   card view). Click **"📂 Open Site"** on any site to open its full detail,
   with 3 tabs:
   - **📊 Site Status** — request a status change (Completed / HOLD / Other)
     + remark. This does **not** update Supabase directly — it goes to the
     admin's **Team Request** page for approval first.
   - **🧾 Create JMS** — load a template or add items, then generate and
     download the JMS PDF (never saved to Supabase).
   - **📸 Site Photos** — upload multiple photos, which are emailed straight
     from memory (never saved to Supabase or disk) to a fixed recipient.
3. **📊 Indus Site Data** — search the Indus/Escalation Matrix data, share
   site details via WhatsApp, and plan a multi-site route.
4. **✅ Team Request** *(admin only)* — approve or reject pending Site Status
   requests from the team. Approving updates `site_data."Site Status"`.

## Demo Mode

If Supabase secrets aren't set, the app runs in **demo mode** with sample
data — login: mobile `9999999999`, password `demo123` (this demo user is
also an admin, so you can try the Team Request page too).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Connecting real Supabase

1. Run `new_tables_schema.sql` in the Supabase SQL Editor. This:
   - Adds an `is_admin` column to your existing `app_users` table (doesn't
     touch existing rows/passwords).
   - Creates `site_status_requests` (pending Site Status change requests).
   - Creates `ground_template` / `ground_template_items` if not already there.
2. Make yourself an admin:
   ```sql
   update app_users set is_admin = true where mobile_number = 'your-mobile-number';
   ```
3. Add `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.example`):
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "your-key"

   EMAIL_SENDER = "youraddress@gmail.com"
   EMAIL_PASSWORD = "your-gmail-app-password"   # NOT your normal Gmail password
   EMAIL_RECEIVER = "recipient@example.com"
   ```
   For Gmail, create an **App Password** at
   Google Account → Security → 2-Step Verification → App Passwords — a normal
   password will not work for sending mail via SMTP.
4. Team member logins: send me (Claude) their Name / Mobile / User ID /
   Password and I'll generate the bcrypt hash + ready SQL insert for you.

## How Technician/FSE details are found

`utils/data.get_technician_fse_for_site()` looks up the site's Technician and
FSE detail from the **"Excalation Matrix"** table by matching Site ID (it
also tries a couple of likely column-name variants, same approach as the
Indus Site Data page).

## Files

```
app.py                              # Login page (cookie-based persistent login)
pages/1_Site_Data.py                # Site list + detail (Status/JMS/Photos tabs)
pages/2_Indus_Site_Data.py          # Indus search + WhatsApp share + route plan
pages/3_Team_Request.py             # Admin-only approval page
utils/supabase_client.py            # Supabase connection (demo-mode aware)
utils/auth.py                       # bcrypt login check
utils/data.py                       # All Supabase queries + demo data fallback
utils/guard.py                      # require_login() (with cookie auto-login)
utils/cookies.py                    # Shared browser cookie manager
utils/pdf_generator.py              # Plain, boxed JMS PDF builder (reportlab)
utils/email_sender.py               # In-memory photo -> email sender (SMTP)
new_tables_schema.sql               # SQL: is_admin column + new tables
generate_password_hash.py           # Run locally to create a new user's login
.streamlit/secrets.toml.example     # Rename & fill in for real Supabase + email
requirements.txt
```

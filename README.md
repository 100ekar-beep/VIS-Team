# JMS (Joint Measurement Sheet) App

Login-protected Streamlit app: team apna mobile number + password se login karti hai,
apni sites automatically dekhti hai (`site_data` ke **Team Name** column se match hoke —
koi manual allocation nahi karni padti), aur JMS PDF bana ke mobile pe download kar
sakti hai. **Kuch bhi Supabase mein wapas save nahi hota.**

## Pages

1. **Login** (`app.py`) — mobile number + password
2. **📍 My Sites** — jitni sites `site_data."Team Name"` = logged-in user ka `full_name`, sirf wahi dikhti hain
3. **📋 Create JMS** — popup form: site details upar, template load karo ya items
   manually add karo (+ item), qty/remarks edit karo, submit karke PDF download karo

## Demo Mode

Supabase secrets set nahi hai to app apne aap **demo mode** mein chalta hai — login:
mobile `9999999999`, password `demo123`.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Real Supabase se connect karna

1. **Naye tables banao** — `new_tables_schema.sql` Supabase SQL Editor mein run karo.
   Ye 3 tables banayega: `item_master`, `ground_template`, `ground_template_items`.
   (Koi allocation table nahi — site allocation `site_data."Team Name"` se hi hoti hai.)

2. **Item master fill karo** — `item_master` mein apne saare item codes + descriptions
   + units daalo.

3. **Templates banao** (optional) — `ground_template` + `ground_template_items` mein
   (examples SQL file ke comments mein hai).

4. **Team members ke login add karo** — `app_users` table abhi khali hai, isko is app
   ke liye use karo:
   - `generate_password_hash.py` apne computer pe chalao (`pip install bcrypt` phir
     `python generate_password_hash.py`) — ye har member ke liye bcrypt password hash
     + ready SQL insert statement generate kar dega.
   - **Zaroori:** `full_name` **exactly** wahi spelling honi chahiye jo `site_data`
     ke "Team Name" dropdown mein use hoti hai — warna us user ko apni sites nahi
     dikhengi.

5. **Secrets set karo** — `.streamlit/secrets.toml.example` ko `.streamlit/secrets.toml`
   rename karo aur apna Supabase URL + key daalo (ya Streamlit Cloud "Settings → Secrets"
   mein):
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "your-key"
   ```

Bas — secrets set hote hi app demo mode se nikal ke real Supabase data use karne lagega।

## Login kaise kaam karta hai

- `app_users.mobile_number` + `app_users.password_hash` (bcrypt) se login verify hota hai.
- Login ke baad `full_name` se `site_data` query hoti hai (`"Team Name" = full_name`)
  taaki sirf uski sites dikhein.

## PDF format

`utils/pdf_generator.py` aapke diye hue JMS_Format.pdf ke exact layout ko follow
karta hai — Circle/Date, TSP Partner/Site ID, Site Name/RL ID header, line items table
(S.No, Line Item, Unit, Qty as per site, Remarks), aur neeche signature block.

## Files

```
app.py                              # Login page
pages/1_📍_My_Sites.py             # Team Name se auto-matched sites
pages/2_📋_Create_JMS.py           # Template + item selection, PDF generation
utils/supabase_client.py            # Supabase connection (demo-mode aware)
utils/auth.py                       # bcrypt login check
utils/data.py                       # All Supabase queries + demo data fallback
utils/guard.py                      # require_login() helper for protected pages
utils/pdf_generator.py              # JMS PDF builder (reportlab)
generate_password_hash.py           # Run locally to create a new user's login
new_tables_schema.sql                # SQL for the 3 new Supabase tables
.streamlit/secrets.toml.example      # Rename & fill in for real Supabase
requirements.txt
```

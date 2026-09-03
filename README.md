# JMS (Joint Measurement Sheet) App

Login-protected Streamlit app. Team mobile number + password se login karti hai, aur
ek hi page (**JMS**) pe apni saari sites ek colorful table mein dikhti hai — har site
ke saamne **"🧾 Create JMS"** button hai. Click karte hi popup khulta hai jahan
template load karo ya items add karo, aur PDF turant download ho jaati hai.
**Kuch bhi Supabase mein wapas save nahi hota.**

## Pages

1. **Login** (`app.py`) — mobile number + password
2. **📋 JMS** — sabhi allocated sites (Team Name match se) ek table mein, har row mein
   "Create JMS" button jo popup kholta hai (template/item select → PDF download)

## Demo Mode

Supabase secrets set nahi hai to app apne aap **demo mode** mein chalta hai — login:
mobile `9999999999`, password `demo123`.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Real Supabase se connect karna

1. `new_tables_schema.sql` Supabase SQL Editor mein run karo (`app_users` naye sirre
   se banega — sirf 4 columns; plus `item_master`, `ground_template`,
   `ground_template_items`).
2. `item_master` mein apne items daalo.
3. `ground_template` + `ground_template_items` mein templates banao (optional).
4. Team member logins add karne ke liye mujhe (Claude) unki details do — main bcrypt
   hash + ready SQL bana dunga.
5. `.streamlit/secrets.toml.example` ko `.streamlit/secrets.toml` rename karke apna
   Supabase URL + key daalo (ya Streamlit Cloud "Settings → Secrets" mein).

## PDF format

`utils/pdf_generator.py` — colorful boxed design:
- Upar colored title bar (VISIONTECH INFRA SOLUTIONS)
- Bordered light-fill "Site Info" box: Circle, TSP Partner, Site ID, Site Name,
  **Project ID** (Date aur RL ID hata diye gaye hai)
- Colored-header items table (S.No, Line Item, Unit, Qty as per site, Remarks), zebra rows
- Neeche 4 colored signature boxes (Partner Supervisor / Audit Engineer / TSP Partner
  Name / Agency Name) — har box mein naam ke neeche khali "Signature" jagah

## Login kaise kaam karta hai

- `app_users.mobile_number` + `app_users.password` (bcrypt hash) se login verify hota hai.
- Login ke baad `team_name` se `site_data` query hoti hai (`"Team Name" = team_name`)
  taaki sirf uski sites dikhein.

## Files

```
app.py                              # Login page
pages/1_📋_JMS.py                  # Sites table + row-wise Create JMS (combined page)
utils/supabase_client.py            # Supabase connection (demo-mode aware, with debug info)
utils/auth.py                       # bcrypt login check
utils/data.py                       # All Supabase queries + demo data fallback
utils/guard.py                      # require_login() helper
utils/pdf_generator.py              # Colorful boxed JMS PDF builder (reportlab)
new_tables_schema.sql                # SQL for app_users + 3 new Supabase tables
.streamlit/secrets.toml.example      # Rename & fill in for real Supabase
requirements.txt
```

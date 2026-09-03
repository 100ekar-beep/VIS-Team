# JMS (Joint Measurement Sheet) App

Login-protected Streamlit app: team apna mobile number + password se login karti hai,
apni allocated sites dekhti hai, aur wahi se JMS PDF bana ke mobile pe download kar
sakti hai — **kuch bhi Supabase mein wapas save nahi hota** (sirf login/site/item/template
data padha jaata hai).

## Pages

1. **Login** (`app.py`) — mobile number + password
2. **📍 My Sites** — sirf allocated sites dikhti hain, ek site select karo
3. **📋 Create JMS** — popup form: site details upar, template load karo ya items
   manually add karo (+ item), qty/remarks edit karo, submit karke PDF download karo

## Abhi ke liye: Demo Mode

Supabase secrets set nahi hai to app apne aap **demo mode** mein chalta hai (sample data ke
saath) — login: mobile `9999999999`, password `demo123`. Isse UI test kar sakte ho bina
Supabase ke.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Real Supabase se connect karna

1. **Naye tables banao** — `new_tables_schema.sql` file Supabase SQL Editor mein run karo.
   Ye 4 tables banayega: `user_site_allocation`, `item_master`, `ground_template`,
   `ground_template_items`. (Aapke existing `app_users` aur `site_data` tables se link
   honge — koi change nahi hoga unmein.)

2. **Item master fill karo** — `item_master` table mein apne saare item codes +
   descriptions + units daalo.

3. **Templates banao** (optional) — `ground_template` mein "Battery Bank", "LA", etc.
   banao, aur `ground_template_items` mein unke line items daalo (examples SQL file
   ke comments mein hai).

4. **Site allocation karo** — `user_site_allocation` mein daalo ki kis user ko (uuid
   `app_users.id`) kaunsi site (uuid `site_data.id`) allocate hai.

5. **Secrets set karo** — `.streamlit/secrets.toml.example` ko `.streamlit/secrets.toml`
   rename karo aur apna Supabase URL + key daalo:
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "your-key"
   ```
   Streamlit Cloud pe deploy karte time ye same values "App settings → Secrets" mein
   daal do.

Bas — jaise hi secrets set honge, app automatically demo mode se nikal ke real Supabase
data use karne lagega. Koi code change nahi karna padega.

## Login kaise kaam karta hai

- `app_users` table ka `mobile_number` + `password_hash` (bcrypt) use hota hai.
- Login ke baad user ki `id` se `user_site_allocation` query hoti hai taaki sirf uski
  allocated sites dikhein.

## PDF format

`utils/pdf_generator.py` aapke diye hue **JMS_Format.pdf** ke exact layout ko follow
karta hai — Circle/Date, TSP Partner/Site ID, Site Name/RL ID header, line items table
(S.No, Line Item, Unit, Qty as per site, Remarks), aur neeche Partner Supervisor /
Audit Engineer / TSP Partner / Agency signature block.

## Files

```
app.py                              # Login page
pages/1_📍_My_Sites.py             # Allocated site picker
pages/2_📋_Create_JMS.py           # Template + item selection, PDF generation
utils/supabase_client.py            # Supabase connection (demo-mode aware)
utils/auth.py                       # bcrypt login check
utils/data.py                       # All Supabase queries + demo data fallback
utils/guard.py                      # require_login() helper for protected pages
utils/pdf_generator.py              # JMS PDF builder (reportlab)
new_tables_schema.sql                # SQL for the 4 new Supabase tables
.streamlit/secrets.toml.example      # Rename & fill in for real Supabase
requirements.txt
```

-- =====================================================================
-- NEW TABLES FOR THE JMS APP
-- (Site allocation needs NO new table — it uses your existing
--  site_data."Team Name" column, matched against app_users.full_name.)
-- Run this in Supabase SQL Editor.
-- =====================================================================

-- 1. ITEM MASTER (item code + description + unit, shown in the JMS dropdown)
create table if not exists item_master (
    id                bigserial primary key,
    item_code         text unique not null,
    item_description  text not null,
    unit              text not null,          -- e.g. Meter, Each
    created_at        timestamptz default now()
);

-- 2. TEMPLATES (e.g. "Battery Bank", "LA", "Optional", "Sharing")
create table if not exists ground_template (
    id             bigserial primary key,
    template_name  text unique not null,
    created_at     timestamptz default now()
);

-- 3. TEMPLATE LINE ITEMS (which item codes + default qty belong to each template)
create table if not exists ground_template_items (
    id             bigserial primary key,
    template_id    bigint not null references ground_template(id) on delete cascade,
    item_code      text not null references item_master(item_code) on delete cascade,
    default_qty    numeric default 0,
    sort_order     int default 0
);

-- =====================================================================
-- ADDING TEAM MEMBER LOGINS (app_users table already exists, currently empty)
-- Don't insert plain-text passwords — use generate_password_hash.py locally
-- to get a bcrypt hash, then run:
--
-- insert into app_users (full_name, mobile_number, password_hash, is_admin, allowed_pages)
-- values ('Pramodkumar Jaju', '9999999999', '<bcrypt-hash-here>', false, '[]');
--
-- IMPORTANT: full_name must EXACTLY match the "Team Name" spelling used in
-- site_data, otherwise that user won't see their sites.
-- =====================================================================

-- EXAMPLE: create a template and add items to it
-- insert into ground_template (template_name) values ('Battery Bank') returning id;
-- insert into ground_template_items (template_id, item_code, default_qty, sort_order) values
--   (1, 'ITM-008', 1, 1),
--   (1, 'ITM-009', 1, 2);

-- =====================================================================
-- NOTE: JMS PDFs are generated on the client (mobile) and downloaded
-- directly — nothing about the generated PDF or its line items is ever
-- written back to Supabase.
-- =====================================================================

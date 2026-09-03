-- =====================================================================
-- NEW TABLES FOR THE JMS APP
-- Matches your existing tables:
--   app_users(id uuid, full_name, allowed_pages, is_admin, mobile_number, password_hash, ...)
--   site_data(id uuid, "Project ID", "Site ID", "Site Name", "Team Name", ...)
-- Run this in Supabase SQL Editor.
-- =====================================================================

-- 1. USER <-> SITE ALLOCATION (one user can have many sites)
create table if not exists user_site_allocation (
    id           bigserial primary key,
    user_id      uuid not null references app_users(id) on delete cascade,
    site_id      uuid not null references site_data(id) on delete cascade,
    created_at   timestamptz default now(),
    unique (user_id, site_id)
);

-- 2. ITEM MASTER (item code + description + unit, shown in the JMS dropdown)
create table if not exists item_master (
    id                bigserial primary key,
    item_code         text unique not null,
    item_description  text not null,
    unit              text not null,          -- e.g. Meter, Each
    created_at        timestamptz default now()
);

-- 3. TEMPLATES (e.g. "Battery Bank", "LA", "Optional", "Sharing")
create table if not exists ground_template (
    id             bigserial primary key,
    template_name  text unique not null,
    created_at     timestamptz default now()
);

-- 4. TEMPLATE LINE ITEMS (which item codes + default qty belong to each template)
create table if not exists ground_template_items (
    id             bigserial primary key,
    template_id    bigint not null references ground_template(id) on delete cascade,
    item_code      text not null references item_master(item_code) on delete cascade,
    default_qty    numeric default 0,
    sort_order     int default 0
);

-- =====================================================================
-- EXAMPLE: allocate a site to a user (replace with real ids)
-- insert into user_site_allocation (user_id, site_id) values
--   ('500c5002-70b2-4401-b901-7acec2b5bfec', '0063608d-faa7-4632-8b3e-09c5a768495a');
--
-- EXAMPLE: create a template and add items to it
-- insert into ground_template (template_name) values ('Battery Bank') returning id;
-- insert into ground_template_items (template_id, item_code, default_qty, sort_order) values
--   (1, 'ITM-008', 1, 1),
--   (1, 'ITM-009', 1, 2);
-- =====================================================================

-- NOTE: JMS PDFs are generated on the client (mobile) and downloaded
-- directly — nothing about the generated PDF or its line items is ever
-- written back to Supabase. Only login (app_users), site allocation
-- (user_site_allocation), item_master, and templates are read from DB.

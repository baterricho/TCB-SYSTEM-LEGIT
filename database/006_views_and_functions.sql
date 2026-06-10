-- 006_views_and_functions.sql
-- Optional helper functions and safe views for the current schema.
--
-- These objects do not replace Django model logic. Code generation for
-- application_code, case_number, listing_code, inquiry_code, and key_code
-- currently lives in Django model save() methods and is intentionally not
-- recreated here as active database logic.

-- Generic updated_at trigger helper.
-- This function is safe to create, but no triggers are installed by default
-- because Django currently manages updated_at fields through auto_now.
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Optional trigger example only. Do not enable unless Django model/migration
-- strategy is updated to expect database-managed updated_at values.
--
-- CREATE TRIGGER set_ip_application_updated_at
-- BEFORE UPDATE ON public.ip_application
-- FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Safe encryption key metadata view. This intentionally excludes
-- encrypted_key_material so reporting tools can inspect key metadata without
-- exposing raw encrypted material.
CREATE OR REPLACE VIEW public.encryption_key_metadata
WITH (security_invoker = true)
AS
SELECT
    key_id,
    key_code,
    key_name,
    algorithm,
    status,
    created_by_id,
    created_at,
    rotated_at,
    disabled_at,
    rotation_policy,
    is_primary,
    is_backup
FROM public.encryption_key;

-- Public marketplace view matching the published/active listing rule used by
-- the RLS policy.
CREATE OR REPLACE VIEW public.public_market_listings
WITH (security_invoker = true)
AS
SELECT
    listing_id,
    listing_code,
    record_id,
    title,
    ip_type,
    inventor_name,
    short_description,
    full_description,
    category,
    availability_status,
    image,
    status,
    is_active,
    created_at,
    updated_at
FROM public.market_listing
WHERE status = 'published'
  AND is_active = true;

-- Public announcements view matching the published announcement rule used by
-- the RLS policy.
CREATE OR REPLACE VIEW public.public_announcements
WITH (security_invoker = true)
AS
SELECT
    announcement_id,
    title,
    content,
    category,
    is_published,
    created_at,
    updated_at
FROM public.announcement
WHERE is_published = true;

-- Admin dashboard summary view. Access is still governed by underlying RLS
-- because the view is security_invoker.
CREATE OR REPLACE VIEW public.admin_case_status_summary
WITH (security_invoker = true)
AS
SELECT
    status,
    count(*)::bigint AS case_count
FROM public."case"
GROUP BY status;

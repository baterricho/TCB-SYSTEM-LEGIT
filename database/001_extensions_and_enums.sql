-- 001_extensions_and_enums.sql
-- PostgreSQL/Supabase enum reference objects for The Creator's Bulwark.
--
-- Source of truth:
-- - Django models in accounts, applications, cases, payments, marketplace,
--   inquiries, security_keys, ipophl_email, and related apps.
-- - Initial Django migrations in */migrations/0001_initial.py.
--
-- The current Django schema stores choice fields as varchar columns. These enum
-- types document the exact allowed values found in the Django models. The table
-- definitions in 002_tables.sql keep varchar columns to remain compatible with
-- Django migrations.
--
-- No PostgreSQL extension is required by the current models. Primary keys use
-- bigint identity columns, not UUID columns, and application/key/listing/case
-- codes are generated in Django with Python uuid helpers. pgcrypto is therefore
-- intentionally not enabled here.

DO $$
BEGIN
    CREATE TYPE public.user_role AS ENUM ('applicant', 'evaluator', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.user_status AS ENUM ('active', 'inactive', 'locked', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.otp_purpose AS ENUM ('login', 'registration', 'password_reset');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.applicant_type AS ENUM ('faculty', 'staff', 'student', 'external');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.evaluator_specialization AS ENUM (
        'patent_mechanical',
        'patent_electrical',
        'utility_model',
        'industrial_design',
        'trademark',
        'copyright'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.ip_type AS ENUM (
        'patent',
        'utility_model',
        'industrial_design',
        'trademark',
        'copyright'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.application_status AS ENUM ('draft', 'submitted', 'withdrawn');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.language_validation_status AS ENUM ('valid', 'warning', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.application_checklist_status AS ENUM (
        'complete',
        'missing',
        'needs_review',
        'optional'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.case_status AS ENUM (
        'pending',
        'under_review',
        'evaluated',
        'on_going',
        'certified',
        'archived'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.case_priority_label AS ENUM ('low', 'normal', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.activity_role_visibility AS ENUM ('applicant', 'admin', 'all');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.fee_assessment_status AS ENUM (
        'pending',
        'issued',
        'paid',
        'waived',
        'cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.payment_status AS ENUM ('pending', 'verified', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.market_listing_status AS ENUM ('draft', 'published', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.inquiry_status AS ENUM ('new', 'answered', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.encryption_key_status AS ENUM ('active', 'rotated', 'disabled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.key_activity_action AS ENUM (
        'generated',
        'rotated',
        'disabled',
        'escrow_report_generated'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE public.ipophl_email_parse_status AS ENUM ('matched', 'unmatched', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

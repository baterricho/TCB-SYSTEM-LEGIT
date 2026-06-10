-- full_schema.sql
-- Combined PostgreSQL/Supabase schema for The Creator's Bulwark.
-- Generated from database/001 through database/006.
-- Do not run this alongside Django migrations if it would create duplicate/conflicting tables.


-- ============================================================================
-- 001_extensions_and_enums.sql
-- ============================================================================

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

-- ============================================================================
-- 002_tables.sql
-- ============================================================================

-- 002_tables.sql
-- CREATE TABLE statements for the current Django database schema.
--
-- Notes:
-- - Primary keys follow the current project strategy: BigAutoField/bigint
--   identity for project models, AutoField/integer identity for relevant
--   Django contrib tables.
-- - Django model defaults such as auto_now_add, auto_now, and CharField
--   defaults are application-level defaults in the migrations. They are not
--   added as PostgreSQL column defaults here.
-- - Foreign keys, unique constraints, check constraints, and indexes are added
--   in 003_indexes_and_constraints.sql.

CREATE TABLE IF NOT EXISTS public.django_content_type (
    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    app_label varchar(100) NOT NULL,
    model varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_permission (
    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name varchar(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_group (
    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name varchar(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.auth_group_permissions (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_session (
    session_key varchar(40) PRIMARY KEY,
    session_data text NOT NULL,
    expire_date timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public."user" (
    password varchar(128) NOT NULL,
    last_login timestamptz NULL,
    is_superuser boolean NOT NULL,
    user_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    email varchar(254) NOT NULL,
    username varchar(150) NULL,
    first_name varchar(150) NOT NULL,
    middle_name varchar(150) NOT NULL,
    last_name varchar(150) NOT NULL,
    role varchar(20) NOT NULL,
    status varchar(20) NOT NULL,
    contact_number varchar(30) NOT NULL,
    address text NOT NULL,
    is_staff boolean NOT NULL,
    failed_login_attempts smallint NOT NULL,
    locked_until timestamptz NULL,
    last_login_ip inet NULL,
    last_login_at timestamptz NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.user_groups (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    group_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.user_user_permissions (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    permission_id integer NOT NULL
);

CREATE TABLE IF NOT EXISTS public.django_admin_log (
    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    action_time timestamptz NOT NULL,
    object_id text NULL,
    object_repr varchar(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer NULL,
    user_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS public.token_blacklist_outstandingtoken (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NULL,
    jti varchar(255) NOT NULL,
    token text NOT NULL,
    created_at timestamptz NULL,
    expires_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.token_blacklist_blacklistedtoken (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    token_id bigint NOT NULL,
    blacklisted_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.applicant_profile (
    applicant_profile_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    applicant_type varchar(30) NOT NULL,
    institution varchar(255) NOT NULL,
    student_or_employee_id varchar(100) NOT NULL,
    profile_photo varchar(100) NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.evaluator_profile (
    evaluator_profile_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    specialization varchar(40) NOT NULL,
    workload_count integer NOT NULL,
    is_available boolean NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.otp_code (
    otp_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    purpose varchar(30) NOT NULL,
    otp_hash varchar(255) NOT NULL,
    expires_at timestamptz NOT NULL,
    used_at timestamptz NULL,
    attempts smallint NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.encryption_key (
    key_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    key_code varchar(50) NOT NULL,
    key_name varchar(150) NOT NULL,
    algorithm varchar(50) NOT NULL,
    status varchar(20) NOT NULL,
    encrypted_key_material text NOT NULL,
    created_by_id bigint NULL,
    created_at timestamptz NOT NULL,
    rotated_at timestamptz NULL,
    disabled_at timestamptz NULL,
    rotation_policy varchar(255) NOT NULL,
    is_primary boolean NOT NULL,
    is_backup boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS public.ip_application (
    application_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    application_code varchar(40) NOT NULL,
    applicant_id bigint NOT NULL,
    ip_type varchar(30) NOT NULL,
    title varchar(255) NOT NULL,
    description text NOT NULL,
    abstract text NOT NULL,
    claims text NOT NULL,
    technical_explanation text NOT NULL,
    novelty_explanation text NOT NULL,
    supporting_details text NOT NULL,
    declaration_accepted boolean NOT NULL,
    status varchar(20) NOT NULL,
    completeness_score smallint NOT NULL,
    language_validation_status varchar(30) NOT NULL,
    created_at timestamptz NOT NULL,
    submitted_at timestamptz NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.application_checklist (
    checklist_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    application_id bigint NOT NULL,
    item_name varchar(255) NOT NULL,
    status varchar(20) NOT NULL,
    remarks text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public."case" (
    case_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_number varchar(40) NOT NULL,
    application_id bigint NOT NULL,
    applicant_id bigint NOT NULL,
    assigned_evaluator_id bigint NULL,
    taken_by_id bigint NULL,
    is_taken boolean NOT NULL,
    taken_at timestamptz NULL,
    status varchar(30) NOT NULL,
    priority_score integer NOT NULL,
    priority_label varchar(20) NOT NULL,
    deadline timestamptz NULL,
    sla_stage varchar(100) NOT NULL,
    sla_due_date timestamptz NULL,
    evaluation_summary text NOT NULL,
    evaluator_recommendation text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.case_status_history (
    status_history_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    previous_status varchar(30) NOT NULL,
    new_status varchar(30) NOT NULL,
    changed_by_id bigint NULL,
    remarks text NOT NULL,
    changed_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.activity_timeline (
    timeline_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    performed_by_id bigint NULL,
    role_visibility varchar(20) NOT NULL,
    action varchar(255) NOT NULL,
    applicant_message text NOT NULL,
    admin_message text NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.case_evaluation (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    evaluator_id bigint NOT NULL,
    content text NOT NULL,
    recommendation text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.document (
    document_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    uploaded_by_id bigint NOT NULL,
    document_type varchar(100) NOT NULL,
    original_filename varchar(255) NOT NULL,
    encrypted_file_path varchar(100) NOT NULL,
    file_size bigint NOT NULL,
    mime_type varchar(150) NOT NULL,
    encryption_key_id bigint NOT NULL,
    nonce varchar(50) NOT NULL,
    checksum varchar(64) NOT NULL,
    uploaded_at timestamptz NOT NULL,
    is_confidential boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS public.fee_assessment (
    assessment_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    application_id bigint NOT NULL,
    evaluator_id bigint NULL,
    amount numeric(12, 2) NOT NULL,
    fee_type varchar(120) NOT NULL,
    description text NOT NULL,
    status varchar(20) NOT NULL,
    issued_at timestamptz NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.payment (
    payment_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_id bigint NOT NULL,
    case_id bigint NOT NULL,
    applicant_id bigint NOT NULL,
    amount_paid numeric(12, 2) NOT NULL,
    payment_method varchar(80) NOT NULL,
    receipt_no varchar(100) NOT NULL,
    encrypted_receipt_file varchar(100) NOT NULL,
    original_filename varchar(255) NOT NULL,
    file_size bigint NOT NULL,
    mime_type varchar(150) NOT NULL,
    encryption_key_id bigint NOT NULL,
    nonce varchar(50) NOT NULL,
    checksum varchar(64) NOT NULL,
    payment_status varchar(20) NOT NULL,
    payment_date date NULL,
    verified_by_id bigint NULL,
    verified_at timestamptz NULL,
    remarks text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.conversation (
    conversation_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    applicant_id bigint NOT NULL,
    evaluator_id bigint NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.message (
    message_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    conversation_id bigint NOT NULL,
    sender_id bigint NOT NULL,
    content text NOT NULL,
    sent_at timestamptz NOT NULL,
    is_read boolean NOT NULL,
    has_attachment boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS public.message_attachment (
    attachment_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    message_id bigint NOT NULL,
    file_path varchar(100) NOT NULL,
    original_filename varchar(255) NOT NULL,
    file_size bigint NOT NULL,
    mime_type varchar(150) NOT NULL,
    uploaded_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.notification (
    notification_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL,
    related_case_id bigint NULL,
    type varchar(100) NOT NULL,
    title varchar(255) NOT NULL,
    content text NOT NULL,
    role_visibility varchar(30) NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.audit_log (
    log_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NULL,
    case_id bigint NULL,
    account_name varchar(255) NOT NULL,
    role varchar(30) NOT NULL,
    action varchar(150) NOT NULL,
    target varchar(150) NOT NULL,
    record_id varchar(100) NOT NULL,
    details text NOT NULL,
    ip_address inet NULL,
    user_agent text NOT NULL,
    log_timestamp timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.ip_record (
    record_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    case_id bigint NOT NULL,
    application_id bigint NOT NULL,
    encryption_key_id bigint NULL,
    certification_date date NULL,
    is_certified boolean NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.market_listing (
    listing_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    listing_code varchar(50) NOT NULL,
    record_id bigint NOT NULL,
    admin_id bigint NOT NULL,
    title varchar(255) NOT NULL,
    ip_type varchar(30) NOT NULL,
    inventor_name varchar(255) NOT NULL,
    short_description text NOT NULL,
    full_description text NOT NULL,
    category varchar(150) NOT NULL,
    availability_status varchar(100) NOT NULL,
    image varchar(100) NULL,
    status varchar(20) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.bookmark (
    bookmark_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    applicant_id bigint NOT NULL,
    listing_id bigint NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.inquiry (
    inquiry_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    inquiry_code varchar(50) NOT NULL,
    user_id bigint NULL,
    listing_id bigint NULL,
    sender_name varchar(255) NOT NULL,
    email varchar(254) NOT NULL,
    category varchar(100) NOT NULL,
    subject varchar(255) NOT NULL,
    message text NOT NULL,
    popularity_count integer NOT NULL,
    status varchar(20) NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.announcement (
    announcement_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    admin_id bigint NOT NULL,
    title varchar(255) NOT NULL,
    content text NOT NULL,
    category varchar(120) NOT NULL,
    is_published boolean NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.report_export (
    report_export_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    generated_by_id bigint NOT NULL,
    report_type varchar(120) NOT NULL,
    file_path varchar(100) NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.key_activity_log (
    key_activity_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    key_id bigint NOT NULL,
    action varchar(100) NOT NULL,
    performed_by_id bigint NULL,
    details text NOT NULL,
    ip_address inet NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.ipophl_email_parse (
    email_parse_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    sender varchar(254) NOT NULL,
    subject varchar(255) NOT NULL,
    body text NOT NULL,
    case_number_detected varchar(80) NOT NULL,
    report_type varchar(150) NOT NULL,
    deadline_detected date NULL,
    required_action text NOT NULL,
    attachments_metadata jsonb NOT NULL,
    matched_case_id bigint NULL,
    status varchar(20) NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS public.nlq_query (
    nlq_query_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id bigint NULL,
    raw_query text NOT NULL,
    detected_intent varchar(150) NOT NULL,
    extracted_filters jsonb NOT NULL,
    result_count integer NOT NULL,
    created_at timestamptz NOT NULL
);

-- ============================================================================
-- 003_indexes_and_constraints.sql
-- ============================================================================

-- 003_indexes_and_constraints.sql
-- Indexes and constraints based on the current Django models and migrations.
--
-- This file intentionally keeps constraints aligned with real model fields.
-- Choice checks are added only for fields that declare Django choices.

-- ---------------------------------------------------------------------------
-- Unique constraints
-- ---------------------------------------------------------------------------

ALTER TABLE public.django_content_type
    ADD CONSTRAINT uq_django_content_type_app_label_model UNIQUE (app_label, model);

ALTER TABLE public.auth_permission
    ADD CONSTRAINT uq_auth_permission_content_type_codename UNIQUE (content_type_id, codename);

ALTER TABLE public.auth_group
    ADD CONSTRAINT uq_auth_group_name UNIQUE (name);

ALTER TABLE public.auth_group_permissions
    ADD CONSTRAINT uq_auth_group_permissions_group_permission UNIQUE (group_id, permission_id);

ALTER TABLE public."user"
    ADD CONSTRAINT uq_user_email UNIQUE (email);

ALTER TABLE public."user"
    ADD CONSTRAINT uq_user_username UNIQUE (username);

ALTER TABLE public.user_groups
    ADD CONSTRAINT uq_user_groups_user_group UNIQUE (user_id, group_id);

ALTER TABLE public.user_user_permissions
    ADD CONSTRAINT uq_user_user_permissions_user_permission UNIQUE (user_id, permission_id);

ALTER TABLE public.token_blacklist_outstandingtoken
    ADD CONSTRAINT uq_token_blacklist_outstandingtoken_jti UNIQUE (jti);

ALTER TABLE public.token_blacklist_blacklistedtoken
    ADD CONSTRAINT uq_token_blacklist_blacklistedtoken_token UNIQUE (token_id);

ALTER TABLE public.applicant_profile
    ADD CONSTRAINT uq_applicant_profile_user UNIQUE (user_id);

ALTER TABLE public.evaluator_profile
    ADD CONSTRAINT uq_evaluator_profile_user UNIQUE (user_id);

ALTER TABLE public.encryption_key
    ADD CONSTRAINT uq_encryption_key_key_code UNIQUE (key_code);

ALTER TABLE public.ip_application
    ADD CONSTRAINT uq_ip_application_application_code UNIQUE (application_code);

ALTER TABLE public.application_checklist
    ADD CONSTRAINT uq_application_checklist_application_item UNIQUE (application_id, item_name);

ALTER TABLE public."case"
    ADD CONSTRAINT uq_case_case_number UNIQUE (case_number);

ALTER TABLE public."case"
    ADD CONSTRAINT uq_case_application UNIQUE (application_id);

ALTER TABLE public.conversation
    ADD CONSTRAINT unique_case_applicant_evaluator_conversation UNIQUE (case_id, applicant_id, evaluator_id);

ALTER TABLE public.ip_record
    ADD CONSTRAINT uq_ip_record_case UNIQUE (case_id);

ALTER TABLE public.market_listing
    ADD CONSTRAINT uq_market_listing_listing_code UNIQUE (listing_code);

ALTER TABLE public.bookmark
    ADD CONSTRAINT unique_applicant_market_listing_bookmark UNIQUE (applicant_id, listing_id);

ALTER TABLE public.inquiry
    ADD CONSTRAINT uq_inquiry_inquiry_code UNIQUE (inquiry_code);

-- ---------------------------------------------------------------------------
-- Foreign key constraints
-- ---------------------------------------------------------------------------

ALTER TABLE public.auth_permission
    ADD CONSTRAINT fk_auth_permission_content_type
    FOREIGN KEY (content_type_id) REFERENCES public.django_content_type (id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.auth_group_permissions
    ADD CONSTRAINT fk_auth_group_permissions_group
    FOREIGN KEY (group_id) REFERENCES public.auth_group (id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.auth_group_permissions
    ADD CONSTRAINT fk_auth_group_permissions_permission
    FOREIGN KEY (permission_id) REFERENCES public.auth_permission (id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.user_groups
    ADD CONSTRAINT fk_user_groups_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.user_groups
    ADD CONSTRAINT fk_user_groups_group
    FOREIGN KEY (group_id) REFERENCES public.auth_group (id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.user_user_permissions
    ADD CONSTRAINT fk_user_user_permissions_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.user_user_permissions
    ADD CONSTRAINT fk_user_user_permissions_permission
    FOREIGN KEY (permission_id) REFERENCES public.auth_permission (id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.django_admin_log
    ADD CONSTRAINT fk_django_admin_log_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.django_admin_log
    ADD CONSTRAINT fk_django_admin_log_content_type
    FOREIGN KEY (content_type_id) REFERENCES public.django_content_type (id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.token_blacklist_outstandingtoken
    ADD CONSTRAINT fk_token_blacklist_outstandingtoken_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.token_blacklist_blacklistedtoken
    ADD CONSTRAINT fk_token_blacklist_blacklistedtoken_token
    FOREIGN KEY (token_id) REFERENCES public.token_blacklist_outstandingtoken (id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.applicant_profile
    ADD CONSTRAINT fk_applicant_profile_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.evaluator_profile
    ADD CONSTRAINT fk_evaluator_profile_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.otp_code
    ADD CONSTRAINT fk_otp_code_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.encryption_key
    ADD CONSTRAINT fk_encryption_key_created_by
    FOREIGN KEY (created_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.ip_application
    ADD CONSTRAINT fk_ip_application_applicant
    FOREIGN KEY (applicant_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.application_checklist
    ADD CONSTRAINT fk_application_checklist_application
    FOREIGN KEY (application_id) REFERENCES public.ip_application (application_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public."case"
    ADD CONSTRAINT fk_case_application
    FOREIGN KEY (application_id) REFERENCES public.ip_application (application_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public."case"
    ADD CONSTRAINT fk_case_applicant
    FOREIGN KEY (applicant_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public."case"
    ADD CONSTRAINT fk_case_assigned_evaluator
    FOREIGN KEY (assigned_evaluator_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public."case"
    ADD CONSTRAINT fk_case_taken_by
    FOREIGN KEY (taken_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.case_status_history
    ADD CONSTRAINT fk_case_status_history_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.case_status_history
    ADD CONSTRAINT fk_case_status_history_changed_by
    FOREIGN KEY (changed_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.activity_timeline
    ADD CONSTRAINT fk_activity_timeline_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.activity_timeline
    ADD CONSTRAINT fk_activity_timeline_performed_by
    FOREIGN KEY (performed_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.case_evaluation
    ADD CONSTRAINT fk_case_evaluation_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.case_evaluation
    ADD CONSTRAINT fk_case_evaluation_evaluator
    FOREIGN KEY (evaluator_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.document
    ADD CONSTRAINT fk_document_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.document
    ADD CONSTRAINT fk_document_uploaded_by
    FOREIGN KEY (uploaded_by_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.document
    ADD CONSTRAINT fk_document_encryption_key
    FOREIGN KEY (encryption_key_id) REFERENCES public.encryption_key (key_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.fee_assessment
    ADD CONSTRAINT fk_fee_assessment_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.fee_assessment
    ADD CONSTRAINT fk_fee_assessment_application
    FOREIGN KEY (application_id) REFERENCES public.ip_application (application_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.fee_assessment
    ADD CONSTRAINT fk_fee_assessment_evaluator
    FOREIGN KEY (evaluator_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.payment
    ADD CONSTRAINT fk_payment_assessment
    FOREIGN KEY (assessment_id) REFERENCES public.fee_assessment (assessment_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.payment
    ADD CONSTRAINT fk_payment_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.payment
    ADD CONSTRAINT fk_payment_applicant
    FOREIGN KEY (applicant_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.payment
    ADD CONSTRAINT fk_payment_encryption_key
    FOREIGN KEY (encryption_key_id) REFERENCES public.encryption_key (key_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.payment
    ADD CONSTRAINT fk_payment_verified_by
    FOREIGN KEY (verified_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.conversation
    ADD CONSTRAINT fk_conversation_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.conversation
    ADD CONSTRAINT fk_conversation_applicant
    FOREIGN KEY (applicant_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.conversation
    ADD CONSTRAINT fk_conversation_evaluator
    FOREIGN KEY (evaluator_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.message
    ADD CONSTRAINT fk_message_conversation
    FOREIGN KEY (conversation_id) REFERENCES public.conversation (conversation_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.message
    ADD CONSTRAINT fk_message_sender
    FOREIGN KEY (sender_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.message_attachment
    ADD CONSTRAINT fk_message_attachment_message
    FOREIGN KEY (message_id) REFERENCES public.message (message_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.notification
    ADD CONSTRAINT fk_notification_recipient
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.notification
    ADD CONSTRAINT fk_notification_related_case
    FOREIGN KEY (related_case_id) REFERENCES public."case" (case_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.audit_log
    ADD CONSTRAINT fk_audit_log_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.audit_log
    ADD CONSTRAINT fk_audit_log_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.ip_record
    ADD CONSTRAINT fk_ip_record_case
    FOREIGN KEY (case_id) REFERENCES public."case" (case_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.ip_record
    ADD CONSTRAINT fk_ip_record_application
    FOREIGN KEY (application_id) REFERENCES public.ip_application (application_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.ip_record
    ADD CONSTRAINT fk_ip_record_encryption_key
    FOREIGN KEY (encryption_key_id) REFERENCES public.encryption_key (key_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.market_listing
    ADD CONSTRAINT fk_market_listing_record
    FOREIGN KEY (record_id) REFERENCES public.ip_record (record_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.market_listing
    ADD CONSTRAINT fk_market_listing_admin
    FOREIGN KEY (admin_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.bookmark
    ADD CONSTRAINT fk_bookmark_applicant
    FOREIGN KEY (applicant_id) REFERENCES public."user" (user_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.bookmark
    ADD CONSTRAINT fk_bookmark_listing
    FOREIGN KEY (listing_id) REFERENCES public.market_listing (listing_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.inquiry
    ADD CONSTRAINT fk_inquiry_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.inquiry
    ADD CONSTRAINT fk_inquiry_listing
    FOREIGN KEY (listing_id) REFERENCES public.market_listing (listing_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.announcement
    ADD CONSTRAINT fk_announcement_admin
    FOREIGN KEY (admin_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.report_export
    ADD CONSTRAINT fk_report_export_generated_by
    FOREIGN KEY (generated_by_id) REFERENCES public."user" (user_id)
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.key_activity_log
    ADD CONSTRAINT fk_key_activity_log_key
    FOREIGN KEY (key_id) REFERENCES public.encryption_key (key_id)
    ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.key_activity_log
    ADD CONSTRAINT fk_key_activity_log_performed_by
    FOREIGN KEY (performed_by_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.ipophl_email_parse
    ADD CONSTRAINT fk_ipophl_email_parse_matched_case
    FOREIGN KEY (matched_case_id) REFERENCES public."case" (case_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE public.nlq_query
    ADD CONSTRAINT fk_nlq_query_user
    FOREIGN KEY (user_id) REFERENCES public."user" (user_id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

-- ---------------------------------------------------------------------------
-- Check constraints from positive numeric Django fields
-- ---------------------------------------------------------------------------

ALTER TABLE public.django_admin_log
    ADD CONSTRAINT ck_django_admin_log_action_flag_nonnegative CHECK (action_flag >= 0);

ALTER TABLE public."user"
    ADD CONSTRAINT ck_user_failed_login_attempts_nonnegative CHECK (failed_login_attempts >= 0);

ALTER TABLE public.evaluator_profile
    ADD CONSTRAINT ck_evaluator_profile_workload_count_nonnegative CHECK (workload_count >= 0);

ALTER TABLE public.otp_code
    ADD CONSTRAINT ck_otp_code_attempts_nonnegative CHECK (attempts >= 0);

ALTER TABLE public.ip_application
    ADD CONSTRAINT ck_ip_application_completeness_score_nonnegative CHECK (completeness_score >= 0);

ALTER TABLE public."case"
    ADD CONSTRAINT ck_case_priority_score_nonnegative CHECK (priority_score >= 0);

ALTER TABLE public.document
    ADD CONSTRAINT ck_document_file_size_nonnegative CHECK (file_size >= 0);

ALTER TABLE public.payment
    ADD CONSTRAINT ck_payment_file_size_nonnegative CHECK (file_size >= 0);

ALTER TABLE public.message_attachment
    ADD CONSTRAINT ck_message_attachment_file_size_nonnegative CHECK (file_size >= 0);

ALTER TABLE public.inquiry
    ADD CONSTRAINT ck_inquiry_popularity_count_nonnegative CHECK (popularity_count >= 0);

ALTER TABLE public.nlq_query
    ADD CONSTRAINT ck_nlq_query_result_count_nonnegative CHECK (result_count >= 0);

-- ---------------------------------------------------------------------------
-- Check constraints from Django choice fields
-- ---------------------------------------------------------------------------

ALTER TABLE public."user"
    ADD CONSTRAINT ck_user_role_choice CHECK (role IN ('applicant', 'evaluator', 'admin'));

ALTER TABLE public."user"
    ADD CONSTRAINT ck_user_status_choice CHECK (status IN ('active', 'inactive', 'locked', 'archived'));

ALTER TABLE public.otp_code
    ADD CONSTRAINT ck_otp_code_purpose_choice CHECK (purpose IN ('login', 'registration', 'password_reset'));

ALTER TABLE public.applicant_profile
    ADD CONSTRAINT ck_applicant_profile_applicant_type_choice CHECK (applicant_type IN ('faculty', 'staff', 'student', 'external'));

ALTER TABLE public.evaluator_profile
    ADD CONSTRAINT ck_evaluator_profile_specialization_choice CHECK (
        specialization IN (
            'patent_mechanical',
            'patent_electrical',
            'utility_model',
            'industrial_design',
            'trademark',
            'copyright'
        )
    );

ALTER TABLE public.ip_application
    ADD CONSTRAINT ck_ip_application_ip_type_choice CHECK (
        ip_type IN ('patent', 'utility_model', 'industrial_design', 'trademark', 'copyright')
    );

ALTER TABLE public.ip_application
    ADD CONSTRAINT ck_ip_application_status_choice CHECK (status IN ('draft', 'submitted', 'withdrawn'));

ALTER TABLE public.ip_application
    ADD CONSTRAINT ck_ip_application_language_validation_status_choice CHECK (
        language_validation_status IN ('valid', 'warning', 'failed')
    );

ALTER TABLE public.application_checklist
    ADD CONSTRAINT ck_application_checklist_status_choice CHECK (
        status IN ('complete', 'missing', 'needs_review', 'optional')
    );

ALTER TABLE public."case"
    ADD CONSTRAINT ck_case_status_choice CHECK (
        status IN ('pending', 'under_review', 'evaluated', 'on_going', 'certified', 'archived')
    );

ALTER TABLE public."case"
    ADD CONSTRAINT ck_case_priority_label_choice CHECK (
        priority_label IN ('low', 'normal', 'medium', 'high', 'critical')
    );

ALTER TABLE public.activity_timeline
    ADD CONSTRAINT ck_activity_timeline_role_visibility_choice CHECK (role_visibility IN ('applicant', 'admin', 'all'));

ALTER TABLE public.fee_assessment
    ADD CONSTRAINT ck_fee_assessment_status_choice CHECK (
        status IN ('pending', 'issued', 'paid', 'waived', 'cancelled')
    );

ALTER TABLE public.payment
    ADD CONSTRAINT ck_payment_status_choice CHECK (payment_status IN ('pending', 'verified', 'rejected'));

ALTER TABLE public.market_listing
    ADD CONSTRAINT ck_market_listing_status_choice CHECK (status IN ('draft', 'published', 'archived'));

ALTER TABLE public.inquiry
    ADD CONSTRAINT ck_inquiry_status_choice CHECK (status IN ('new', 'answered', 'closed'));

ALTER TABLE public.encryption_key
    ADD CONSTRAINT ck_encryption_key_status_choice CHECK (status IN ('active', 'rotated', 'disabled'));

ALTER TABLE public.ipophl_email_parse
    ADD CONSTRAINT ck_ipophl_email_parse_status_choice CHECK (status IN ('matched', 'unmatched', 'failed'));

-- KeyActivityLog.Action is defined as a TextChoices class in the model, but
-- the action field currently does not declare choices=Action. For that reason
-- no active CHECK constraint is added here.
--
-- Recommendation only, not active SQL:
-- ALTER TABLE public.key_activity_log
--     ADD CONSTRAINT ck_key_activity_log_action_choice
--     CHECK (action IN ('generated', 'rotated', 'disabled', 'escrow_report_generated'));

-- EncryptionKey currently has is_primary, but the Django model does not define
-- a uniqueness constraint limiting active primary keys. Keep this recommendation
-- commented unless the Django model is updated to match it.
--
-- CREATE UNIQUE INDEX uq_one_active_primary_encryption_key
--     ON public.encryption_key (is_primary)
--     WHERE is_primary = true AND status = 'active';

-- ---------------------------------------------------------------------------
-- Indexes declared in Django Meta.indexes and useful FK indexes
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_auth_permission_content_type_id ON public.auth_permission (content_type_id);
CREATE INDEX IF NOT EXISTS idx_auth_group_name_like ON public.auth_group (name varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_auth_group_permissions_group_id ON public.auth_group_permissions (group_id);
CREATE INDEX IF NOT EXISTS idx_auth_group_permissions_permission_id ON public.auth_group_permissions (permission_id);
CREATE INDEX IF NOT EXISTS idx_django_admin_log_content_type_id ON public.django_admin_log (content_type_id);
CREATE INDEX IF NOT EXISTS idx_django_admin_log_user_id ON public.django_admin_log (user_id);
CREATE INDEX IF NOT EXISTS idx_django_session_expire_date ON public.django_session (expire_date);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_outstandingtoken_user_id ON public.token_blacklist_outstandingtoken (user_id);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_outstandingtoken_expires_at ON public.token_blacklist_outstandingtoken (expires_at);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_outstandingtoken_jti_like ON public.token_blacklist_outstandingtoken (jti varchar_pattern_ops);

CREATE INDEX IF NOT EXISTS user_email_7bbb4c_idx ON public."user" (email);
CREATE INDEX IF NOT EXISTS user_role_3744fd_idx ON public."user" (role);
CREATE INDEX IF NOT EXISTS user_status_116710_idx ON public."user" (status);
CREATE INDEX IF NOT EXISTS idx_user_email_like ON public."user" (email varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_user_username_like ON public."user" (username varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_user_groups_user_id ON public.user_groups (user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group_id ON public.user_groups (group_id);
CREATE INDEX IF NOT EXISTS idx_user_user_permissions_user_id ON public.user_user_permissions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_user_permissions_permission_id ON public.user_user_permissions (permission_id);
CREATE INDEX IF NOT EXISTS otp_code_user_id_8922b8_idx ON public.otp_code (user_id, purpose, created_at);
CREATE INDEX IF NOT EXISTS otp_code_expires_8d1cde_idx ON public.otp_code (expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_code_user_id ON public.otp_code (user_id);

CREATE INDEX IF NOT EXISTS encryption__key_cod_76a822_idx ON public.encryption_key (key_code);
CREATE INDEX IF NOT EXISTS encryption__status_4fdfda_idx ON public.encryption_key (status);
CREATE INDEX IF NOT EXISTS encryption__is_prim_35df32_idx ON public.encryption_key (is_primary);
CREATE INDEX IF NOT EXISTS idx_encryption_key_created_by_id ON public.encryption_key (created_by_id);
CREATE INDEX IF NOT EXISTS idx_key_activity_log_key_id ON public.key_activity_log (key_id);
CREATE INDEX IF NOT EXISTS idx_key_activity_log_performed_by_id ON public.key_activity_log (performed_by_id);
CREATE INDEX IF NOT EXISTS idx_key_activity_log_action ON public.key_activity_log (action);

CREATE INDEX IF NOT EXISTS ip_applicat_applica_77989d_idx ON public.ip_application (application_code);
CREATE INDEX IF NOT EXISTS ip_applicat_applica_e9ba39_idx ON public.ip_application (applicant_id);
CREATE INDEX IF NOT EXISTS ip_applicat_ip_type_e35c6a_idx ON public.ip_application (ip_type);
CREATE INDEX IF NOT EXISTS ip_applicat_status_fdf317_idx ON public.ip_application (status);
CREATE INDEX IF NOT EXISTS ip_applicat_submitt_d7b8be_idx ON public.ip_application (submitted_at);
CREATE INDEX IF NOT EXISTS idx_application_checklist_application_id ON public.application_checklist (application_id);

CREATE INDEX IF NOT EXISTS case_case_nu_3c14f4_idx ON public."case" (case_number);
CREATE INDEX IF NOT EXISTS case_applica_f396a2_idx ON public."case" (applicant_id);
CREATE INDEX IF NOT EXISTS case_assigne_b7decd_idx ON public."case" (assigned_evaluator_id);
CREATE INDEX IF NOT EXISTS case_taken_b_a6301c_idx ON public."case" (taken_by_id);
CREATE INDEX IF NOT EXISTS case_status_deb121_idx ON public."case" (status);
CREATE INDEX IF NOT EXISTS case_deadlin_8e1017_idx ON public."case" (deadline);
CREATE INDEX IF NOT EXISTS case_priorit_fd53f3_idx ON public."case" (priority_score);
CREATE INDEX IF NOT EXISTS idx_case_application_id ON public."case" (application_id);
CREATE INDEX IF NOT EXISTS idx_case_status_history_case_id ON public.case_status_history (case_id);
CREATE INDEX IF NOT EXISTS idx_case_status_history_changed_by_id ON public.case_status_history (changed_by_id);
CREATE INDEX IF NOT EXISTS idx_activity_timeline_case_id ON public.activity_timeline (case_id);
CREATE INDEX IF NOT EXISTS idx_activity_timeline_performed_by_id ON public.activity_timeline (performed_by_id);
CREATE INDEX IF NOT EXISTS idx_case_evaluation_case_id ON public.case_evaluation (case_id);
CREATE INDEX IF NOT EXISTS idx_case_evaluation_evaluator_id ON public.case_evaluation (evaluator_id);

CREATE INDEX IF NOT EXISTS document_case_id_f867da_idx ON public.document (case_id);
CREATE INDEX IF NOT EXISTS document_uploade_523401_idx ON public.document (uploaded_by_id);
CREATE INDEX IF NOT EXISTS document_documen_eae0b0_idx ON public.document (document_type);
CREATE INDEX IF NOT EXISTS document_uploade_7afb96_idx ON public.document (uploaded_at);
CREATE INDEX IF NOT EXISTS idx_document_encryption_key_id ON public.document (encryption_key_id);

CREATE INDEX IF NOT EXISTS fee_assessm_case_id_477045_idx ON public.fee_assessment (case_id);
CREATE INDEX IF NOT EXISTS fee_assessm_applica_7c73dc_idx ON public.fee_assessment (application_id);
CREATE INDEX IF NOT EXISTS fee_assessm_evaluat_7b8d9f_idx ON public.fee_assessment (evaluator_id);
CREATE INDEX IF NOT EXISTS fee_assessm_status_cd983c_idx ON public.fee_assessment (status);
CREATE INDEX IF NOT EXISTS payment_assessm_91b40e_idx ON public.payment (assessment_id);
CREATE INDEX IF NOT EXISTS payment_case_id_1237eb_idx ON public.payment (case_id);
CREATE INDEX IF NOT EXISTS payment_applica_21c5a2_idx ON public.payment (applicant_id);
CREATE INDEX IF NOT EXISTS payment_payment_285a08_idx ON public.payment (payment_status);
CREATE INDEX IF NOT EXISTS payment_payment_904250_idx ON public.payment (payment_date);
CREATE INDEX IF NOT EXISTS idx_payment_encryption_key_id ON public.payment (encryption_key_id);
CREATE INDEX IF NOT EXISTS idx_payment_verified_by_id ON public.payment (verified_by_id);

CREATE INDEX IF NOT EXISTS idx_conversation_case_id ON public.conversation (case_id);
CREATE INDEX IF NOT EXISTS idx_conversation_applicant_id ON public.conversation (applicant_id);
CREATE INDEX IF NOT EXISTS idx_conversation_evaluator_id ON public.conversation (evaluator_id);
CREATE INDEX IF NOT EXISTS message_convers_34c8b8_idx ON public.message (conversation_id, sent_at);
CREATE INDEX IF NOT EXISTS message_sender__0e912c_idx ON public.message (sender_id);
CREATE INDEX IF NOT EXISTS message_is_read_8eefe1_idx ON public.message (is_read);
CREATE INDEX IF NOT EXISTS idx_message_attachment_message_id ON public.message_attachment (message_id);

CREATE INDEX IF NOT EXISTS notificatio_user_id_3cbd6f_idx ON public.notification (user_id);
CREATE INDEX IF NOT EXISTS notificatio_related_2c0ef0_idx ON public.notification (related_case_id);
CREATE INDEX IF NOT EXISTS notificatio_type_f65c28_idx ON public.notification (type);
CREATE INDEX IF NOT EXISTS notificatio_role_vi_3fceb9_idx ON public.notification (role_visibility);
CREATE INDEX IF NOT EXISTS notificatio_is_read_8a483f_idx ON public.notification (is_read);

CREATE INDEX IF NOT EXISTS audit_log_log_tim_33ab23_idx ON public.audit_log (log_timestamp);
CREATE INDEX IF NOT EXISTS audit_log_action_b32d4d_idx ON public.audit_log (action);
CREATE INDEX IF NOT EXISTS audit_log_role_186789_idx ON public.audit_log (role);
CREATE INDEX IF NOT EXISTS audit_log_case_id_6ecb42_idx ON public.audit_log (case_id);
CREATE INDEX IF NOT EXISTS audit_log_record__a10a3a_idx ON public.audit_log (record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log (user_id);

CREATE INDEX IF NOT EXISTS ip_record_case_id_dbcd3e_idx ON public.ip_record (case_id);
CREATE INDEX IF NOT EXISTS ip_record_applica_21607c_idx ON public.ip_record (application_id);
CREATE INDEX IF NOT EXISTS ip_record_is_cert_ddab6b_idx ON public.ip_record (is_certified);
CREATE INDEX IF NOT EXISTS idx_ip_record_encryption_key_id ON public.ip_record (encryption_key_id);
CREATE INDEX IF NOT EXISTS market_list_listing_6810cb_idx ON public.market_listing (listing_code);
CREATE INDEX IF NOT EXISTS market_list_record__4b99b6_idx ON public.market_listing (record_id);
CREATE INDEX IF NOT EXISTS market_list_admin_i_c57302_idx ON public.market_listing (admin_id);
CREATE INDEX IF NOT EXISTS market_list_ip_type_41f254_idx ON public.market_listing (ip_type);
CREATE INDEX IF NOT EXISTS market_list_status_c8c1b6_idx ON public.market_listing (status, is_active);
CREATE INDEX IF NOT EXISTS bookmark_applica_a01571_idx ON public.bookmark (applicant_id);
CREATE INDEX IF NOT EXISTS bookmark_listing_bee8bb_idx ON public.bookmark (listing_id);

CREATE INDEX IF NOT EXISTS inquiry_inquiry_7522f9_idx ON public.inquiry (inquiry_code);
CREATE INDEX IF NOT EXISTS inquiry_user_id_090206_idx ON public.inquiry (user_id);
CREATE INDEX IF NOT EXISTS inquiry_listing_49a296_idx ON public.inquiry (listing_id);
CREATE INDEX IF NOT EXISTS inquiry_categor_9f78e9_idx ON public.inquiry (category);
CREATE INDEX IF NOT EXISTS inquiry_status_1d105d_idx ON public.inquiry (status);
CREATE INDEX IF NOT EXISTS inquiry_popular_1ca465_idx ON public.inquiry (popularity_count);

CREATE INDEX IF NOT EXISTS announcemen_is_publ_470336_idx ON public.announcement (is_published);
CREATE INDEX IF NOT EXISTS announcemen_categor_6192ba_idx ON public.announcement (category);
CREATE INDEX IF NOT EXISTS announcemen_created_cbc578_idx ON public.announcement (created_at);
CREATE INDEX IF NOT EXISTS idx_announcement_admin_id ON public.announcement (admin_id);

CREATE INDEX IF NOT EXISTS report_expo_generat_42e2ef_idx ON public.report_export (generated_by_id);
CREATE INDEX IF NOT EXISTS report_expo_report__a427c4_idx ON public.report_export (report_type);
CREATE INDEX IF NOT EXISTS report_expo_created_5b869b_idx ON public.report_export (created_at);

CREATE INDEX IF NOT EXISTS ipophl_emai_sender_0c4964_idx ON public.ipophl_email_parse (sender);
CREATE INDEX IF NOT EXISTS ipophl_emai_case_nu_ae5742_idx ON public.ipophl_email_parse (case_number_detected);
CREATE INDEX IF NOT EXISTS ipophl_emai_report__528ce4_idx ON public.ipophl_email_parse (report_type);
CREATE INDEX IF NOT EXISTS ipophl_emai_deadlin_da6139_idx ON public.ipophl_email_parse (deadline_detected);
CREATE INDEX IF NOT EXISTS ipophl_emai_status_148eac_idx ON public.ipophl_email_parse (status);
CREATE INDEX IF NOT EXISTS idx_ipophl_email_parse_matched_case_id ON public.ipophl_email_parse (matched_case_id);

CREATE INDEX IF NOT EXISTS nlq_query_user_id_8c4ded_idx ON public.nlq_query (user_id);
CREATE INDEX IF NOT EXISTS nlq_query_detecte_fc940a_idx ON public.nlq_query (detected_intent);
CREATE INDEX IF NOT EXISTS nlq_query_created_e2c444_idx ON public.nlq_query (created_at);

-- ============================================================================
-- 004_rls_policies.sql
-- ============================================================================

-- 004_rls_policies.sql
-- Supabase Row Level Security policies for the current Django schema.
--
-- Important:
-- The current backend uses Django authentication and SimpleJWT. These policies
-- are useful only if the system later uses Supabase Auth, or if equivalent JWT
-- context is passed so auth.jwt() contains an email claim matching
-- public."user".email.
--
-- Django connections using the database owner/service role generally bypass RLS
-- unless PostgreSQL FORCE ROW LEVEL SECURITY is enabled. Keep Django API
-- permissions as the primary authorization layer unless auth is redesigned.

-- ---------------------------------------------------------------------------
-- Auth helper functions
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.current_app_user_id()
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT u.user_id
    FROM public."user" u
    WHERE lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION public.current_app_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT u.role
    FROM public."user" u
    WHERE u.user_id = public.current_app_user_id()
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION public.is_app_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT coalesce(public.current_app_role() = 'admin', false)
$$;

CREATE OR REPLACE FUNCTION public.is_app_evaluator()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT coalesce(public.current_app_role() = 'evaluator', false)
$$;

CREATE OR REPLACE FUNCTION public.can_access_case(p_case_id bigint)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT public.is_app_admin()
        OR EXISTS (
            SELECT 1
            FROM public."case" c
            WHERE c.case_id = p_case_id
              AND (
                  c.applicant_id = public.current_app_user_id()
                  OR c.assigned_evaluator_id = public.current_app_user_id()
                  OR c.taken_by_id = public.current_app_user_id()
              )
        )
$$;

CREATE OR REPLACE FUNCTION public.can_access_application(p_application_id bigint)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT public.is_app_admin()
        OR EXISTS (
            SELECT 1
            FROM public.ip_application a
            WHERE a.application_id = p_application_id
              AND a.applicant_id = public.current_app_user_id()
        )
        OR EXISTS (
            SELECT 1
            FROM public."case" c
            WHERE c.application_id = p_application_id
              AND public.can_access_case(c.case_id)
        )
$$;

CREATE OR REPLACE FUNCTION public.can_access_conversation(p_conversation_id bigint)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT public.is_app_admin()
        OR EXISTS (
            SELECT 1
            FROM public.conversation cv
            WHERE cv.conversation_id = p_conversation_id
              AND (
                  cv.applicant_id = public.current_app_user_id()
                  OR cv.evaluator_id = public.current_app_user_id()
                  OR public.can_access_case(cv.case_id)
              )
        )
$$;

CREATE OR REPLACE FUNCTION public.can_access_message(p_message_id bigint)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT public.is_app_admin()
        OR EXISTS (
            SELECT 1
            FROM public.message m
            WHERE m.message_id = p_message_id
              AND public.can_access_conversation(m.conversation_id)
        )
$$;

-- ---------------------------------------------------------------------------
-- Enable RLS and give admins broad access.
-- ---------------------------------------------------------------------------

DO $$
DECLARE
    table_name text;
    table_names text[] := ARRAY[
        'django_content_type',
        'auth_permission',
        'auth_group',
        'auth_group_permissions',
        'django_session',
        'django_admin_log',
        'token_blacklist_outstandingtoken',
        'token_blacklist_blacklistedtoken',
        'user',
        'user_groups',
        'user_user_permissions',
        'applicant_profile',
        'evaluator_profile',
        'otp_code',
        'encryption_key',
        'key_activity_log',
        'ip_application',
        'application_checklist',
        'case',
        'case_status_history',
        'activity_timeline',
        'case_evaluation',
        'document',
        'fee_assessment',
        'payment',
        'conversation',
        'message',
        'message_attachment',
        'notification',
        'audit_log',
        'ip_record',
        'market_listing',
        'bookmark',
        'inquiry',
        'announcement',
        'report_export',
        'ipophl_email_parse',
        'nlq_query'
    ];
BEGIN
    FOREACH table_name IN ARRAY table_names LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('DROP POLICY IF EXISTS admin_all ON public.%I', table_name);
        EXECUTE format(
            'CREATE POLICY admin_all ON public.%I FOR ALL TO authenticated USING (public.is_app_admin()) WITH CHECK (public.is_app_admin())',
            table_name
        );
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- Account and profile policies
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS user_self_select ON public."user";
CREATE POLICY user_self_select ON public."user"
    FOR SELECT TO authenticated
    USING (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS user_self_update ON public."user";
CREATE POLICY user_self_update ON public."user"
    FOR UPDATE TO authenticated
    USING (user_id = public.current_app_user_id())
    WITH CHECK (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS applicant_profile_self ON public.applicant_profile;
CREATE POLICY applicant_profile_self ON public.applicant_profile
    FOR ALL TO authenticated
    USING (user_id = public.current_app_user_id())
    WITH CHECK (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS evaluator_profile_self ON public.evaluator_profile;
CREATE POLICY evaluator_profile_self ON public.evaluator_profile
    FOR SELECT TO authenticated
    USING (user_id = public.current_app_user_id());

-- OTP codes and Django auth/session/token tables are intentionally admin-only.
-- Normal users should not read OTP hashes, session rows, or JWT blacklist rows.

-- ---------------------------------------------------------------------------
-- Applications, cases, evaluations, and timelines
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS ip_application_applicant_select ON public.ip_application;
CREATE POLICY ip_application_applicant_select ON public.ip_application
    FOR SELECT TO authenticated
    USING (applicant_id = public.current_app_user_id() OR public.can_access_application(application_id));

DROP POLICY IF EXISTS ip_application_applicant_insert ON public.ip_application;
CREATE POLICY ip_application_applicant_insert ON public.ip_application
    FOR INSERT TO authenticated
    WITH CHECK (applicant_id = public.current_app_user_id());

DROP POLICY IF EXISTS ip_application_applicant_update ON public.ip_application;
CREATE POLICY ip_application_applicant_update ON public.ip_application
    FOR UPDATE TO authenticated
    USING (applicant_id = public.current_app_user_id())
    WITH CHECK (applicant_id = public.current_app_user_id());

DROP POLICY IF EXISTS application_checklist_case_access_select ON public.application_checklist;
CREATE POLICY application_checklist_case_access_select ON public.application_checklist
    FOR SELECT TO authenticated
    USING (public.can_access_application(application_id));

DROP POLICY IF EXISTS case_applicant_or_evaluator_select ON public."case";
CREATE POLICY case_applicant_or_evaluator_select ON public."case"
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id));

DROP POLICY IF EXISTS case_evaluator_update ON public."case";
CREATE POLICY case_evaluator_update ON public."case"
    FOR UPDATE TO authenticated
    USING (
        public.is_app_evaluator()
        AND (
            assigned_evaluator_id = public.current_app_user_id()
            OR taken_by_id = public.current_app_user_id()
        )
    )
    WITH CHECK (
        public.is_app_evaluator()
        AND (
            assigned_evaluator_id = public.current_app_user_id()
            OR taken_by_id = public.current_app_user_id()
        )
    );

DROP POLICY IF EXISTS case_status_history_case_access_select ON public.case_status_history;
CREATE POLICY case_status_history_case_access_select ON public.case_status_history
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id));

DROP POLICY IF EXISTS activity_timeline_case_access_select ON public.activity_timeline;
CREATE POLICY activity_timeline_case_access_select ON public.activity_timeline
    FOR SELECT TO authenticated
    USING (
        public.can_access_case(case_id)
        AND (
            public.is_app_admin()
            OR role_visibility = 'all'
            OR (role_visibility = 'applicant' AND public.current_app_role() = 'applicant')
            OR (role_visibility = 'admin' AND public.current_app_role() = 'admin')
        )
    );

DROP POLICY IF EXISTS case_evaluation_case_access_select ON public.case_evaluation;
CREATE POLICY case_evaluation_case_access_select ON public.case_evaluation
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id));

DROP POLICY IF EXISTS case_evaluation_evaluator_insert ON public.case_evaluation;
CREATE POLICY case_evaluation_evaluator_insert ON public.case_evaluation
    FOR INSERT TO authenticated
    WITH CHECK (
        evaluator_id = public.current_app_user_id()
        AND public.can_access_case(case_id)
    );

-- ---------------------------------------------------------------------------
-- Documents and payments
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS document_case_access_select ON public.document;
CREATE POLICY document_case_access_select ON public.document
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id));

DROP POLICY IF EXISTS document_uploader_insert ON public.document;
CREATE POLICY document_uploader_insert ON public.document
    FOR INSERT TO authenticated
    WITH CHECK (
        uploaded_by_id = public.current_app_user_id()
        AND public.can_access_case(case_id)
    );

DROP POLICY IF EXISTS fee_assessment_case_access_select ON public.fee_assessment;
CREATE POLICY fee_assessment_case_access_select ON public.fee_assessment
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id) OR public.can_access_application(application_id));

DROP POLICY IF EXISTS payment_case_access_select ON public.payment;
CREATE POLICY payment_case_access_select ON public.payment
    FOR SELECT TO authenticated
    USING (applicant_id = public.current_app_user_id() OR public.can_access_case(case_id));

DROP POLICY IF EXISTS payment_applicant_insert ON public.payment;
CREATE POLICY payment_applicant_insert ON public.payment
    FOR INSERT TO authenticated
    WITH CHECK (
        applicant_id = public.current_app_user_id()
        AND public.can_access_case(case_id)
    );

-- ---------------------------------------------------------------------------
-- Messaging
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS conversation_participant_select ON public.conversation;
CREATE POLICY conversation_participant_select ON public.conversation
    FOR SELECT TO authenticated
    USING (public.can_access_conversation(conversation_id));

DROP POLICY IF EXISTS conversation_participant_insert ON public.conversation;
CREATE POLICY conversation_participant_insert ON public.conversation
    FOR INSERT TO authenticated
    WITH CHECK (
        applicant_id = public.current_app_user_id()
        OR evaluator_id = public.current_app_user_id()
        OR public.can_access_case(case_id)
    );

DROP POLICY IF EXISTS message_conversation_access_select ON public.message;
CREATE POLICY message_conversation_access_select ON public.message
    FOR SELECT TO authenticated
    USING (public.can_access_conversation(conversation_id));

DROP POLICY IF EXISTS message_sender_insert ON public.message;
CREATE POLICY message_sender_insert ON public.message
    FOR INSERT TO authenticated
    WITH CHECK (
        sender_id = public.current_app_user_id()
        AND public.can_access_conversation(conversation_id)
    );

DROP POLICY IF EXISTS message_reader_update ON public.message;
CREATE POLICY message_reader_update ON public.message
    FOR UPDATE TO authenticated
    USING (public.can_access_conversation(conversation_id))
    WITH CHECK (public.can_access_conversation(conversation_id));

DROP POLICY IF EXISTS message_attachment_message_access_select ON public.message_attachment;
CREATE POLICY message_attachment_message_access_select ON public.message_attachment
    FOR SELECT TO authenticated
    USING (public.can_access_message(message_id));

DROP POLICY IF EXISTS message_attachment_message_access_insert ON public.message_attachment;
CREATE POLICY message_attachment_message_access_insert ON public.message_attachment
    FOR INSERT TO authenticated
    WITH CHECK (public.can_access_message(message_id));

-- ---------------------------------------------------------------------------
-- Notifications
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS notification_recipient_select ON public.notification;
CREATE POLICY notification_recipient_select ON public.notification
    FOR SELECT TO authenticated
    USING (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS notification_recipient_update ON public.notification;
CREATE POLICY notification_recipient_update ON public.notification
    FOR UPDATE TO authenticated
    USING (user_id = public.current_app_user_id())
    WITH CHECK (user_id = public.current_app_user_id());

-- ---------------------------------------------------------------------------
-- Marketplace, bookmarks, inquiries, and announcements
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS market_listing_public_select ON public.market_listing;
CREATE POLICY market_listing_public_select ON public.market_listing
    FOR SELECT TO anon, authenticated
    USING (status = 'published' AND is_active = true);

DROP POLICY IF EXISTS bookmark_applicant_all ON public.bookmark;
CREATE POLICY bookmark_applicant_all ON public.bookmark
    FOR ALL TO authenticated
    USING (applicant_id = public.current_app_user_id())
    WITH CHECK (applicant_id = public.current_app_user_id());

DROP POLICY IF EXISTS inquiry_public_insert ON public.inquiry;
CREATE POLICY inquiry_public_insert ON public.inquiry
    FOR INSERT TO anon, authenticated
    WITH CHECK (user_id IS NULL OR user_id = public.current_app_user_id());

DROP POLICY IF EXISTS inquiry_owner_select ON public.inquiry;
CREATE POLICY inquiry_owner_select ON public.inquiry
    FOR SELECT TO authenticated
    USING (user_id = public.current_app_user_id());

DROP POLICY IF EXISTS announcement_public_select ON public.announcement;
CREATE POLICY announcement_public_select ON public.announcement
    FOR SELECT TO anon, authenticated
    USING (is_published = true);

-- ---------------------------------------------------------------------------
-- Reports, audit logs, encryption keys, email parser, and NLQ
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS report_export_owner_select ON public.report_export;
CREATE POLICY report_export_owner_select ON public.report_export
    FOR SELECT TO authenticated
    USING (generated_by_id = public.current_app_user_id());

-- Audit logs are admin-only through admin_all. No normal user update/delete
-- policies are defined.

-- Encryption keys and key activity logs are admin-only through admin_all.
-- Raw encrypted_key_material is never exposed to public/normal user policies.

DROP POLICY IF EXISTS ip_record_case_access_select ON public.ip_record;
CREATE POLICY ip_record_case_access_select ON public.ip_record
    FOR SELECT TO authenticated
    USING (public.can_access_case(case_id) OR public.can_access_application(application_id));

DROP POLICY IF EXISTS ipophl_email_parse_case_access_select ON public.ipophl_email_parse;
CREATE POLICY ipophl_email_parse_case_access_select ON public.ipophl_email_parse
    FOR SELECT TO authenticated
    USING (matched_case_id IS NOT NULL AND public.can_access_case(matched_case_id));

DROP POLICY IF EXISTS nlq_query_owner_all ON public.nlq_query;
CREATE POLICY nlq_query_owner_all ON public.nlq_query
    FOR ALL TO authenticated
    USING (user_id = public.current_app_user_id())
    WITH CHECK (user_id = public.current_app_user_id());

-- ============================================================================
-- 005_reference_data.sql
-- ============================================================================

-- 005_reference_data.sql
-- Required reference data for The Creator's Bulwark.
--
-- The inspected Django models store roles, statuses, IP types, and other fixed
-- values as CharField/TextChoices, not lookup/reference tables. Because of that
-- there is no required seed data to insert here.
--
-- Do not insert users, applicants, evaluators, admins, cases, applications,
-- documents, payments, marketplace listings, audit logs, messages, or demo data.
--
-- If the Django models are later changed to use lookup tables, add only those
-- required lookup rows here and use ON CONFLICT DO NOTHING.

-- No active INSERT statements are required for the current schema.

-- ============================================================================
-- 006_views_and_functions.sql
-- ============================================================================

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

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

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

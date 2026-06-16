# TCB Workflow Integration Repair Design

## Objective

Repair the integration between the Django REST backend and the existing vanilla JavaScript frontend so authenticated Applicant, Evaluator, and Admin workflows use real backend data and enforce existing role permissions.

The highest-priority acceptance flow is:

1. An Applicant creates and submits an IP application.
2. The backend marks the application `submitted`.
3. The backend creates exactly one related Case with:
   - `status = pending`
   - `is_taken = false`
   - `taken_by = null`
   - `assigned_evaluator = null`
   - `taken_at = null`
   - `deadline = null`
4. A matching available Evaluator receives the Case from `GET /api/cases/available/`.
5. The Evaluator takes it through `POST /api/cases/{id}/take/`.
6. The backend changes the Case to `under_review`, assigns the Evaluator, and sets the deadline to `taken_at + 90 days`.
7. The Case disappears from Available Cases and appears in `GET /api/cases/my-cases/`.

## Constraints

- Do not rewrite the frontend or redesign the UI.
- Do not add dummy records, seed records, fake accounts, or fallback cases.
- Do not disable authentication, OTP, JWT handling, RBAC, specialization matching, or object-level permissions.
- Do not bypass backend validation to make the UI appear successful.
- Keep changes small and focused on verified integration defects.
- Do not run schema-changing commands unless model changes are necessary and explained first.

## Current Architecture

The project is a Django 5.2 application with Django REST Framework, Simple JWT, a custom `accounts.User`, and a single-page frontend implemented in `templates/index.html` and `static/js/app.js`.

Backend modules separate authentication, applications, cases, documents, payments, messaging, notifications, audit logs, marketplace, inquiries, announcements, and reports. The frontend, however, keeps a large shared in-memory and local-storage model that combines prototype state with records mapped from backend responses.

The backend already contains the core application submission and evaluator take-case services. Existing tests demonstrate that these backend transitions work when called directly through the API.

## Root Causes

### Submission is not backend-authoritative

`submitForm()` catches errors from `createBackendApplication()` but continues to create a browser-local submission and displays a successful confirmation. A failed API request therefore produces a record visible only in the Applicant browser. No Case exists for the Evaluator API to return.

### Document and completeness ordering conflicts

The frontend currently creates the application, submits it, and uploads documents only after Case creation. Industrial Design completeness expects drawings before submission, while document upload requires a Case. This creates a circular dependency for applications whose required completeness depends on uploaded files.

### Case endpoint mismatch

The frontend calls `cases/{id}/status/` for evaluator status transitions. Django exposes `cases/{id}/update-status/` and accepts `POST`. These requests currently fail.

### Errors are represented as empty data

Evaluator data loading catches failures from Available Cases, My Cases, dashboard summary, and reports and substitutes empty values. Authentication failures, missing evaluator profiles, specialization mismatches, and server errors therefore look like valid empty queues.

### Prototype and backend state are mixed

Authenticated pages use the same `submissions`, notifications, marketplace, and other collections as prototype/sample data. Backend records are merged into mutable local objects and then persisted. This can retain stale records, duplicate records, or display locally-created state as if the backend confirmed it.

### Evaluator eligibility is not explained

Available Cases correctly requires an available `EvaluatorProfile` with a compatible specialization, but the frontend does not distinguish:

- no matching cases,
- no evaluator profile,
- evaluator marked unavailable,
- unsupported specialization,
- authorization failure.

## Selected Approach

Use a targeted integration repair rather than a frontend rewrite or broad backend compatibility layer.

The backend remains the source of truth. Existing API routes are used where they are correct. Compatibility aliases will be added only if an actively used frontend contract cannot safely be changed, not as the default solution.

The frontend retains its current visual structure and rendering functions. Changes will focus on request sequencing, endpoint names, backend response mapping, error states, and removal of local-success behavior from authenticated workflows.

## Backend Design

### Application submission

Keep `ApplicationSubmissionService.submit()` as the transactional owner of the submitted state and Case creation. It must remain idempotent, ensuring that repeated submission requests never create duplicate Cases.

Submission should return the application identifier, application code, Case identifier, Case number, and whether the Case was newly created.

### Required document ordering

Resolve the circular dependency without weakening authorization:

1. Create the application as a draft.
2. Ensure a Case exists in a controlled draft/pending intake state when document upload requires a Case reference.
3. Upload required files against that Case using the authenticated Applicant.
4. Run submission completeness validation.
5. Mark the application submitted only after validation passes.
6. Keep the same Case pending and available to matching Evaluators.

The implementation must prevent draft applications from appearing in Available Cases by retaining the existing `application__status="submitted"` filter.

If the existing architecture supports a smaller safe alternative, such as a dedicated application-scoped document upload, it may be used only if it requires fewer changes and preserves object-level access.

### Evaluator availability

`GET /api/cases/available/` continues to return only:

- submitted applications,
- pending cases,
- untaken cases,
- cases with no conflicting assignment,
- cases compatible with the Evaluator's available specialization.

The backend should return an actionable validation or permission response when the Evaluator has no profile or is unavailable, rather than silently returning an indistinguishable empty list.

### Take Case

`CaseWorkflowService.take_case()` remains transactional and uses row locking. It must continue to:

- reject non-Evaluators,
- reject already-taken Cases,
- enforce specialization,
- set `taken_by` and `assigned_evaluator`,
- set `is_taken = true`,
- set `taken_at`,
- set `status = under_review`,
- set `deadline = taken_at + 90 days`,
- create history, timeline, audit, and notification records.

### Supporting APIs

Backend changes outside the priority workflow will be limited to confirmed contract or permission defects in:

- authentication and password reset,
- documents and payment receipts,
- messages and notifications,
- admin reports and audit logs,
- inquiries, marketplace, and announcements.

## Frontend Design

### API helper and authentication

Continue using `apiRequest()` as the central JSON/FormData request helper. Authenticated requests must include `Authorization: Bearer <access token>`. A failed refresh must clear the session and redirect to the correct role login page.

Errors must retain HTTP status and backend detail so render functions can distinguish empty data from failed requests.

### Applicant submission sequence

`submitForm()` must not create a local successful submission if any required backend step fails.

The successful path will:

1. Create or update the backend draft application.
2. Upload required documents in the valid backend order.
3. Submit the application.
4. Confirm a backend Case ID and Case number were returned.
5. Reload applications/cases from the backend.
6. Render success using the backend reference.

On failure, the frontend will:

- remain on the form or confirmation boundary,
- display the backend error,
- avoid local submission insertion,
- avoid local audit/notification success entries,
- allow the Applicant to correct and retry.

### Evaluator Cases and My Cases

Available Cases and My Cases will be populated from their separate endpoints:

- `/api/cases/available/`
- `/api/cases/my-cases/`

The rendering layer may reuse current table components, but it must retain the queue source so Available Cases cannot accidentally contain owned cases and My Cases cannot contain untaken cases.

The Take Case action will use the backend Case ID, wait for success, reload both endpoint collections, then navigate to My Cases.

### Status updates

All evaluator status updates will call:

`POST /api/cases/{id}/update-status/`

The UI must update only after the backend confirms the transition.

### Empty and error states

Authenticated list pages will distinguish:

- loading,
- valid empty result,
- unauthorized or expired session,
- evaluator profile configuration issue,
- network/server failure.

The existing page layout and styling will be reused.

### Prototype state containment

Sample and local collections will not be broadly deleted in this repair. Instead, authenticated workflow loaders will replace their scoped data with backend results and will not insert fake fallback records.

Real API failures must never trigger sample data.

## Supporting Workflow Audit

After the priority workflow is repaired, inspect and fix only confirmed issues in:

- Applicant registration, OTP verification, login, and forgot password.
- Applicant document and payment receipt upload.
- Messaging conversation creation, message retrieval, message sending, and attachments.
- Notifications loading, mark-read, and clear.
- Admin reports and dashboard metrics.
- Admin audit log.
- Admin inquiry management.
- Admin marketplace listing operations.
- Admin announcements.

For each workflow, verify:

- route matches Django URLs,
- HTTP method matches the view action,
- Authorization is present when required,
- request fields match serializers,
- paginated responses are unwrapped,
- response fields map to current UI fields,
- backend failures do not mutate local success state.

## Testing Design

### Backend tests

Add or extend tests for:

- failed completeness does not submit the application,
- document-dependent submission ordering,
- submitted applications create exactly one Case,
- draft applications never appear in Available Cases,
- missing or unavailable evaluator profiles return an actionable response,
- specialization filtering,
- concurrent/already-taken Case rejection,
- deadline equals `taken_at + 90 days`,
- status update route and ownership enforcement.

### Frontend contract checks

Because the frontend has no existing JavaScript test runner, use focused static assertions where practical and run:

- `node --check static/js/app.js`
- searches that confirm obsolete endpoint strings are removed,
- manual browser workflow verification against the running Django server.

### Required verification

Run:

```powershell
python manage.py check
node --check static/js/app.js
python manage.py makemigrations --check --dry-run
python manage.py test tests
```

If model changes are required, explain them before running `makemigrations` or `migrate`.

Start the server and verify authenticated responses for:

- `GET /api/auth/me/`
- `POST /api/auth/login/`
- `GET /api/applications/`
- `POST /api/applications/`
- `GET /api/cases/available/`
- `GET /api/cases/my-cases/`
- `GET /api/audit-logs/`
- `GET /api/reports/summary-metrics/`
- `GET /api/marketplace/admin/listings/`

## Manual Acceptance Test

Use real user accounts supplied by the project owner or created through normal system administration. Do not create fake records merely to populate the UI.

1. Login as an Applicant.
2. Complete and submit an application.
3. Confirm the application is `submitted`.
4. Confirm exactly one pending untaken Case exists.
5. Login as a matching available Evaluator.
6. Open Cases and confirm the Case appears.
7. Take the Case.
8. Confirm it leaves Available Cases and appears in My Cases.
9. Confirm status is Under Review.
10. Confirm the deadline is exactly 90 days after `taken_at`.
11. Login as Admin.
12. Confirm Dashboard, Audit Log, Marketplace, Announcements, and Inquiry Management load backend data or honest empty states.

## Completion Criteria

The repair is complete when:

- backend and JavaScript checks pass,
- all Django tests pass,
- the priority workflow passes manually,
- authenticated UI pages do not claim success after failed backend requests,
- no dummy data was added,
- authentication and RBAC remain enabled,
- no permission checks were bypassed,
- remaining unsupported or unverified workflows are explicitly listed in the final report.

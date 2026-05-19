# The Creator's Bulwark Backend

Production-oriented Django REST backend for **The Creator's Bulwark: A Multi-Tiered Intellectual Property Management System for Palawan State University**.

This repository contains backend services only. It does not include frontend files, seed data, fake workflows, sample records, or prototype-only OTP behavior.

## Stack

- Django 5.2 LTS
- Django REST Framework
- PostgreSQL
- Simple JWT
- Python cryptography
- AES-256-GCM document and receipt encryption
- Custom encryption key management module

## Local Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set a real PostgreSQL database and a real `MASTER_KEY` in `.env` before using document, receipt, or key-management endpoints.

## Security Notes

- Passwords use Django's built-in password hashing.
- Login requires password verification followed by a real email OTP.
- OTP codes are hashed, expire after 5 minutes, are single-use, and are rate-limited.
- JWT access tokens expire after 15 minutes.
- Confidential documents and sensitive payment receipts are encrypted before storage.
- Raw encryption key material is never returned by APIs.
- Object-level access checks are enforced for applicant, evaluator, admin, and public flows.

## API Entry Points

All endpoints are mounted under `/api/`.

- `/api/auth/`
- `/api/applications/`
- `/api/cases/`
- `/api/documents/`
- `/api/payments/`
- `/api/messaging/`
- `/api/notifications/`
- `/api/audit-logs/`
- `/api/marketplace/`
- `/api/inquiries/`
- `/api/reports/`
- `/api/security-keys/`
- `/api/ipophl-email/`
- `/api/nlq/`

## No Seed Data

This backend intentionally ships with migrations only. Create real users and records through admin/API workflows.

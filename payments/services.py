import hashlib

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.audit import create_audit_log
from core.file_validators import validate_payment_receipt_file
from core.notifications import create_notification
from security_keys.services import AESGCMDocumentCipher

from .models import FeeAssessment, Payment


class PaymentService:
    @staticmethod
    def upload_receipt(*, uploaded_file, applicant, assessment, amount_paid, payment_method, receipt_no="", payment_date=None, request=None):
        if not isinstance(assessment, FeeAssessment):
            try:
                assessment = FeeAssessment.objects.select_related("case", "case__applicant", "application").get(pk=assessment)
            except ObjectDoesNotExist as exc:
                raise ValidationError("Payment assessment was not found.") from exc
        case = assessment.case
        if applicant.role != "applicant" or case.applicant_id != applicant.id:
            raise PermissionDenied("You can upload payment receipts only for your own case.")
        mime_type = validate_payment_receipt_file(uploaded_file)
        plaintext = uploaded_file.read()
        key, nonce, ciphertext = AESGCMDocumentCipher.encrypt(plaintext)
        checksum = hashlib.sha256(ciphertext).hexdigest()
        original_filename = get_valid_filename(uploaded_file.name)
        payment = Payment.objects.create(
            assessment=assessment,
            case=case,
            applicant=case.applicant,
            amount_paid=amount_paid,
            payment_method=payment_method,
            receipt_no=receipt_no,
            payment_date=payment_date,
            original_filename=original_filename,
            file_size=uploaded_file.size,
            mime_type=mime_type,
            encryption_key=key,
            nonce=nonce,
            checksum=checksum,
        )
        payment.encrypted_receipt_file.save(f"{checksum}-{original_filename}", ContentFile(ciphertext), save=True)
        create_audit_log(request, applicant, "payment.receipt_uploaded", payment.original_filename, "Encrypted payment receipt uploaded.", related_case=case)
        return payment

    @staticmethod
    def decrypt_receipt(payment, user, request=None):
        allowed = user.role == "admin" or payment.applicant_id == user.id or payment.case.taken_by_id == user.id
        if not allowed:
            raise PermissionDenied("You do not have permission to access this payment receipt.")
        with payment.encrypted_receipt_file.open("rb") as encrypted_file:
            ciphertext = encrypted_file.read()
        create_audit_log(request, user, "payment.receipt_viewed", payment.original_filename, "Encrypted receipt decrypted for authorized access.", related_case=payment.case)
        return AESGCMDocumentCipher.decrypt(ciphertext, payment.encryption_key, payment.nonce)

    @staticmethod
    @transaction.atomic
    def verify(payment, admin_user, remarks="", request=None):
        if admin_user.role != "admin":
            raise PermissionDenied("Only admins can verify payment receipts.")
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        payment.payment_status = Payment.Status.VERIFIED
        payment.verified_by = admin_user
        payment.verified_at = timezone.now()
        payment.remarks = remarks
        payment.save(update_fields=["payment_status", "verified_by", "verified_at", "remarks"])

        assessment = FeeAssessment.objects.select_for_update().get(pk=payment.assessment_id)
        assessment.status = FeeAssessment.Status.PAID
        assessment.save(update_fields=["status", "updated_at"])

        create_notification(payment.applicant, "Payment Receipt Verified", "Your payment receipt has been verified.", "payment", payment.case, "applicant")
        create_audit_log(request, admin_user, "payment.verified", payment.original_filename, remarks, related_case=payment.case)
        return payment

    @staticmethod
    @transaction.atomic
    def reject(payment, admin_user, remarks="", request=None):
        if admin_user.role != "admin":
            raise PermissionDenied("Only admins can reject payment receipts.")
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        payment.payment_status = Payment.Status.REJECTED
        payment.verified_by = admin_user
        payment.verified_at = timezone.now()
        payment.remarks = remarks
        payment.save(update_fields=["payment_status", "verified_by", "verified_at", "remarks"])
        create_notification(payment.applicant, "Payment Receipt Rejected", "Your payment receipt was rejected. Please review the remarks.", "payment", payment.case, "applicant")
        create_audit_log(request, admin_user, "payment.rejected", payment.original_filename, remarks, related_case=payment.case)
        return payment

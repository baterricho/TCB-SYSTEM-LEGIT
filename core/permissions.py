"""
Shared permission classes for RBAC enforcement.
Applied across all API endpoints.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allows access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsEvaluator(BasePermission):
    """Allows access only to evaluator users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "evaluator"
        )


class IsApplicant(BasePermission):
    """Allows access only to applicant users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "applicant"
        )


class IsAdminOrEvaluator(BasePermission):
    """Allows access to admin or evaluator users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "evaluator")
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allows access if the user is the owner
    of the object or an admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        # Check common ownership fields
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsOwnerOrAdminOrAssignedEvaluator(BasePermission):
    """
    Object-level permission for IP applications:
    owner, admin, or the assigned evaluator can access.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True
        if hasattr(obj, "assigned_evaluator") and obj.assigned_evaluator == request.user:
            return True
        return False

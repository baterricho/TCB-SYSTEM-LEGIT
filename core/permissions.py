from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.role == "admin" or user.is_staff or user.is_superuser))


class IsApplicant(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "applicant")


class IsEvaluator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "evaluator")


class IsOwnerApplicant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        applicant = getattr(obj, "applicant", None)
        if applicant == request.user:
            return True
        return getattr(applicant, "user", None) == request.user


class IsCaseEvaluator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        case = getattr(obj, "case", obj)
        return bool(case and case.taken_by_id == request.user.id)


class IsCaseParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        case = getattr(obj, "case", obj)
        if not case:
            return False
        return case.applicant_id == request.user.id or case.taken_by_id == request.user.id


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class CanAccessEncryptedDocument(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == "admin":
            return True
        case = getattr(obj, "case", None)
        if getattr(obj, "uploaded_by_id", None) == user.id:
            return True
        if case and case.applicant_id == user.id:
            return True
        return bool(case and case.taken_by_id == user.id)

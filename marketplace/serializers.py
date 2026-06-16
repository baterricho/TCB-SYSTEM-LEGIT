from rest_framework import serializers

from cases.models import Case
from .models import Bookmark, IPRecord, MarketListing


class IPRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPRecord
        fields = ("id", "case", "application", "encryption_key", "certification_date", "is_certified", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class MarketplaceListingSerializer(serializers.ModelSerializer):
    record = serializers.PrimaryKeyRelatedField(queryset=IPRecord.objects.all(), required=False)
    bookmark_count = serializers.IntegerField(read_only=True, default=0)
    created_by = serializers.IntegerField(source="admin_id", read_only=True)
    listing_id = serializers.CharField(source="listing_code", read_only=True)
    case_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = MarketListing
        fields = (
            "id", "listing_id", "listing_code", "record", "admin", "title", "ip_type", "inventor_name", "short_description",
            "full_description", "category", "availability_status", "image", "status", "created_by",
            "is_active", "created_at", "updated_at", "bookmark_count", "case_number",
        )
        read_only_fields = ("id", "listing_id", "listing_code", "admin", "created_by", "created_at", "updated_at", "bookmark_count")

    def validate(self, attrs):
        case_number = attrs.pop("case_number", "")
        if case_number and not attrs.get("record"):
            try:
                case = Case.objects.get(case_number__iexact=case_number)
                attrs["record"] = IPRecord.objects.get(case=case)
            except Case.DoesNotExist as exc:
                raise serializers.ValidationError({"case_number": "No case exists with this case number."}) from exc
            except IPRecord.DoesNotExist as exc:
                raise serializers.ValidationError({"case_number": "No IP record exists for this case number."}) from exc
        if self.instance is None and not attrs.get("record"):
            raise serializers.ValidationError({"record": "A marketplace listing must be connected to an IP record."})
        return attrs

    def validate_image(self, value):
        if value:
            if value.name.lower().endswith(".svg"):
                raise serializers.ValidationError("SVG files are not allowed.")
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file size exceeds the 5 MB limit.")
            import magic
            value.seek(0)
            mime = magic.from_buffer(value.read(2048), mime=True)
            value.seek(0)
            if not mime.startswith("image/") or mime not in {"image/jpeg", "image/png", "image/gif"}:
                raise serializers.ValidationError("Unsupported file type. Only JPG, JPEG, and PNG images are allowed.")
        return value


class BookmarkSerializer(serializers.ModelSerializer):
    listing = MarketplaceListingSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ("id", "listing", "created_at")
        read_only_fields = fields


class BookmarkCreateSerializer(serializers.Serializer):
    listing = serializers.IntegerField()

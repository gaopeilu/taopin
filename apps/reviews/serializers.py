from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'sku_id', 'spu_id', 'order_no', 'rating', 'content', 'images', 'is_anonymous', 'created_at', 'username']
        read_only_fields = ['id', 'created_at']

    def get_username(self, obj):
        if obj.is_anonymous:
            return obj.user.username[:3] + '***'
        return obj.user.username


class CreateReviewSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField()
    spu_id = serializers.IntegerField()
    order_no = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')
    rating = serializers.IntegerField(min_value=1, max_value=5, default=5)
    content = serializers.CharField(required=False, allow_blank=True, default='')
    images = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    is_anonymous = serializers.BooleanField(default=False)

from rest_framework import serializers
from .models import Coupon, CouponRecord


class CouponSerializer(serializers.ModelSerializer):
    remaining = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = ['id', 'name', 'coupon_type', 'value', 'min_amount', 'total_count',
                  'claimed_count', 'remaining', 'start_time', 'end_time', 'is_active']


class CouponRecordSerializer(serializers.ModelSerializer):
    coupon_name = serializers.SerializerMethodField()
    coupon_type = serializers.SerializerMethodField()
    coupon_value = serializers.SerializerMethodField()
    min_amount = serializers.SerializerMethodField()

    class Meta:
        model = CouponRecord
        fields = ['id', 'coupon', 'status', 'order_no', 'claimed_at', 'used_at',
                  'coupon_name', 'coupon_type', 'coupon_value', 'min_amount']

    def get_coupon_name(self, obj):
        return obj.coupon.name if obj.coupon else ''

    def get_coupon_type(self, obj):
        return obj.coupon.coupon_type if obj.coupon else ''

    def get_coupon_value(self, obj):
        return str(obj.coupon.value) if obj.coupon else '0'

    def get_min_amount(self, obj):
        return str(obj.coupon.min_amount) if obj.coupon else '0'

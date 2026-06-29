from django.contrib import admin
from .models import Coupon, CouponRecord


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['name', 'coupon_type', 'value', 'min_amount', 'total_count', 'claimed_count', 'is_active', 'start_time', 'end_time']
    list_filter = ['coupon_type', 'is_active']
    search_fields = ['name']


@admin.register(CouponRecord)
class CouponRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'coupon', 'status', 'order_no', 'claimed_at', 'used_at']
    list_filter = ['status']
    search_fields = ['user__username', 'order_no']

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['pay_no', 'order_no', 'amount', 'pay_method', 'status', 'pay_time']
    list_filter = ['status', 'pay_method']
    search_fields = ['pay_no', 'order_no']
    readonly_fields = ['pay_no', 'created_at']

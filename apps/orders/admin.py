from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['sku_id', 'spu_id', 'goods_name', 'sku_name', 'price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'status', 'total_amount', 'pay_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_no', 'receiver_name', 'receiver_phone']
    readonly_fields = ['order_no', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

import re
from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'sku_id', 'spu_id', 'goods_name', 'goods_image', 'sku_name', 'price', 'quantity', 'subtotal']


class OrderItemInputSerializer(serializers.Serializer):
    """[修复11] 订单商品输入校验"""
    sku_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=999)
    goods_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    goods_image = serializers.CharField(max_length=500, required=False, allow_blank=True)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'total_amount', 'pay_amount', 'freight_fee', 'status',
                  'receiver_name', 'receiver_phone', 'receiver_address',
                  'pay_method', 'pay_time', 'ship_time', 'express_no', 'remark',
                  'created_at', 'updated_at', 'items']
        read_only_fields = ['order_no', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    """创建订单"""
    address_id = serializers.IntegerField(required=False)
    coupon_id = serializers.IntegerField(required=False)  # 优惠券ID（可选）
    receiver_name = serializers.CharField(max_length=50)
    receiver_phone = serializers.CharField(max_length=11, min_length=11)
    receiver_address = serializers.CharField(max_length=500)
    items = OrderItemInputSerializer(many=True)
    remark = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')

    def validate_receiver_phone(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('请输入正确的11位手机号')
        return value


class PayOrderSerializer(serializers.Serializer):
    """支付订单"""
    pay_method = serializers.CharField(max_length=20, default='wechat')

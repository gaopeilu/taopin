from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'pay_no', 'order_no', 'amount', 'pay_method', 'status', 'trade_no', 'pay_time', 'created_at']
        read_only_fields = ['id', 'pay_no', 'created_at']


class CreatePaymentSerializer(serializers.Serializer):
    """发起支付"""
    order_no = serializers.CharField(max_length=64)
    pay_method = serializers.CharField(max_length=20, default='wechat')


class MockPaySerializer(serializers.Serializer):
    """模拟支付"""
    pay_no = serializers.CharField(max_length=64)

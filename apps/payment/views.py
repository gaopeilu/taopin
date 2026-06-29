import uuid
import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView

logger = logging.getLogger(__name__)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer, MockPaySerializer
from apps.orders.models import Order


def generate_pay_no():
    """生成支付号（UUID保证唯一性）"""
    return f'PAY{uuid.uuid4().hex[:16].upper()}'


class CreatePaymentView(APIView):
    """发起支付"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = CreatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order_no = ser.validated_data['order_no']
        pay_method = ser.validated_data.get('pay_method', 'wechat')

        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)

        if order.status != 'pending':
            return Response({'code': 400, 'message': '订单状态不允许支付'}, status=400)

        # 创建支付记录
        payment = Payment.objects.create(
            pay_no=generate_pay_no(),
            order_no=order_no,
            amount=order.pay_amount,
            pay_method=pay_method,
        )

        return Response({'code': 200, 'message': '支付创建成功', 'data': PaymentSerializer(payment).data})


class MockPayView(APIView):
    """模拟支付（开发环境）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = MockPaySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pay_no = ser.validated_data['pay_no']

        try:
            payment = Payment.objects.get(pay_no=pay_no)
        except Payment.DoesNotExist:
            return Response({'code': 404, 'message': '支付记录不存在'}, status=404)

        if payment.status != 'pending':
            return Response({'code': 400, 'message': '支付状态不允许'}, status=400)

        # [修复2] 使用事务保证支付记录和订单状态一致性
        with transaction.atomic():
            payment.status = 'success'
            payment.trade_no = f'TN{uuid.uuid4().hex[:16].upper()}'
            payment.pay_time = timezone.now()
            payment.save()

            try:
                order = Order.objects.get(order_no=payment.order_no)
                order.status = 'paid'
                order.pay_method = payment.pay_method
                order.pay_time = payment.pay_time
                order.trade_no = payment.trade_no
                order.save()
            except Order.DoesNotExist:
                logger.error(f'支付成功但订单不存在: pay_no={payment.pay_no}, order_no={payment.order_no}')
                return Response({'code': 500, 'message': '支付成功但订单异常，请联系客服'}, status=500)

        return Response({'code': 200, 'message': '支付成功', 'data': PaymentSerializer(payment).data})


class PaymentStatusView(APIView):
    """查询支付状态"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pay_no):
        try:
            payment = Payment.objects.get(pay_no=pay_no)
        except Payment.DoesNotExist:
            return Response({'code': 404, 'message': '支付记录不存在'}, status=404)

        return Response({'code': 200, 'data': PaymentSerializer(payment).data})


class PaymentCallbackView(APIView):
    """支付回调（内部接口）"""
    # [Bug2] 添加签名验证，不再完全开放
    permission_classes = []  # 内部接口，通过签名验证而非Token认证

    def post(self, request):
        # [Bug2] 签名验证
        callback_secret = request.headers.get('X-Callback-Secret', '')
        from django.conf import settings
        expected_secret = getattr(settings, 'PAYMENT_CALLBACK_SECRET', 'dianshang_callback_secret_2026')
        if callback_secret != expected_secret:
            return Response({'code': 403, 'message': '回调签名验证失败'}, status=403)

        pay_no = request.data.get('pay_no')
        trade_no = request.data.get('trade_no', '')
        status_val = request.data.get('status', 'success')

        # [Bug3] 只接受合法的状态值
        if status_val not in ('success', 'failed'):
            return Response({'code': 400, 'message': '无效的支付状态'}, status=400)

        try:
            payment = Payment.objects.get(pay_no=pay_no)
        except Payment.DoesNotExist:
            return Response({'code': 404, 'message': '支付记录不存在'}, status=404)

        # [修复2] 事务保护
        with transaction.atomic():
            payment.status = status_val
            payment.trade_no = trade_no
            if status_val == 'success':
                payment.pay_time = timezone.now()
            payment.save()

            if status_val == 'success':
                try:
                    order = Order.objects.get(order_no=payment.order_no)
                    order.status = 'paid'
                    order.pay_method = payment.pay_method
                    order.pay_time = payment.pay_time
                    order.trade_no = trade_no
                    order.save()
                except Order.DoesNotExist:
                    logger.error(f'回调成功但订单不存在: pay_no={payment.pay_no}')

        return Response({'code': 200, 'message': '回调处理成功'})

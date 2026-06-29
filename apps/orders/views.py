import uuid
import time
import random
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer, PayOrderSerializer
from apps.goods.models import GoodsSKU


def generate_order_no():
    """生成订单号（UUID保证唯一性）"""
    return f'ORD{uuid.uuid4().hex[:16].upper()}'


class OrderListCreateView(generics.ListCreateAPIView):
    """订单列表 & 创建"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status')
        view_type = self.request.query_params.get('type', '')  # type=seller 查看作为商家的订单

        if user.role == 'seller' and view_type == 'seller':
            # 商家查看包含自己商品的订单
            from apps.goods.models import GoodsSPU
            my_spu_ids = GoodsSPU.objects.filter(seller=user).values_list('id', flat=True)
            my_sku_ids = GoodsSKU.objects.filter(spu_id__in=my_spu_ids).values_list('id', flat=True)
            order_ids = OrderItem.objects.filter(sku_id__in=my_sku_ids).values_list('order_id', flat=True)
            qs = Order.objects.filter(id__in=order_ids).prefetch_related('items')
        else:
            # 普通用户查看自己的订单
            qs = Order.objects.filter(user=user).prefetch_related('items')

        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        ser = CreateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        items_data = data['items']
        if not items_data:
            return Response({'code': 400, 'message': '商品列表不能为空'}, status=400)

        # 优惠券预校验
        coupon_id = data.get('coupon_id')
        coupon_record = None
        discount = 0
        if coupon_id:
            from apps.marketing.models import CouponRecord
            try:
                coupon_record = CouponRecord.objects.select_related('coupon').get(
                    id=coupon_id, user=request.user, status='unused'
                )
                coupon = coupon_record.coupon
                if not coupon.is_active:
                    return Response({'code': 400, 'message': '优惠券已失效'}, status=400)
                from django.utils import timezone
                now = timezone.now()
                if now < coupon.start_time or now > coupon.end_time:
                    return Response({'code': 400, 'message': '优惠券不在有效期内'}, status=400)
            except CouponRecord.DoesNotExist:
                return Response({'code': 400, 'message': '优惠券不存在或已使用'}, status=400)

        # [Bug5] 使用事务 + 行锁防止超卖
        with transaction.atomic():
            total = 0
            order_items = []
            for item in items_data:
                sku_id = item.get('sku_id')
                quantity = int(item.get('quantity', 1))
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id, is_active=True)
                except GoodsSKU.DoesNotExist:
                    return Response({'code': 400, 'message': f'SKU {sku_id} 不存在或已下架'}, status=400)
                if sku.spu.is_deleted or not sku.spu.is_on_sale:
                    return Response({'code': 400, 'message': f'商品「{sku.spu.name}」已下架或删除'}, status=400)
                if sku.stock < quantity:
                    return Response({'code': 400, 'message': f'「{sku.name}」库存不足，剩余{sku.stock}件'}, status=400)
                subtotal = sku.price * quantity
                total += subtotal
                order_items.append({
                    'sku': sku,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'goods_name': item.get('goods_name', sku.spu.name),
                    'goods_image': item.get('goods_image', sku.spu.main_image or ''),
                    'sku_name': sku.name,
                })

            # 计算优惠券抵扣（全部用Decimal，避免类型错误）
            from decimal import Decimal
            pay_amount = total
            discount = Decimal('0')
            if coupon_record:
                coupon = coupon_record.coupon
                if total < coupon.min_amount:
                    return Response({'code': 400, 'message': f'未满最低消费 ¥{coupon.min_amount}'}, status=400)
                if coupon.coupon_type == 'minus':
                    discount = coupon.value
                    pay_amount = max(Decimal('0'), total - discount)
                elif coupon.coupon_type == 'discount':
                    pay_amount = (total * coupon.value / Decimal('10')).quantize(Decimal('0.01'))
                    discount = total - pay_amount
                elif coupon.coupon_type == 'newcomer':
                    discount = coupon.value
                    pay_amount = max(Decimal('0'), total - discount)

            # 创建订单
            order = Order.objects.create(
                user=request.user,
                order_no=generate_order_no(),
                total_amount=total,
                pay_amount=pay_amount,
                receiver_name=data['receiver_name'],
                receiver_phone=data['receiver_phone'],
                receiver_address=data['receiver_address'],
                remark=data.get('remark', ''),
            )

            # 创建订单项 & 扣减库存
            for oi in order_items:
                OrderItem.objects.create(
                    order=order,
                    sku_id=oi['sku'].id,
                    spu_id=oi['sku'].spu_id,
                    goods_name=oi['goods_name'],
                    goods_image=oi['goods_image'],
                    sku_name=oi['sku_name'],
                    price=oi['sku'].price,
                    quantity=oi['quantity'],
                    subtotal=oi['subtotal'],
                )
                oi['sku'].stock -= oi['quantity']
                oi['sku'].sales += oi['quantity']
                oi['sku'].save()
                oi['sku'].spu.sales += oi['quantity']
                oi['sku'].spu.save()

            # 核销优惠券
            if coupon_record:
                coupon_record.status = 'used'
                coupon_record.order_no = order.order_no
                coupon_record.used_at = timezone.now()
                coupon_record.save()

        return Response({'code': 200, 'message': '下单成功', 'data': OrderSerializer(order).data}, status=201)


class OrderDetailView(generics.RetrieveDestroyAPIView):
    """订单详情/删除"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = 'order_no'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status not in ('cancelled', 'completed'):
            return Response({'code': 400, 'message': '当前状态不允许删除'}, status=400)
        # [修复8] 软删除，保留审计记录
        order.is_deleted = True
        order.save(update_fields=['is_deleted'])
        return Response({'code': 200, 'message': '订单已删除'})


class OrderPayView(APIView):
    """模拟支付"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        if order.status != 'pending':
            return Response({'code': 400, 'message': '订单状态不允许支付'}, status=400)

        ser = PayOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        pay_method = ser.validated_data.get('pay_method', 'wechat')
        trade_no = f'TN{uuid.uuid4().hex[:16].upper()}'
        pay_time = timezone.now()

        order.status = 'paid'
        order.pay_method = pay_method
        order.pay_time = pay_time
        order.trade_no = trade_no
        order.save()

        # [Bug10/18] 同步创建Payment记录，统一支付流水
        from apps.payment.models import Payment
        from apps.payment.views import generate_pay_no
        Payment.objects.create(
            pay_no=generate_pay_no(),
            order_no=order.order_no,
            amount=order.pay_amount,
            pay_method=pay_method,
            status='success',
            trade_no=trade_no,
            pay_time=pay_time,
        )

        return Response({'code': 200, 'message': '支付成功', 'data': OrderSerializer(order).data})


class OrderCancelView(APIView):
    """取消订单"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        if order.status not in ('pending',):
            return Response({'code': 400, 'message': '当前状态不允许取消'}, status=400)

        # [Bug6] 恢复库存，增加SPU存在性保护
        for item in order.items.all():
            try:
                sku = GoodsSKU.objects.get(id=item.sku_id)
                sku.stock += item.quantity
                sku.sales = max(0, sku.sales - item.quantity)
                sku.save()
                try:
                    spu = sku.spu
                    spu.sales = max(0, spu.sales - item.quantity)
                    spu.save()
                except Exception:
                    pass  # SPU可能已被删除
            except GoodsSKU.DoesNotExist:
                pass  # SKU已被删除，跳过

        order.status = 'cancelled'
        order.save()
        return Response({'code': 200, 'message': '订单已取消'})


class OrderShipView(APIView):
    """商家发货"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        if order.status != 'paid':
            return Response({'code': 400, 'message': '订单状态不允许发货'}, status=400)

        # [Bug1] 验证当前用户是该订单商品的卖家
        if request.user.role != 'seller':
            return Response({'code': 403, 'message': '只有商家才能发货'}, status=403)
        order_item_spus = OrderItem.objects.filter(order=order).values_list('spu_id', flat=True)
        from apps.goods.models import GoodsSPU
        seller_owns = GoodsSPU.objects.filter(
            id__in=order_item_spus, seller=request.user
        ).exists()
        if not seller_owns:
            return Response({'code': 403, 'message': '您不是该订单商品的卖家'}, status=403)

        order.status = 'shipped'
        order.ship_time = timezone.now()
        order.express_no = request.data.get('express_no', '')
        order.save()
        return Response({'code': 200, 'message': '发货成功', 'data': OrderSerializer(order).data})


class OrderCompleteView(APIView):
    """确认收货"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        if order.status != 'shipped':
            return Response({'code': 400, 'message': '订单状态不允许确认收货'}, status=400)

        order.status = 'completed'
        order.save()
        return Response({'code': 200, 'message': '已确认收货'})


class OrderRefundView(APIView):
    """申请退款"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '订单不存在'}, status=404)
        if order.status not in ('paid', 'shipped', 'completed'):
            return Response({'code': 400, 'message': '当前状态不允许申请退款'}, status=400)

        order.status = 'refund'
        order.save()
        return Response({'code': 200, 'message': '退款申请已提交', 'data': OrderSerializer(order).data})


class RefundDetailView(APIView):
    """退款详情"""
    permission_classes = [IsAuthenticated]

    def get(self, request, refund_no):
        # refund_no 实际是 order_no
        try:
            order = Order.objects.get(order_no=refund_no, user=request.user)
        except Order.DoesNotExist:
            return Response({'code': 404, 'message': '退款记录不存在'}, status=404)
        if order.status != 'refund':
            return Response({'code': 400, 'message': '该订单非退款状态'}, status=400)
        return Response({
            'code': 200,
            'data': {
                'refund_no': order.order_no,
                'order_no': order.order_no,
                'amount': str(order.pay_amount),
                'status': 'pending',
                'reason': '用户申请退款',
                'created_at': order.updated_at.isoformat() if order.updated_at else None,
            }
        })



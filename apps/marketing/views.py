from django.db import transaction, IntegrityError
from django.db.models import F
from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Coupon, CouponRecord
from .serializers import CouponSerializer, CouponRecordSerializer


class CouponListView(generics.ListAPIView):
    """可领取的优惠券列表（返回当前用户的领取状态）"""
    serializer_class = CouponSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        now = timezone.now()
        return Coupon.objects.filter(is_active=True, start_time__lte=now, end_time__gte=now)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # 如果用户已登录，标记每张券的领取状态
        if request.user.is_authenticated:
            claimed_ids = set(
                CouponRecord.objects.filter(user=request.user)
                .values_list('coupon_id', flat=True)
            )
            for item in data:
                item['is_claimed'] = item['id'] in claimed_ids

        return Response({'code': 200, 'data': data})


class CouponClaimView(APIView):
    """领取优惠券"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            coupon = Coupon.objects.get(id=pk, is_active=True)
        except Coupon.DoesNotExist:
            return Response({'code': 404, 'message': '优惠券不存在'}, status=404)

        now = timezone.now()
        if now < coupon.start_time or now > coupon.end_time:
            return Response({'code': 400, 'message': '优惠券不在领取时间范围内'}, status=400)

        # [修复1] 使用事务 + F()表达式防止超发 + unique_together防重复
        try:
            with transaction.atomic():
                # 原子扣减库存：只有claimed_count < total_count才能成功
                updated = Coupon.objects.filter(
                    id=pk,
                    claimed_count__lt=F('total_count')
                ).update(claimed_count=F('claimed_count') + 1)
                if not updated:
                    return Response({'code': 400, 'message': '优惠券已领完'}, status=400)

                # 创建领取记录（unique_together约束防重复）
                CouponRecord.objects.create(user=request.user, coupon=coupon)
        except IntegrityError:
            return Response({'code': 400, 'message': '您已领取过该优惠券'}, status=400)

        return Response({'code': 200, 'message': '领取成功'})


class MyCouponListView(generics.ListAPIView):
    """我的优惠券"""
    serializer_class = CouponRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        status = self.request.query_params.get('status')
        qs = CouponRecord.objects.filter(user=self.request.user).select_related('coupon')
        if status:
            qs = qs.filter(status=status)
        return qs

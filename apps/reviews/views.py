from django.db.models import F
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Review, ReviewLike
from .serializers import ReviewSerializer, CreateReviewSerializer


class ReviewListView(generics.ListAPIView):
    """商品评价列表（公开）"""
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        spu_id = self.request.query_params.get('spu_id')
        if spu_id:
            return Review.objects.filter(spu_id=spu_id).select_related('user')
        return Review.objects.none()


class ReviewCreateView(generics.CreateAPIView):
    """提交评价"""
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = CreateReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        # [修复4] 防止重复评价
        if Review.objects.filter(user=request.user, sku_id=d['sku_id'], order_no=d.get('order_no', '')).exists():
            return Response({'code': 400, 'message': '您已评价过该商品'}, status=400)
        review = Review.objects.create(
            user=request.user,
            sku_id=d['sku_id'],
            spu_id=d['spu_id'],
            order_no=d.get('order_no', ''),
            rating=d['rating'],
            content=d.get('content', ''),
            images=d.get('images', []),
            is_anonymous=d.get('is_anonymous', False),
        )
        return Response({'code': 200, 'message': '评价成功', 'data': ReviewSerializer(review).data}, status=201)


class MyReviewListView(generics.ListAPIView):
    """我的评价"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).select_related('user')


class ReviewLikeView(APIView):
    """评价点赞"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response({'code': 404, 'message': '评价不存在'}, status=404)
        like, created = ReviewLike.objects.get_or_create(review=review, user=request.user)
        if not created:
            return Response({'code': 400, 'message': '您已点赞过该评价'}, status=400)
        # [修复5] 使用F()表达式原子递增
        Review.objects.filter(id=pk).update(like_count=F('like_count') + 1)
        review.refresh_from_db()
        return Response({'code': 200, 'message': '点赞成功', 'data': {'like_count': review.like_count}})

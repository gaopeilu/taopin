from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import SearchHistory
from apps.goods.models import GoodsSPU


class SearchHistoryListView(generics.ListAPIView):
    """搜索历史列表"""
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        history = SearchHistory.objects.filter(user=request.user)[:20]
        data = [{'id': h.id, 'keyword': h.keyword, 'created_at': h.created_at} for h in history]
        return Response({'code': 200, 'data': data})


class SearchHistoryClearView(APIView):
    """清空搜索历史"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        SearchHistory.objects.filter(user=request.user).delete()
        return Response({'code': 200, 'message': '已清空'})


class SearchSuggestView(APIView):
    """搜索建议"""
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q or len(q) < 1:
            return Response({'code': 200, 'data': []})
        # [修复7] 已登录用户记录搜索历史
        if request.user.is_authenticated:
            SearchHistory.objects.update_or_create(
                user=request.user, keyword=q,
                defaults={}  # 更新created_at
            )
        # 从商品名称中搜索建议（去重用distinct）
        suggestions = list(
            GoodsSPU.objects.filter(name__icontains=q, is_deleted=False, is_on_sale=True)
            .values_list('name', flat=True).distinct()[:10]
        )
        return Response({'code': 200, 'data': suggestions})

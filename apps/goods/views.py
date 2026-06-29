"""
商品模块的视图

包含：
1. CategoryViewSet - 分类视图（树形结构）
2. BrandViewSet - 品牌视图
3. GoodsSPUViewSet - SPU视图
4. GoodsSKUViewSet - SKU视图
"""
import os
import uuid
from django.db.models import Q, Min, Max
from django.core.cache import cache
from django.conf import settings as django_settings
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from utils.permissions import IsSellerOrReadOnly
from .models import Category, Brand, GoodsSPU, GoodsSKU, ProductImage
from .serializers import (
    CategorySerializer, BrandSerializer,
    GoodsSPUListSerializer, GoodsSPUDetailSerializer,
    GoodsSPUCreateSerializer, GoodsSKUSerializer,
    ProductImageSerializer
)


# ==================== 分类视图 ====================
class CategoryViewSet(viewsets.ModelViewSet):
    """
    分类视图集

    提供：
    - GET /api/v1/goods/categories/ - 获取分类树
    - POST /api/v1/goods/categories/ - 创建分类
    - GET /api/v1/goods/categories/{id}/ - 分类详情
    - PUT /api/v1/goods/categories/{id}/ - 更新分类
    - DELETE /api/v1/goods/categories/{id}/ - 删除分类
    - GET /api/v1/goods/categories/tree/ - 完整分类树
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsSellerOrReadOnly]

    # [修复6] perform_create参数名应为serializer
    def perform_create(self, serializer):
        super().perform_create(serializer)
        cache.delete('category_tree')

    def perform_update(self, serializer):
        super().perform_update(serializer)
        cache.delete('category_tree')

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.delete('category_tree')

    def get_queryset(self):
        """只返回顶级分类（parent=None）"""
        queryset = super().get_queryset()
        # 如果请求参数中有 parent，则返回指定分类的子分类
        parent = self.request.query_params.get('parent', None)
        if parent is not None:
            queryset = queryset.filter(parent_id=parent)
        else:
            # 默认只返回顶级分类
            queryset = queryset.filter(parent__isnull=True)
        return queryset

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        获取完整分类树（带Redis缓存，600秒过期）
        GET /api/v1/goods/categories/tree/
        """
        cache_key = 'category_tree'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        categories = Category.objects.filter(
            is_active=True,
            parent__isnull=True
        )
        serializer = self.get_serializer(categories, many=True)
        cache.set(cache_key, serializer.data, 600)  # 缓存10分钟
        return Response(serializer.data)


# ==================== 品牌视图 ====================
class BrandViewSet(viewsets.ModelViewSet):
    """
    品牌视图集

    提供：
    - GET /api/v1/goods/brands/ - 品牌列表
    - POST /api/v1/goods/brands/ - 创建品牌
    - GET /api/v1/goods/brands/{id}/ - 品牌详情
    - PUT /api/v1/goods/brands/{id}/ - 更新品牌
    - DELETE /api/v1/goods/brands/{id}/ - 删除品牌
    """
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['sort_order', 'name']
    permission_classes = [IsSellerOrReadOnly]

    def get_queryset(self):
        """支持按首字母筛选"""
        queryset = super().get_queryset()
        letter = self.request.query_params.get('letter', None)
        if letter:
            queryset = queryset.filter(first_letter=letter.upper())
        return queryset


# ==================== 商品SPU视图 ====================
class GoodsSPUViewSet(viewsets.ModelViewSet):
    """
    商品SPU视图集

    提供：
    - GET /api/v1/goods/spus/ - 商品列表
    - POST /api/v1/goods/spus/ - 创建商品
    - GET /api/v1/goods/spus/{id}/ - 商品详情
    - PUT /api/v1/goods/spus/{id}/ - 更新商品
    - DELETE /api/v1/goods/spus/{id}/ - 删除商品
    - GET /api/v1/goods/spus/hot/ - 热销商品
    - GET /api/v1/goods/spus/search/ - 商品搜索
    - POST /api/v1/goods/spus/{id}/images/ - 上传商品图片
    - GET /api/v1/goods/spus/{id}/images/ - 获取商品图片
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'subtitle', 'category__name', 'category__parent__name', 'brand__name']
    ordering_fields = ['sales', 'created_at']
    permission_classes = [IsSellerOrReadOnly]

    def get_queryset(self):
        """默认不返回已删除的商品，支持分类筛选包含子分类，支持商家筛选，支持上下架筛选"""
        queryset = GoodsSPU.objects.filter(is_deleted=False).annotate(
            min_price=Min('skus__price'),
            max_price=Max('skus__price'),
        )

        # 商家筛选：seller=me 只返回当前商家的商品
        seller = self.request.query_params.get('seller', None)
        if seller == 'me':
            if self.request.user.is_authenticated and self.request.user.role == 'seller':
                queryset = queryset.filter(seller=self.request.user)
            else:
                queryset = queryset.none()
        elif seller:
            queryset = queryset.filter(seller_id=seller)

        # 上下架筛选
        is_on_sale = self.request.query_params.get('is_on_sale', None)
        if is_on_sale is not None:
            if is_on_sale.lower() == 'true':
                queryset = queryset.filter(is_on_sale=True)
            elif is_on_sale.lower() == 'false':
                queryset = queryset.filter(is_on_sale=False)

        # 获取分类筛选参数
        category_id = self.request.query_params.get('category', None)
        if category_id:
            # [Bug7] 检查是否是一级分类
            try:
                category = Category.objects.get(id=category_id)
                if category.parent is None:
                    # 一级分类：查询自身 + 所有子分类的商品
                    child_ids = Category.objects.filter(parent=category).values_list('id', flat=True)
                    all_ids = list(child_ids) + [category.id]
                    queryset = queryset.filter(category_id__in=all_ids)
                else:
                    # 子分类：直接筛选
                    queryset = queryset.filter(category_id=category_id)
            except Category.DoesNotExist:
                queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'list':
            return GoodsSPUListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return GoodsSPUCreateSerializer
        return GoodsSPUDetailSerializer

    def perform_destroy(self, instance):
        """软删除：标记为已删除，不物理删除"""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def skus(self, request, pk=None):
        """
        获取商品的SKU列表
        GET /api/v1/goods/spus/{id}/skus/
        """
        spu = self.get_object()
        skus = spu.skus.filter(is_active=True)
        serializer = GoodsSKUSerializer(skus, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def toggle_sale(self, request, pk=None):
        """
        切换商品上下架状态
        PUT /api/v1/goods/spus/{id}/toggle_sale/
        """
        spu = self.get_object()
        spu.is_on_sale = not spu.is_on_sale
        spu.save()
        return Response({
            'code': 200,
            'message': '上架成功' if spu.is_on_sale else '下架成功',
            'data': {
                'is_on_sale': spu.is_on_sale
            }
        })

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """
        获取热销商品（带Redis缓存，300秒过期）
        GET /api/v1/goods/spus/hot/
        参数：limit - 返回数量，默认10
        """
        limit = int(request.query_params.get('limit', 10))
        cache_key = f'hot_goods:{limit}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response({'code': 200, 'message': 'success', 'data': cached})
        goods = GoodsSPU.objects.filter(
            is_deleted=False,
            is_on_sale=True
        ).order_by('-sales')[:limit]
        serializer = GoodsSPUListSerializer(goods, many=True)
        cache.set(cache_key, serializer.data, 300)  # 缓存5分钟
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        商品搜索
        GET /api/v1/goods/spus/search/?q=关键词
        支持按商品名称、简介、分类名、品牌名搜索
        """
        from django.db import models as db_models
        keyword = request.query_params.get('q', '')
        if not keyword:
            return Response({
                'code': 400,
                'message': '请输入搜索关键词'
            })

        # 搜索商品名称、简介、分类名（含父分类）、品牌名
        goods = GoodsSPU.objects.filter(
            is_deleted=False,
            is_on_sale=True
        ).filter(
            Q(name__icontains=keyword) |
            Q(subtitle__icontains=keyword) |
            Q(category__name__icontains=keyword) |
            Q(category__parent__name__icontains=keyword) |
            Q(brand__name__icontains=keyword)
        ).distinct().order_by('-sales')

        # 分页
        page = self.paginate_queryset(goods)
        if page is not None:
            serializer = GoodsSPUListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = GoodsSPUListSerializer(goods, many=True)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        上传商品图片
        POST /api/v1/goods/spus/{id}/upload_image/
        """
        spu = self.get_object()
        image = request.FILES.get('image')

        if not image:
            return Response({
                'code': 400,
                'message': '请上传图片'
            }, status=status.HTTP_400_BAD_REQUEST)

        # [修复3] 文件类型和大小校验
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if image.content_type not in allowed_types:
            return Response({'code': 400, 'message': '仅支持 JPG/PNG/WebP/GIF 格式'}, status=400)
        if image.size > 5 * 1024 * 1024:  # 5MB
            return Response({'code': 400, 'message': '图片大小不能超过5MB'}, status=400)

        # 生成唯一文件名
        ext = os.path.splitext(image.name)[1]
        filename = f'goods/{spu.id}/{uuid.uuid4().hex}{ext}'
        filepath = os.path.join(django_settings.MEDIA_ROOT, filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 保存文件
        with open(filepath, 'wb+') as f:
            for chunk in image.chunks():
                f.write(chunk)

        # 生成访问URL
        image_url = f'{django_settings.MEDIA_URL}{filename}'

        # 处理is_main参数（表单数据是字符串，需要转换）
        is_main = request.data.get('is_main', 'false')
        if isinstance(is_main, str):
            is_main = is_main.lower() in ('true', '1', 'yes')

        # 创建图片记录
        product_image = ProductImage.objects.create(
            spu=spu,
            image_url=image_url,
            is_main=is_main
        )

        # 如果是主图，更新SPU的主图
        if product_image.is_main:
            spu.main_image = product_image.image_url
            spu.save()

        return Response({
            'code': 200,
            'message': '上传成功',
            'data': ProductImageSerializer(product_image).data
        })

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """
        获取商品图片列表
        GET /api/v1/goods/spus/{id}/images/
        """
        spu = self.get_object()
        images = spu.images.all()
        serializer = ProductImageSerializer(images, many=True)
        return Response({
            'code': 200,
            'message': 'success',
            'data': serializer.data
        })


# ==================== 商品SKU视图 ====================
class GoodsSKUViewSet(viewsets.ModelViewSet):
    """
    商品SKU视图集

    提供：
    - GET /api/v1/goods/skus/ - SKU列表
    - POST /api/v1/goods/skus/ - 创建SKU
    - GET /api/v1/goods/skus/{id}/ - SKU详情
    - PUT /api/v1/goods/skus/{id}/ - 更新SKU
    - DELETE /api/v1/goods/skus/{id}/ - 删除SKU
    - POST /api/v1/goods/skus/{id}/deduct_stock/ - 扣减库存
    - POST /api/v1/goods/skus/{id}/restore_stock/ - 恢复库存
    """
    queryset = GoodsSKU.objects.filter(is_active=True)
    serializer_class = GoodsSKUSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['spu', 'is_default']
    ordering_fields = ['price', 'stock', 'sales']
    permission_classes = [IsSellerOrReadOnly]

    def get_queryset(self):
        """支持按库存筛选"""
        queryset = super().get_queryset()
        in_stock = self.request.query_params.get('in_stock', None)
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock=0)
        return queryset

    @action(detail=True, methods=['post'])
    def deduct_stock(self, request, pk=None):
        """
        扣减库存
        POST /api/v1/goods/skus/{id}/deduct_stock/
        参数：quantity - 扣减数量
        """
        sku = self.get_object()
        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            return Response({
                'code': 400,
                'message': '扣减数量必须大于0'
            }, status=status.HTTP_400_BAD_REQUEST)

        if sku.stock < quantity:
            return Response({
                'code': 400,
                'message': '库存不足'
            }, status=status.HTTP_400_BAD_REQUEST)

        sku.stock -= quantity
        sku.save()

        return Response({
            'code': 200,
            'message': '库存扣减成功',
            'data': {
                'sku_id': sku.id,
                'stock': sku.stock,
                'deducted': quantity
            }
        })

    @action(detail=True, methods=['post'])
    def restore_stock(self, request, pk=None):
        """
        恢复库存
        POST /api/v1/goods/skus/{id}/restore_stock/
        参数：quantity - 恢复数量
        """
        sku = self.get_object()
        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            return Response({
                'code': 400,
                'message': '恢复数量必须大于0'
            }, status=status.HTTP_400_BAD_REQUEST)

        sku.stock += quantity
        sku.save()

        return Response({
            'code': 200,
            'message': '库存恢复成功',
            'data': {
                'sku_id': sku.id,
                'stock': sku.stock,
                'restored': quantity
            }
        })


# ==================== 商品图片视图 ====================
class ProductImageViewSet(viewsets.ModelViewSet):
    """
    商品图片视图集

    提供：
    - DELETE /api/v1/goods/images/{id}/ - 删除图片
    - PUT /api/v1/goods/images/{id}/set_main/ - 设置主图
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsSellerOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        """删除图片"""
        instance = self.get_object()
        # 如果删除的是主图，清空SPU的主图
        if instance.is_main:
            spu = instance.spu
            spu.main_image = None
            spu.save()
        instance.delete()
        return Response({
            'code': 200,
            'message': '删除成功'
        })

    @action(detail=True, methods=['put'])
    def set_main(self, request, pk=None):
        """
        设置主图
        PUT /api/v1/goods/images/{id}/set_main/
        """
        image = self.get_object()

        # 取消该SPU下其他图片的主图状态
        ProductImage.objects.filter(
            spu=image.spu,
            is_main=True
        ).update(is_main=False)

        # 设置当前图片为主图
        image.is_main = True
        image.save()

        # 更新SPU的主图
        image.spu.main_image = image.image_url
        image.spu.save()

        return Response({
            'code': 200,
            'message': '设置成功',
            'data': {
                'image_id': image.id,
                'image_url': image.image_url
            }
        })



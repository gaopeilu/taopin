"""
商品模块的序列化器

包含：
1. CategorySerializer - 分类序列化器（支持树形结构）
2. BrandSerializer - 品牌序列化器
3. GoodsSPUListSerializer - SPU列表序列化器（精简字段）
4. GoodsSPUDetailSerializer - SPU详情序列化器（完整字段）
5. GoodsSKUSerializer - SKU序列化器
6. ProductImageSerializer - 商品图片序列化器
"""
from rest_framework import serializers
from .models import Category, Brand, GoodsSPU, GoodsSKU, ProductImage


# ==================== 商品图片序列化器 ====================
class ProductImageSerializer(serializers.ModelSerializer):
    """
    商品图片序列化器
    用于返回商品图片信息
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'sort_order', 'is_main']
        read_only_fields = ['id']


# ==================== 商品SKU序列化器 ====================
class GoodsSKUSerializer(serializers.ModelSerializer):
    """
    商品SKU序列化器
    用于返回SKU的详细信息
    """
    # 是否有库存（只读属性）
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = GoodsSKU
        fields = [
            'id', 'spu', 'name', 'price', 'original_price',
            'stock', 'sales', 'specs', 'image',
            'is_default', 'is_active', 'is_in_stock',
            'created_at'
        ]
        read_only_fields = ['id', 'sales', 'created_at']


# ==================== 品牌序列化器 ====================
class BrandSerializer(serializers.ModelSerializer):
    """
    品牌序列化器
    """
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'logo', 'description',
            'first_letter', 'sort_order', 'is_active'
        ]
        read_only_fields = ['id']


# ==================== 分类序列化器 ====================
class CategorySerializer(serializers.ModelSerializer):
    """
    分类序列化器
    支持树形结构展示（递归嵌套子分类）
    """
    # 子分类（只读，递归嵌套）
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'parent', 'level',
            'icon', 'sort_order', 'is_active', 'children'
        ]
        read_only_fields = ['id']

    def get_children(self, obj):
        """
        获取子分类列表
        递归调用自身序列化器，实现树形结构
        """
        # 只获取启用的子分类
        children = obj.children.filter(is_active=True)
        if children.exists():
            return CategorySerializer(children, many=True).data
        return []


# ==================== SPU列表序列化器 ====================
class GoodsSPUListSerializer(serializers.ModelSerializer):
    """
    SPU列表序列化器（精简版）
    用于商品列表页，只返回必要字段
    """
    # 品牌名称（只读）
    brand_name = serializers.CharField(source='brand.name', read_only=True, default='')
    # 分类名称（只读）
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    # 价格区间（只读，优先使用annotate的值，fallback到property）
    price_range = serializers.SerializerMethodField()
    # 商家信息（只读）
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True, default='')

    class Meta:
        model = GoodsSPU
        fields = [
            'id', 'name', 'subtitle', 'main_image',
            'brand', 'brand_name',
            'category', 'category_name',
            'seller', 'seller_name',
            'price_range', 'sales', 'is_on_sale',
            'created_at'
        ]
        read_only_fields = ['id', 'sales', 'created_at']

    def get_price_range(self, obj):
        """优先使用annotate预计算的价格，避免N+1查询"""
        if hasattr(obj, 'min_price') and obj.min_price is not None:
            if obj.min_price == obj.max_price:
                return f'¥{obj.min_price}'
            return f'¥{obj.min_price} - ¥{obj.max_price}'
        # fallback到model property（单个详情页场景）
        return obj.price_range


# ==================== SPU详情序列化器 ====================
class GoodsSPUDetailSerializer(serializers.ModelSerializer):
    """
    SPU详情序列化器（完整版）
    用于商品详情页，返回完整信息，包括SKU列表和图片列表
    """
    # 品牌信息（嵌套序列化）
    brand = BrandSerializer(read_only=True)
    # 分类信息（嵌套序列化）
    category = CategorySerializer(read_only=True)
    # SKU列表（只读，反向查询）
    skus = GoodsSKUSerializer(many=True, read_only=True)
    # 图片列表（只读，反向查询）
    images = ProductImageSerializer(many=True, read_only=True)
    # 价格区间
    price_range = serializers.CharField(read_only=True)

    class Meta:
        model = GoodsSPU
        fields = [
            'id', 'name', 'subtitle', 'description',
            'main_image', 'sales',
            'brand', 'category',
            'skus', 'images',
            'price_range', 'is_on_sale',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sales', 'created_at', 'updated_at']


# ==================== SPU创建/更新序列化器 ====================
class GoodsSPUCreateSerializer(serializers.ModelSerializer):
    """
    SPU创建/更新序列化器
    用于商家创建或编辑商品
    """
    class Meta:
        model = GoodsSPU
        fields = [
            'name', 'category', 'brand', 'subtitle',
            'description', 'main_image', 'is_on_sale'
        ]

    def validate_name(self, value):
        """验证商品名称"""
        if len(value) < 2:
            raise serializers.ValidationError("商品名称至少2个字符")
        return value

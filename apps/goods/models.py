"""
商品模块的数据模型

包含：
1. Category - 商品分类（多级树形结构）
2. Brand - 品牌
3. GoodsSPU - 商品SPU（标准产品单元）
4. GoodsSKU - 商品SKU（库存量单元）
5. ProductImage - 商品图片
"""
from django.db import models


# ==================== 商品分类 ====================
class Category(models.Model):
    """
    商品分类模型
    使用 parent_id 实现多级树形结构

    举例：
    - 服装（一级分类）
      - 男装（二级分类）
        - T恤（三级分类）
        - 夹克（三级分类）
      - 女装（二级分类）
    """
    # 分类名称
    name = models.CharField('分类名称', max_length=100)

    # 父分类，self关联实现树形结构
    # null=True 表示顶级分类（没有父分类）
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父分类'
    )

    # 层级：1=一级分类，2=二级分类，3=三级分类
    level = models.SmallIntegerField('层级', default=1)

    # 分类图标
    icon = models.CharField('图标', max_length=255, null=True, blank=True)

    # 排序值，越大越靠前
    sort_order = models.IntegerField('排序', default=0)

    # 是否启用
    is_active = models.BooleanField('启用', default=True)

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 更新时间
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'goods_category'
        verbose_name = '商品分类'
        verbose_name_plural = verbose_name
        ordering = ['-sort_order', 'id']  # 按排序值降序，再按ID升序

    def __str__(self):
        return self.name


# ==================== 品牌 ====================
class Brand(models.Model):
    """
    品牌模型

    举例：Apple、华为、小米、Nike、优衣库
    """
    # 品牌名称，唯一
    name = models.CharField('品牌名称', max_length=100, unique=True)

    # 品牌Logo图片
    logo = models.ImageField('品牌Logo', upload_to='brands/', null=True, blank=True)

    # 品牌描述
    description = models.TextField('品牌描述', blank=True, default='')

    # 品牌首字母，用于索引筛选（A、B、C...）
    first_letter = models.CharField('首字母', max_length=1, blank=True, default='')

    # 排序值
    sort_order = models.IntegerField('排序', default=0)

    # 是否启用
    is_active = models.BooleanField('启用', default=True)

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 更新时间
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'goods_brand'
        verbose_name = '品牌'
        verbose_name_plural = verbose_name
        ordering = ['-sort_order', 'id']

    def __str__(self):
        return self.name


# ==================== 商品SPU ====================
class GoodsSPU(models.Model):
    """
    商品SPU模型（标准产品单元）

    SPU是商品的抽象概念，不涉及具体规格和库存
    举例：iPhone 15 Pro Max（一个SPU）
    """
    # 所属商家
    seller = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='goods',
        verbose_name='所属商家',
        limit_choices_to={'role': 'seller'}
    )

    # 商品名称
    name = models.CharField('商品名称', max_length=200, db_index=True)

    # 所属分类
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # 分类删除时，商品分类设为NULL
        null=True,
        blank=True,
        related_name='spus',
        verbose_name='所属分类'
    )

    # 所属品牌
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spus',
        verbose_name='所属品牌'
    )

    # 商品简介（简短描述）
    subtitle = models.CharField('商品简介', max_length=500, blank=True, default='')

    # 商品详情（富文本，支持HTML）
    description = models.TextField('商品详情', blank=True, default='')

    # 主图URL
    main_image = models.CharField('主图', max_length=255, null=True, blank=True)

    # 销量（冗余字段，由SKU销量汇总）
    sales = models.IntegerField('总销量', default=0)

    # 是否上架
    is_on_sale = models.BooleanField('上架状态', default=False, db_index=True)

    # 是否删除（软删除）
    is_deleted = models.BooleanField('删除标记', default=False)

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 更新时间
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'goods_spu'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def price_range(self):
        """获取价格区间"""
        skus = self.skus.filter(is_active=True)
        if not skus.exists():
            return '暂无报价'
        prices = skus.values_list('price', flat=True)
        min_price = min(prices)
        max_price = max(prices)
        if min_price == max_price:
            return f'¥{min_price}'
        return f'¥{min_price} - ¥{max_price}'


# ==================== 商品SKU ====================
class GoodsSKU(models.Model):
    """
    商品SKU模型（库存量单元）

    SKU是具体的商品，有明确的规格、价格、库存
    举例：iPhone 15 Pro Max 黑色 256GB（一个SKU）
    """
    # 所属SPU
    spu = models.ForeignKey(
        GoodsSPU,
        on_delete=models.CASCADE,  # SPU删除时，SKU也删除
        related_name='skus',
        verbose_name='所属SPU'
    )

    # SKU名称（通常包含规格信息）
    name = models.CharField('SKU名称', max_length=200)

    # 售价
    price = models.DecimalField(
        '售价',
        max_digits=10,  # 最大10位数
        decimal_places=2,  # 保留2位小数
        db_index=True
    )

    # 原价（划线价，可选）
    original_price = models.DecimalField(
        '原价',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # 库存数量
    stock = models.IntegerField('库存', default=0)

    # 销量
    sales = models.IntegerField('销量', default=0)

    # 规格属性（JSON格式存储）
    # 举例：{"颜色": "黑色", "存储": "256GB"}
    specs = models.JSONField('规格', null=True, blank=True)

    # SKU图片
    image = models.CharField('SKU图片', max_length=255, null=True, blank=True)

    # 是否默认SKU（一个SPU下只能有一个默认SKU）
    is_default = models.BooleanField('默认SKU', default=False)

    # 是否启用
    is_active = models.BooleanField('启用', default=True)

    # 条形码（可选）
    barcode = models.CharField('条形码', max_length=50, null=True, blank=True)

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 更新时间
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'goods_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name
        ordering = ['-is_default', 'price']

    def __str__(self):
        return f'{self.spu.name} - {self.name}'

    @property
    def is_in_stock(self):
        """是否有库存"""
        return self.stock > 0


# ==================== 商品图片 ====================
class ProductImage(models.Model):
    """
    商品图片模型

    一个SPU可以有多张图片，用于商品详情页轮播展示
    """
    # 所属SPU
    spu = models.ForeignKey(
        GoodsSPU,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属SPU'
    )

    # 图片URL
    image_url = models.CharField('图片URL', max_length=255)

    # 排序值
    sort_order = models.IntegerField('排序', default=0)

    # 是否主图（一个SPU只能有一个主图）
    is_main = models.BooleanField('主图', default=False)

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name
        ordering = ['-is_main', 'sort_order']

    def __str__(self):
        return f'{self.spu.name} - 图片{self.id}'

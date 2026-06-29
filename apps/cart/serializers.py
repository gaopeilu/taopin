from rest_framework import serializers
from .models import Cart


class CartSerializer(serializers.ModelSerializer):
    """购物车序列化器"""
    goods_name = serializers.SerializerMethodField()
    goods_image = serializers.SerializerMethodField()
    sku_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'sku_id', 'spu_id', 'quantity', 'is_selected',
                  'goods_name', 'goods_image', 'sku_name', 'price', 'stock', 'subtotal',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    # [Bug20] 预加载缓存，避免N+1查询
    def _get_spu_cache(self):
        if not hasattr(self, '_spu_cache'):
            spu_ids = list(set(obj.spu_id for obj in self.instance)) if hasattr(self, 'instance') and hasattr(self.instance, '__iter__') else []
            from apps.goods.models import GoodsSPU
            self._spu_cache = {spu.id: spu for spu in GoodsSPU.objects.filter(id__in=spu_ids)}
        return self._spu_cache

    def _get_sku_cache(self):
        if not hasattr(self, '_sku_cache'):
            sku_ids = list(set(obj.sku_id for obj in self.instance)) if hasattr(self, 'instance') and hasattr(self.instance, '__iter__') else []
            from apps.goods.models import GoodsSKU
            self._sku_cache = {sku.id: sku for sku in GoodsSKU.objects.filter(id__in=sku_ids)}
        return self._sku_cache

    def _get_spu(self, obj):
        cache = self._get_spu_cache()
        return cache.get(obj.spu_id)

    def _get_sku(self, obj):
        cache = self._get_sku_cache()
        return cache.get(obj.sku_id)

    # [Bug19] 裸except改为except Exception
    def get_goods_name(self, obj):
        spu = self._get_spu(obj)
        return spu.name if spu else ''

    def get_goods_image(self, obj):
        spu = self._get_spu(obj)
        return (spu.main_image or '') if spu else ''

    def get_sku_name(self, obj):
        sku = self._get_sku(obj)
        return sku.name if sku else ''

    def get_price(self, obj):
        sku = self._get_sku(obj)
        return str(sku.price) if sku else '0'

    def get_stock(self, obj):
        sku = self._get_sku(obj)
        return sku.stock if sku else 0

    def get_subtotal(self, obj):
        sku = self._get_sku(obj)
        return str(sku.price * obj.quantity) if sku else '0'


class AddCartSerializer(serializers.Serializer):
    """添加购物车"""
    sku_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartSerializer(serializers.Serializer):
    """更新购物车"""
    quantity = serializers.IntegerField(min_value=1, required=False)
    is_selected = serializers.BooleanField(required=False)

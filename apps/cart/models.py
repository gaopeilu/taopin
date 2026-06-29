from django.db import models
from django.conf import settings


class Cart(models.Model):
    """
    购物车模型（数据库层）
    注意：当前购物车实际使用 Redis 存储（cart/views.py），
    此模型保留作为 fallback 和数据迁移用途。
    Redis 结构: cart:{user_id} -> Hash {sku_id: JSON}
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    sku_id = models.IntegerField('SKU ID', db_index=True)
    spu_id = models.IntegerField('SPU ID')
    quantity = models.IntegerField('数量', default=1)
    is_selected = models.BooleanField('是否选中', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('user', 'sku_id')
        ordering = ['-created_at']

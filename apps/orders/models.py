from django.db import models
from django.conf import settings


class Order(models.Model):
    """订单"""
    STATUS_CHOICES = (
        ('pending', '待付款'),
        ('paid', '待发货'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('refund', '退款中'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name='用户')
    order_no = models.CharField('订单号', max_length=64, unique=True, db_index=True)
    total_amount = models.DecimalField('订单总额', max_digits=10, decimal_places=2)
    pay_amount = models.DecimalField('实付金额', max_digits=10, decimal_places=2)
    freight_fee = models.DecimalField('运费', max_digits=10, decimal_places=2, default=0)
    status = models.CharField('订单状态', max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    receiver_name = models.CharField('收货人', max_length=50, default='')
    receiver_phone = models.CharField('收货电话', max_length=11, default='')
    receiver_address = models.CharField('收货地址', max_length=500, default='')

    pay_method = models.CharField('支付方式', max_length=20, blank=True, default='')
    pay_time = models.DateTimeField('支付时间', null=True, blank=True)
    trade_no = models.CharField('交易流水号', max_length=100, blank=True, default='')

    ship_time = models.DateTimeField('发货时间', null=True, blank=True)
    express_no = models.CharField('快递单号', max_length=100, blank=True, default='')

    remark = models.CharField('备注', max_length=500, blank=True, default='')
    is_deleted = models.BooleanField('软删除', default=False)  # [修复8] 订单软删除
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):  # [修复12]
        return f'{self.order_no} ({self.get_status_display()})'


class OrderItem(models.Model):
    """订单商品"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sku_id = models.IntegerField()
    spu_id = models.IntegerField()
    goods_name = models.CharField(max_length=200)
    goods_image = models.CharField(max_length=500, default='')
    sku_name = models.CharField(max_length=200, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):  # [修复12]
        return f'{self.goods_name} x{self.quantity}'

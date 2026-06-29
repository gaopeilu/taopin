from django.db import models
from django.conf import settings


class Coupon(models.Model):
    """优惠券"""
    TYPE_CHOICES = (
        ('minus', '满减券'),
        ('discount', '折扣券'),
        ('newcomer', '新人券'),
    )

    name = models.CharField('优惠券名称', max_length=100)
    coupon_type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='minus')
    value = models.DecimalField('面值/折扣', max_digits=10, decimal_places=2)
    min_amount = models.DecimalField('最低消费', max_digits=10, decimal_places=2, default=0)
    total_count = models.IntegerField('发行总量', default=100)
    claimed_count = models.IntegerField('已领取数量', default=0)
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']

    @property
    def remaining(self):
        return self.total_count - self.claimed_count


class CouponRecord(models.Model):
    """用户优惠券领取记录"""
    STATUS_CHOICES = (
        ('unused', '未使用'),
        ('used', '已使用'),
        ('expired', '已过期'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='records')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='unused')
    order_no = models.CharField('使用订单号', max_length=64, blank=True, default='')
    claimed_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'coupon_records'
        ordering = ['-claimed_at']
        unique_together = ('user', 'coupon')  # 防止重复领取

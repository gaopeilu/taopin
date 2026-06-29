from django.db import models


class Payment(models.Model):
    """支付记录"""
    STATUS_CHOICES = (
        ('pending', '待支付'),
        ('success', '支付成功'),
        ('failed', '支付失败'),
        ('refunded', '已退款'),
    )
    METHOD_CHOICES = (
        ('wechat', '微信支付'),
        ('alipay', '支付宝'),
        ('card', '银行卡'),
    )

    pay_no = models.CharField('支付流水号', max_length=64, unique=True, db_index=True)
    order_no = models.CharField('订单号', max_length=64, db_index=True)
    amount = models.DecimalField('支付金额', max_digits=10, decimal_places=2)
    pay_method = models.CharField('支付方式', max_length=20, choices=METHOD_CHOICES, default='wechat')
    status = models.CharField('支付状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    trade_no = models.CharField('第三方交易号', max_length=100, blank=True, default='')
    pay_time = models.DateTimeField('支付时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

from django.db import models
from django.conf import settings


class Review(models.Model):
    """商品评价"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    sku_id = models.IntegerField('SKU ID', db_index=True)
    spu_id = models.IntegerField('SPU ID', db_index=True)
    order_no = models.CharField('订单号', max_length=64, default='')
    rating = models.IntegerField('评分', default=5)  # 1-5
    content = models.TextField('评价内容', blank=True, default='')
    images = models.JSONField('评价图片', default=list, blank=True)
    is_anonymous = models.BooleanField('匿名评价', default=False)
    like_count = models.IntegerField('点赞数', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']


class ReviewReply(models.Model):
    """评价回复"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField('回复内容')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_replies'


class ReviewLike(models.Model):
    """评价点赞记录（[Bug15] 防止重复点赞）"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_likes'
        unique_together = ('review', 'user')

from django.db import models
from django.conf import settings


class SearchHistory(models.Model):
    """搜索历史"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_history')
    keyword = models.CharField('搜索关键词', max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        ordering = ['-created_at']
        unique_together = ('user', 'keyword')

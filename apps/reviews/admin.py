from django.contrib import admin
from .models import Review, ReviewLike


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'spu_id', 'rating', 'is_anonymous', 'like_count', 'created_at']
    list_filter = ['rating', 'is_anonymous']
    search_fields = ['content']


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']

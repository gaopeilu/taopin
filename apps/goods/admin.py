from django.contrib import admin
from .models import Category, Brand, GoodsSPU, GoodsSKU, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'sort_order', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'first_letter', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


class GoodsSKUInline(admin.TabularInline):
    model = GoodsSKU
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(GoodsSPU)
class GoodsSPUAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'brand', 'sales', 'is_on_sale', 'is_deleted']
    list_filter = ['is_on_sale', 'is_deleted', 'category']
    search_fields = ['name', 'subtitle']
    inlines = [GoodsSKUInline, ProductImageInline]


@admin.register(GoodsSKU)
class GoodsSKUAdmin(admin.ModelAdmin):
    list_display = ['name', 'spu', 'price', 'stock', 'sales', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'barcode']

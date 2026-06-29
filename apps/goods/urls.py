"""
商品模块的路由配置

将URL映射到对应的视图
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册路由
# 自动生成：列表、创建、详情、更新、删除 等接口
router.register('categories', views.CategoryViewSet, basename='category')
router.register('brands', views.BrandViewSet, basename='brand')
router.register('spus', views.GoodsSPUViewSet, basename='spu')
router.register('skus', views.GoodsSKUViewSet, basename='sku')
router.register('images', views.ProductImageViewSet, basename='image')

app_name = 'goods'

urlpatterns = [
    # 路由器自动生成的URL
    path('', include(router.urls)),
]

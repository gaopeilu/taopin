"""
URL configuration for dianshang project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django后台管理
    path('admin/', admin.site.urls),

    # API v1 - 用户模块
    path('api/v1/users/', include('apps.users.urls')),

    # 商品模块
    path('api/v1/goods/', include('apps.goods.urls')),

    # 购物车模块
    path('api/v1/cart/', include('apps.cart.urls')),

    # 订单模块
    path('api/v1/orders/', include('apps.orders.urls')),

    # 支付模块
    path('api/v1/payment/', include('apps.payment.urls')),

    # 营销/优惠券模块
    path('api/v1/coupons/', include('apps.marketing.urls')),

    # 搜索模块
    path('api/v1/search/', include('apps.search.urls')),

    # 评价模块
    path('api/v1/reviews/', include('apps.reviews.urls')),
]

# 开发环境：提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

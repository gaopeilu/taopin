from django.urls import path
from . import views

urlpatterns = [
    path('', views.CouponListView.as_view(), name='coupon-list'),
    path('<int:pk>/claim/', views.CouponClaimView.as_view(), name='coupon-claim'),
    path('mine/', views.MyCouponListView.as_view(), name='coupon-mine'),
]

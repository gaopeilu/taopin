from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('<str:order_no>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<str:order_no>/pay/', views.OrderPayView.as_view(), name='order-pay'),
    path('<str:order_no>/cancel/', views.OrderCancelView.as_view(), name='order-cancel'),
    path('<str:order_no>/ship/', views.OrderShipView.as_view(), name='order-ship'),
    path('<str:order_no>/complete/', views.OrderCompleteView.as_view(), name='order-complete'),
    path('<str:order_no>/refund/', views.OrderRefundView.as_view(), name='order-refund'),
    path('refund/<str:refund_no>/', views.RefundDetailView.as_view(), name='refund-detail'),
]

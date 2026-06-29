from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.CreatePaymentView.as_view(), name='payment-create'),
    path('mock-pay/', views.MockPayView.as_view(), name='payment-mock'),
    path('callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
    path('<str:pay_no>/status/', views.PaymentStatusView.as_view(), name='payment-status'),
]

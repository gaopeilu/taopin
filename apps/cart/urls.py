from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartListView.as_view(), name='cart-list'),
    path('add/', views.CartAddView.as_view(), name='cart-add'),
    path('<int:pk>/', views.CartUpdateView.as_view(), name='cart-update'),
    path('<int:pk>/delete/', views.CartDeleteView.as_view(), name='cart-delete'),
    path('clear/', views.CartClearView.as_view(), name='cart-clear'),
    path('select-all/', views.CartSelectAllView.as_view(), name='cart-select-all'),
]

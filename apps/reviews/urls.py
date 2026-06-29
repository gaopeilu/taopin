from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review-list'),
    path('create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('mine/', views.MyReviewListView.as_view(), name='review-mine'),
    path('<int:pk>/like/', views.ReviewLikeView.as_view(), name='review-like'),
]

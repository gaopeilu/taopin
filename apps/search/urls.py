from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.SearchHistoryListView.as_view(), name='search-history'),
    path('history/clear/', views.SearchHistoryClearView.as_view(), name='search-history-clear'),
    path('suggest/', views.SearchSuggestView.as_view(), name='search-suggest'),
]

from django.urls import path
from .views import YahooFinanceUpdateView

urlpatterns = [
    path('yahoo-finance/latest', YahooFinanceUpdateView.as_view(), name='yahoo-finance-latest'),
]

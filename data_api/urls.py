from django.urls import path
from .views import CSVDataView

urlpatterns = [
    path('<str:filename>', CSVDataView.as_view(), name='csv-data'),
]

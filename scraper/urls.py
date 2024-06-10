from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('result/', views.result, name='result'),
    path('download-csv/', views.download_csv, name='download_csv'),
]

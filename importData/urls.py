""" URL module for importData """
from django.urls import path
from .views import get_record, LoadDatabasePage


urlpatterns = [
    path('database-load/', LoadDatabasePage.as_view(), name='database_load'),
    path('database-load-record/', get_record, name ='load_record'),
]
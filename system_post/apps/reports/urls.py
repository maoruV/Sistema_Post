from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('view/', views.report_view, name='view'),
    path('data/', views.report_data, name='data'),
]

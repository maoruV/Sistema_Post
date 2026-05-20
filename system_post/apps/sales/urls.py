from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('new/', views.sale_new, name='sale_new'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/cancel/', views.sale_cancel, name='sale_cancel'),
    path('<int:pk>/pay/', views.sale_pay, name='sale_pay'),
    path('<int:pk>/collect/', views.sale_collect, name='sale_collect'),
    path('<int:pk>/collect/save/', views.sale_collect_save, name='sale_collect_save'),
    path('<int:pk>/invoice/', views.sale_invoice, name='sale_invoice'),
    path('<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('<int:pk>/edit/save/', views.sale_edit_save, name='sale_edit_save'),
    path('complete/', views.sale_complete, name='sale_complete'),
    path('add-item/', views.add_item, name='add_item'),
]

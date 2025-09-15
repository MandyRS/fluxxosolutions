from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog, name='blog'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    path('novo/', views.post_create, name='post_create'),
    path('<slug:slug>/editar/', views.post_edit, name='post_edit'),
    path('<slug:slug>/deletar/', views.post_delete, name='post_delete'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
]

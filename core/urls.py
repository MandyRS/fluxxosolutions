from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('servicos/', views.servicos, name='servicos'),
    path('contato/', views.contato, name='contato'),
    path('sobre/', views.sobre, name='sobre'),

]


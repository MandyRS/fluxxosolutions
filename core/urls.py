from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('selecionar-empresa/', views.selecionar_empresa, name='selecionar_empresa'),
    path('logout/', views.logout_view, name='logout'),
    path('cliente/criar/', views.criar_cliente_ajax, name='criar_cliente_ajax'),
    path('produto/criar/', views.criar_produto_ajax, name='criar_produto_ajax'),
    path('servico/criar/', views.criar_servico_ajax, name='criar_servico_ajax'),
    path('orcamentos/', views.listar_orcamentos, name='listar_orcamentos'),
    path('orcamentos/criar/', views.criar_orcamento, name='criar_orcamento'),
    path('orcamentos/<int:orcamento_id>/', views.detalhe_orcamento, name='detalhe_orcamento'),
    path('orcamentos/<int:orcamento_id>/editar/', views.editar_orcamento, name='editar_orcamento'),
    path('orcamentos/<int:orcamento_id>/excluir/', views.excluir_orcamento, name='excluir_orcamento'),
    path('autocomplete/cliente/', views.autocomplete_cliente, name='autocomplete_cliente'),
    path('orcamentos/<int:orcamento_id>/itens/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('orcamentos/itens/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('orcamentos/itens/<int:item_id>/excluir/', views.excluir_item, name='excluir_item'),
    path('orcamentos/itens/<int:item_id>/', views.detalhe_item, name='detalhe_item'),
    path('orcamentos/<int:orcamento_id>/imprimir/', views.imprimir_orcamento, name='imprimir_orcamento'),
    path('orcamentos/<int:id>/json/', views.orcamento_detalhe_json, name='orcamento_detalhe_json'),
    path('autocomplete/produto-servico/', views.autocomplete_produto_servico, name='autocomplete_produto_servico'),
]

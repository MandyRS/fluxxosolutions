from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Páginas principais
    path('', views.index, name='index'),
    path('selecionar-sistema/', views.selecionar_sistema, name='selecionar_sistema'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('selecionar-empresa/', views.selecionar_empresa, name='selecionar_empresa'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('suporte/', views.suporte, name='suporte'),

    # AJAX - Clientes / Produtos / Serviços
    path('cliente/criar/', views.criar_cliente_ajax, name='criar_cliente_ajax'),
    path('produto/criar/', views.criar_produto_ajax, name='criar_produto_ajax'),
    path('servico/criar/', views.criar_servico_ajax, name='criar_servico_ajax'),



    # Orçamentos principais
    path('orcamentos/', views.listar_orcamentos, name='listar_orcamentos'),
    path('orcamentos/criar/', views.criar_orcamento, name='criar_orcamento'),
    path('orcamentos/<int:orcamento_id>/obter/', views.obter_orcamento, name='obter_orcamento'),  # <-- nova
    path('orcamentos/<int:orcamento_id>/editar/', views.editar_orcamento, name='editar_orcamento'),
    path('orcamentos/<int:orcamento_id>/excluir/', views.excluir_orcamento, name='excluir_orcamento'),
    path('orcamentos/<int:orcamento_id>/imprimir/', views.imprimir_orcamento, name='imprimir_orcamento'),
    # Itens de orçamento individuais
    path('orcamentos/<int:orcamento_id>/itens/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('orcamentos/itens/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('orcamentos/itens/<int:item_id>/excluir/', views.excluir_item, name='excluir_item'),
    path('orcamentos/itens/<int:item_id>/', views.detalhe_item, name='detalhe_item'),


    # Autocomplete
    path('autocomplete/cliente/', views.autocomplete_cliente, name='autocomplete_cliente'),
    path('autocomplete/produto-servico/', views.autocomplete_produto_servico, name='autocomplete_produto_servico'),

    # JSON para edição de orçamento (via AJAX)
    path('orcamentos/<int:id>/json/', views.orcamento_detalhe_json, name='orcamento_detalhe_json'),
]

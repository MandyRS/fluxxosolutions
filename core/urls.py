from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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

    # ---------------- CLIENTES ----------------

    path('clientes/<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:id>/excluir/', views.excluir_cliente, name='excluir_cliente'),
    path('clientes/criar/', views.criar_cliente_ajax, name='criar_cliente_ajax'),path('produtos/criar/', views.criar_produto_ajax, name='criar_produto_ajax'),
  
    # ---------------- PRODUTOS ----------------  

    path('produtos/<int:id>/editar/', views.editar_produto, name='editar_produto'),
    path('produtos/<int:id>/excluir/', views.excluir_produto, name='excluir_produto'),

    # ---------------- SERVIÇOS ----------------

    path('servicos/<int:id>/editar/', views.editar_servico_ajax, name='editar_servico_ajax'),
    path('servicos/<int:id>/excluir/', views.excluir_servico_ajax, name='excluir_servico_ajax'),
    path('servicos/criar/', views.criar_servico_ajax, name='criar_servico_ajax'),

    # ---------------- ORÇAMENTOS ----------------

    path('orcamentos/', views.listar_orcamentos, name='listar_orcamentos'),
    path('orcamentos/criar/', views.criar_orcamento, name='criar_orcamento'),
    path('orcamentos/<int:orcamento_id>/obter/', views.obter_orcamento, name='obter_orcamento'),  # <-- nova
    path('orcamentos/<int:orcamento_id>/editar/', views.editar_orcamento, name='editar_orcamento'),
    path('orcamentos/<int:orcamento_id>/excluir/', views.excluir_orcamento, name='excluir_orcamento'),
    path('orcamentos/<int:orcamento_id>/imprimir/', views.imprimir_orcamento, name='imprimir_orcamento'),
    
    #---------------- ITENS DO ORÇAMENTO ----------------

    path('orcamentos/<int:orcamento_id>/itens/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('orcamentos/itens/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('orcamentos/itens/<int:item_id>/excluir/', views.excluir_item, name='excluir_item'),
    path('orcamentos/itens/<int:item_id>/', views.detalhe_item, name='detalhe_item'),

    # ---------------- AUTOCOMPLETE ----------------
    
    path('autocomplete/cliente/', views.autocomplete_cliente, name='autocomplete_cliente'),
    path('autocomplete_produto_servico/', views.autocomplete_produto_servico, name='autocomplete_produto_servico'),

    # ---------------- DETALHE ORÇAMENTO JSON ----------------
    
    path('orcamentos/<int:id>/json/', views.orcamento_detalhe_json, name='orcamento_detalhe_json'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

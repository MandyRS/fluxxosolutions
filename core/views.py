from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
import json

from .models import (
    Empresa, UserEmpresa, Cliente, Produto, Servico,
    Orcamento, ItemOrcamento
)
from .forms import OrcamentoForm, ItemOrcamentoForm


# -----------------------------
# Funções auxiliares
# -----------------------------
def get_empresa_do_usuario(user):
    """Retorna a primeira empresa associada ao usuário."""
    try:
        return user.userempresa_set.first().empresa
    except AttributeError:
        return None


# -----------------------------
# Views básicas
# -----------------------------
def index(request):
    return render(request, 'core/index.html')


def logout_view(request):
    logout(request)
    return redirect('core:index')


@login_required
def selecionar_empresa(request):
    empresas = UserEmpresa.objects.filter(user=request.user)
    if request.method == 'POST':
        request.session['empresa_id'] = request.POST.get('empresa_id')
        return redirect('core:dashboard')
    return render(request, 'core/selecionar_empresa.html', {'empresas': empresas})


@login_required
def dashboard(request):
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return redirect('core:selecionar_empresa')

    empresa = get_object_or_404(Empresa, id=empresa_id)

    orcamentos = Orcamento.objects.filter(empresa=empresa)
    clientes = Cliente.objects.filter(empresa=empresa)
    produtos = Produto.objects.filter(empresa=empresa)
    servicos = Servico.objects.filter(empresa=empresa)

    hoje = timezone.now().date()
    alerta_orcamentos = orcamentos.filter(previsao_entrega__lte=hoje + timedelta(days=3))

    context = {
        'empresa': empresa,
        'orcamentos': orcamentos.count(),
        'clientes': clientes.count(),
        'produtos': produtos.count(),
        'servicos': servicos.count(),
        'alerta_orcamentos': alerta_orcamentos,
    }
    return render(request, 'core/configuracao.html', context)


# -----------------------------
# Criação rápida (via AJAX)
# -----------------------------
@login_required
@require_POST
def criar_cliente_ajax(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return JsonResponse({'status': 'erro', 'mensagem': 'Empresa não encontrada.'})

    cliente = Cliente.objects.create(
        empresa=empresa,
        razao_social=request.POST.get('razao_social'),
        nome_fantasia=request.POST.get('nome_fantasia'),
        cpf_cnpj=request.POST.get('cpf_cnpj'),
        telefone=request.POST.get('telefone'),
        email=request.POST.get('email'),
        endereco=request.POST.get('endereco'),
        cidade_uf=request.POST.get('cidade_uf'),
        cep=request.POST.get('cep')
    )

    return JsonResponse({
        'status': 'ok',
        'cliente': {
            'razao_social': cliente.razao_social,
            'nome_fantasia': cliente.nome_fantasia,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.telefone,
        }
    })


@login_required
@require_POST
def criar_produto_ajax(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return JsonResponse({'status': 'erro', 'mensagem': 'Empresa não encontrada.'})

    produto = Produto.objects.create(
        empresa=empresa,
        codigo=request.POST.get('codigo'),
        nome=request.POST.get('nome'),
        descricao=request.POST.get('descricao'),
        preco=request.POST.get('preco')
    )

    return JsonResponse({
        'status': 'ok',
        'produto': {
            'codigo': produto.codigo,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco),
        }
    })


@login_required
@require_POST
def criar_servico_ajax(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return JsonResponse({'status': 'erro', 'mensagem': 'Empresa não encontrada.'})

    servico = Servico.objects.create(
        empresa=empresa,
        codigo=request.POST.get('codigo'),
        nome=request.POST.get('nome'),
        descricao=request.POST.get('descricao'),
        preco=request.POST.get('preco')
    )

    return JsonResponse({
        'status': 'ok',
        'servico': {
            'codigo': servico.codigo,
            'nome': servico.nome,
            'descricao': servico.descricao,
            'preco': str(servico.preco),
        }
    })


# -----------------------------
# Orçamentos
# -----------------------------
@login_required
def listar_orcamentos(request):
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return redirect('core:selecionar_empresa')

    orcamentos = Orcamento.objects.filter(empresa_id=empresa_id).order_by('-criado_em')
    clientes = Cliente.objects.filter(empresa_id=empresa_id)

    return render(request, 'core/orcamentos/listar.html', {
        'orcamentos': orcamentos,
        'clientes': clientes,
    })


@login_required
@require_POST
def criar_orcamento(request):
    try:
        data = request.POST
        empresa = get_empresa_do_usuario(request.user)
        orc = Orcamento.objects.create(
            empresa=empresa,
            cliente_id=data.get('cliente'),
            solicitante=data.get('solicitante'),
            previsao_entrega=data.get('previsao_entrega'),
            forma_pagamento=data.get('forma_pagamento'),
            vencimento=data.get('vencimento'),
            observacao=data.get('observacao'),
        )

        itens = json.loads(data.get('itens', '[]'))
        total = 0
        for item in itens:
            tipo = item.get('tipo')
            qtd = float(item.get('qtd') or 0)
            valor = float(item.get('valor') or 0)
            subtotal = qtd * valor
            total += subtotal

            model = Produto if tipo == 'produto' else Servico
            ref = model.objects.filter(id=item.get('id_item')).first()
            ItemOrcamento.objects.create(
                orcamento=orc,
                produto=ref if tipo == 'produto' else None,
                servico=ref if tipo == 'servico' else None,
                quantidade=qtd,
                valor=valor
            )

        orc.total = total
        orc.save()
        return JsonResponse({'status': 'ok'})

    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': str(e)})


@login_required
@require_POST
def editar_orcamento(request, orcamento_id):
    orcamento = get_object_or_404(
        Orcamento,
        id=orcamento_id,
        empresa_id=request.session.get('empresa_id')
    )
    form = OrcamentoForm(request.POST, instance=orcamento)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro', 'erros': form.errors})


@login_required
@require_POST
def excluir_orcamento(request, orcamento_id):
    orcamento = get_object_or_404(
        Orcamento,
        id=orcamento_id,
        empresa_id=request.session.get('empresa_id')
    )
    orcamento.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def imprimir_orcamento(request, orcamento_id):
    empresa_id = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa_id)
    return render(request, 'core/orcamentos/imprimir.html', {'orcamento': orcamento})


# -----------------------------
# Itens de Orçamento
# -----------------------------
@login_required
@require_POST
def adicionar_item(request, orcamento_id):
    orcamento = get_object_or_404(
        Orcamento,
        id=orcamento_id,
        empresa_id=request.session.get('empresa_id')
    )
    form = ItemOrcamentoForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.orcamento = orcamento
        item.save()
        return JsonResponse({'status': 'ok', 'item_id': item.id})
    return JsonResponse({'status': 'erro', 'erros': form.errors})


@login_required
@require_POST
def editar_item(request, item_id):
    item = get_object_or_404(
        ItemOrcamento,
        id=item_id,
        orcamento__empresa_id=request.session.get('empresa_id')
    )
    form = ItemOrcamentoForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro', 'erros': form.errors})


@login_required
@require_POST
def excluir_item(request, item_id):
    item = get_object_or_404(
        ItemOrcamento,
        id=item_id,
        orcamento__empresa_id=request.session.get('empresa_id')
    )
    item.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def detalhe_item(request, item_id):
    item = get_object_or_404(
        ItemOrcamento,
        id=item_id,
        orcamento__empresa_id=request.session.get('empresa_id')
    )
    data = {
        'id': item.id,
        'produto': {'id': item.produto.id} if item.produto else None,
        'servico': {'id': item.servico.id} if item.servico else None,
        'quantidade': item.quantidade,
        'preco_unitario': float(item.preco_unitario),
    }
    return JsonResponse(data)


# -----------------------------
# Autocompletes
# -----------------------------
@login_required
def autocomplete_cliente(request):
    empresa_id = request.session.get('empresa_id')
    term = request.GET.get('term', '')
    clientes = Cliente.objects.filter(
        empresa_id=empresa_id,
        razao_social__icontains=term
    )[:10]

    results = [{
        'id': c.id,
        'label': c.razao_social,
        'value': c.razao_social,
        'nome_fantasia': c.nome_fantasia,
        'cpf_cnpj': c.cpf_cnpj,
        'telefone': c.telefone,
        'email': c.email,
        'endereco': c.endereco,
        'cidade_uf': c.cidade_uf,
        'cep': c.cep,
    } for c in clientes]

    return JsonResponse(results, safe=False)


@login_required
def autocomplete_produto_servico(request):
    term = request.GET.get('term', '')
    produtos = Produto.objects.filter(nome__icontains=term)[:5]
    servicos = Servico.objects.filter(nome__icontains=term)[:5]

    results = [
        {'id': p.id, 'label': f'🛒 {p.nome}', 'preco': float(p.preco or 0), 'tipo': 'produto'}
        for p in produtos
    ] + [
        {'id': s.id, 'label': f'🧰 {s.nome}', 'preco': float(s.preco or 0), 'tipo': 'servico'}
        for s in servicos
    ]

    return JsonResponse(results, safe=False)

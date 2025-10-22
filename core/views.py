from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import json
from core.models import Orcamento, OrcamentoItem, Produto, Servico
from . import models
from .models import Empresa, UserEmpresa, Cliente, Produto, Servico, Orcamento, ItemOrcamento
from .forms import OrcamentoForm, ItemOrcamentoForm
from django.forms import inlineformset_factory
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST

def index(request):
    return render(request, 'core/index.html')

@login_required
def selecionar_empresa(request):
    empresas = UserEmpresa.objects.filter(user=request.user)
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        request.session['empresa_id'] = empresa_id
        return redirect('core:dashboard')
    return render(request, 'core/selecionar_empresa.html', {'empresas': empresas})

@login_required
def dashboard(request):
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return redirect('core:selecionar_empresa')
    
    empresa = Empresa.objects.get(id=empresa_id)

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
        'clientes_list': clientes,
        'produtos_list': produtos,
        'servicos_list': servicos,
    }
    return render(request, 'core/configuracao.html', context)

def logout_view(request):
    logout(request)
    return redirect('core:index')

def get_empresa_do_usuario(user):
    try:
        return user.userempresa_set.first().empresa
    except:
        return None

@login_required
@require_POST
def criar_cliente_ajax(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return JsonResponse({'status': 'erro', 'mensagem': 'Empresa não encontrada.'})

    dados = request.POST
    cliente = Cliente.objects.create(
        empresa=empresa,
        razao_social=dados.get('razao_social'),
        nome_fantasia=dados.get('nome_fantasia'),
        cpf_cnpj=dados.get('cpf_cnpj'),
        telefone=dados.get('telefone'),
        email=dados.get('email'),
        endereco=dados.get('endereco'),
        cidade_uf=dados.get('cidade_uf'),
        cep=dados.get('cep')
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

    dados = request.POST
    produto = Produto.objects.create(
        empresa=empresa,
        codigo=dados.get('codigo'),
        nome=dados.get('nome'),
        descricao=dados.get('descricao'),
        preco=dados.get('preco')
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

    dados = request.POST
    servico = Servico.objects.create(
        empresa=empresa,
        codigo=dados.get('codigo'),
        nome=dados.get('nome'),
        descricao=dados.get('descricao'),
        preco=dados.get('preco')
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

@login_required
def listar_orcamentos(request):
    empresa = request.session.get('empresa_id')
    if not empresa:
        return redirect('core:selecionar_empresa')

    orcamentos = Orcamento.objects.filter(empresa_id=empresa).order_by('-criado_em')
    clientes = Cliente.objects.filter(empresa_id=empresa)

    return render(request, 'core/orcamentos/listar.html', {
        'orcamentos': orcamentos,
        'clientes': clientes,
    })


@login_required
@require_POST
def criar_orcamento(request):
    if request.method == "POST":
        try:
            data = request.POST
            orc = Orcamento.objects.create(
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

                if tipo == 'produto':
                    produto = Produto.objects.filter(id=item.get('id_item')).first()
                    OrcamentoItem.objects.create(orcamento=orc, produto=produto, quantidade=qtd, valor=valor)
                else:
                    servico = Servico.objects.filter(id=item.get('id_item')).first()
                    OrcamentoItem.objects.create(orcamento=orc, servico=servico, quantidade=qtd, valor=valor)

            orc.total = total
            orc.save()

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'erros': str(e)})

@login_required
@require_POST
def editar_orcamento(request, orcamento_id):
    empresa = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa)

    form = OrcamentoForm(request.POST, instance=orcamento)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'status': 'erro', 'erros': form.errors})

@login_required
@require_POST
def excluir_orcamento(request, orcamento_id):
    empresa = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa)

    orcamento.delete()
    return JsonResponse({'status': 'ok'})

# API para autocomplete de clientes (autocomplete)
@login_required
def autocomplete_cliente(request):
    empresa = request.session.get('empresa_id')
    term = request.GET.get('term', '')
    clientes = Cliente.objects.filter(empresa_id=empresa, razao_social__icontains=term)[:10]
    suggestions = []
    for c in clientes:
        suggestions.append({
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
        })
    return JsonResponse(suggestions, safe=False)

@login_required
@require_POST
def adicionar_item(request, orcamento_id):
    empresa = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa)
    form = ItemOrcamentoForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.orcamento = orcamento
        item.save()
        return JsonResponse({'status': 'ok', 'item_id': item.id})
    else:
        return JsonResponse({'status': 'erro', 'erros': form.errors})

@login_required
@require_POST
def editar_item(request, item_id):
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))
    form = ItemOrcamentoForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'status': 'erro', 'erros': form.errors})

@login_required
@require_POST
def excluir_item(request, item_id):
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))
    item.delete()
    return JsonResponse({'status': 'ok'})

def detalhe_item(request, item_id):
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))

    data = {
        'id': item.id,
        'produto': {'id': item.produto.id} if item.produto else None,
        'servico': {'id': item.servico.id} if item.servico else None,
        'quantidade': item.quantidade,
        'preco_unitario': float(item.preco_unitario),
    }
    return JsonResponse(data)

@login_required
def imprimir_orcamento(request, orcamento_id):
    empresa = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa)
    return render(request, 'core/orcamentos/imprimir.html', {'orcamento': orcamento})

def orcamento_detalhe_json(request, id):
    orc = get_object_or_404(Orcamento, id=id)
    data = {
        "orcamento": {
            "id": orc.id,
            "numero": orc.numero,
            "cliente": {
                "id": orc.cliente.id,
                "razao_social": orc.cliente.razao_social,
            },
            "previsao_entrega": orc.previsao_entrega.strftime("%Y-%m-%d") if orc.previsao_entrega else "",
            "solicitante": orc.solicitante or "",
            "servicos_descricao": orc.servicos_descricao or "",
            "escopo": orc.escopo or "",
            "local_uso": orc.local_uso or "",
            "responsavel": orc.responsavel or "",
            "observacao": orc.observacao or "",
            "forma_pagamento": orc.forma_pagamento or "",
            "vencimento": orc.vencimento.strftime("%Y-%m-%d") if orc.vencimento else "",
            "desconto": float(orc.desconto or 0),
        }
    }
    return JsonResponse(data)

def autocomplete_produto_servico(request):
    term = request.GET.get('term', '')
    produtos = Produto.objects.filter(nome__icontains=term)[:5]
    servicos = Servico.objects.filter(nome__icontains=term)[:5]
    results = []

    for p in produtos:
        results.append({'id': p.id, 'label': f'🛒 {p.nome}', 'preco': float(p.preco or 0), 'tipo': 'produto'})
    for s in servicos:
        results.append({'id': s.id, 'label': f'🧰 {s.nome}', 'preco': float(s.preco or 0), 'tipo': 'servico'})

    return JsonResponse(results, safe=False)
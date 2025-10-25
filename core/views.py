from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.db.models import Sum, F, FloatField
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from . import views
from .models import (
    Empresa, UserEmpresa, Cliente, Produto, Servico,
    Orcamento, ItemOrcamento, Servico,
)
from .forms import OrcamentoForm, ItemOrcamentoForm


# -----------------------------
# INDEX
# -----------------------------
def index(request):
    return render(request, 'index.html')


# -----------------------------
# SELECIONAR SISTEMA
# -----------------------------
def selecionar_sistema(request):
    if request.method == 'POST':
        sistema = request.POST.get('sistema')

        # Exemplo: se o usuário escolheu o sistema de orçamento
        if sistema == 'orcamento':
            return redirect('core:login')

        # Caso outros sistemas sejam adicionados depois
        messages.info(request, "Sistema ainda não disponível.")
        return redirect('core:selecionar_sistema')

    return render(request, 'selecionar_sistema.html')


# -----------------------------
# LOGIN / LOGOUT
# -----------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:selecionar_empresa')
        else:
            messages.error(request, "Usuário ou senha incorretos")

    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('core:index')


# -----------------------------
# SELECIONAR EMPRESA
# -----------------------------
@login_required
def selecionar_empresa(request):
    # Busca as empresas vinculadas ao usuário logado
    empresas_vinculadas = UserEmpresa.objects.filter(user=request.user)

    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        if empresa_id:
            request.session['empresa_id'] = empresa_id
            return redirect('core:dashboard')  # ou para onde quiser depois da escolha

    return render(request, 'selecionar_empresa.html', {
        'empresas': empresas_vinculadas  # 👈 nome da variável usada no template
    })


# -----------------------------
# FUNÇÃO AUXILIAR
# -----------------------------

def get_empresa_do_usuario(user):
    try:
        return user.userempresa_set.first().empresa
    except AttributeError:
        return None


# -----------------------------
# DASHBOARD
# -----------------------------

@login_required
def dashboard(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return render(request, "core/erro.html", {"mensagem": "Nenhuma empresa associada."})

    # Contadores básicos
    clientes = empresa.cliente_set.count()
    produtos = empresa.produto_set.count()
    servicos = empresa.servico_set.count()
    orcamentos = empresa.orcamento_set.all()

    # Soma total de todos os orçamentos (somando itens)
    orcamentos_valor_total = (
        ItemOrcamento.objects.filter(orcamento__empresa=empresa)
        .aggregate(total=Sum(F("quantidade") * F("preco_unitario"), output_field=FloatField()))
    )["total"] or 0

    # --------------------------
    # 🔔 Alerta de orçamentos com previsão de entrega próxima
    # --------------------------
    hoje = timezone.now().date()
    limite_alerta = hoje + timedelta(days=3)

    alerta_orcamentos = orcamentos.filter(previsao_entrega__range=[hoje, limite_alerta])

    # --------------------------
    # 📊 Dados para os gráficos
    # --------------------------
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    orcamentos_mes = []
    orcamentos_valor_mes = []

    for i in range(1, 13):
        # quantidade de orçamentos por mês
        orcs_mes = orcamentos.filter(criado_em__month=i)
        orcamentos_mes.append(orcs_mes.count())

        # soma dos valores dos itens por mês
        valor_mes = (
            ItemOrcamento.objects.filter(
                orcamento__empresa=empresa,
                orcamento__criado_em__month=i
            ).aggregate(total=Sum(F("quantidade") * F("preco_unitario"), output_field=FloatField()))
        )["total"] or 0

        orcamentos_valor_mes.append(float(valor_mes))

    context = {
        "empresa": empresa,
        "clientes": clientes,
        "produtos": produtos,
        "servicos": servicos,
        "orcamentos": orcamentos.count(),
        "orcamentos_valor_total": round(orcamentos_valor_total, 2),
        "alerta_orcamentos": alerta_orcamentos,
        "meses": json.dumps(meses),
        "orcamentos_mes": json.dumps(orcamentos_mes),
        "orcamentos_valor_mes": json.dumps(orcamentos_valor_mes),
    }

    return render(request, "dashboard.html", context)



# --------------------------------------------------------
# CLIENTES
# --------------------------------------------------------

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
            'id': cliente.id,
            'razao_social': cliente.razao_social,
            'nome_fantasia': cliente.nome_fantasia,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.telefone,
        }
    })

@login_required
@require_POST
def excluir_cliente(request, id):
    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(id=id)
            cliente.delete()
            return JsonResponse({'status': 'ok', 'mensagem': 'Cliente excluído com sucesso'})
        except Cliente.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Cliente não encontrado'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'})

@login_required
@require_POST
def editar_cliente(request, id):
    cliente = Cliente.objects.get(id=id)
    if request.method == 'GET':
        # retornar os dados em JSON
        return JsonResponse({
            'razao_social': cliente.razao_social,
            'nome_fantasia': cliente.nome_fantasia,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.telefone,
            'email': cliente.email,
            'endereco': cliente.endereco,
            'cidade_uf': cliente.cidade_uf,
            'cep': cliente.cep,
        })
    elif request.method == 'POST':
        # atualizar os dados
        cliente.razao_social = request.POST.get('razao_social')
        cliente.nome_fantasia = request.POST.get('nome_fantasia')
        cliente.cpf_cnpj = request.POST.get('cpf_cnpj')
        cliente.telefone = request.POST.get('telefone')
        cliente.email = request.POST.get('email')
        cliente.endereco = request.POST.get('endereco')
        cliente.cidade_uf = request.POST.get('cidade_uf')
        cliente.cep = request.POST.get('cep')
        cliente.save()
        return JsonResponse({'status': 'ok', 'cliente': {
            'id': cliente.id,
            'razao_social': cliente.razao_social,
            'nome_fantasia': cliente.nome_fantasia,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.telefone,
        }})

#--------------------------------------------------------

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
        preco=request.POST.get('preco') or 0
    )

    return JsonResponse({
        'status': 'ok',
        'produto': {
            'id': produto.id,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco),
        }
    })


@login_required
@require_POST
def excluir_produto(request, id):
    if request.method == 'POST':
        try:
            produto = Produto.objects.get(id=id)
            produto.delete()
            return JsonResponse({'status': 'ok', 'mensagem': 'Produto excluído com sucesso'})
        except Produto.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Produto não encontrado'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'})
@login_required
def editar_produto(request, id):
    try:
        produto = Produto.objects.get(id=id)
        data = {
            'codigo': produto.codigo,
            'nome': produto.nome,
            'descricao': produto.descricao,
            'preco': str(produto.preco)
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'erro': 'Produto não encontrado'}, status=404)

#--------------------------------------------------------

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
        preco=request.POST.get('preco') or 0
    )

    return JsonResponse({
        'status': 'ok',
        'servico': {
            'id': servico.id,
            'nome': servico.nome,
            'descricao': servico.descricao,
            'preco': str(servico.preco),
        }
    })


    
@login_required
@require_POST
def editar_servico_ajax(request, id):
    try:
        servico = Servico.objects.get(id=id)
        data = {
            'codigo': servico.codigo,
            'nome': servico.nome,
            'descricao': servico.descricao,
            'preco': str(servico.preco)
        }
        return JsonResponse(data)
    except Servico.DoesNotExist:
        return JsonResponse({'erro': 'Serviço não encontrado'}, status=404)
@login_required
def excluir_servico_ajax(request, id):
    if request.method == 'POST':
        try:
            servico = Servico.objects.get(id=id)
            servico.delete()
            return JsonResponse({'status': 'ok', 'mensagem': 'Serviço excluído com sucesso'})
        except Servico.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Serviço não encontrado'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'})


# --------------------------------------------------------
# ORÇAMENTOS
# --------------------------------------------------------

@login_required
def listar_orcamentos(request):
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return redirect('core:selecionar_empresa')

    orcamentos = Orcamento.objects.filter(empresa_id=empresa_id).order_by('-criado_em')
    clientes = Cliente.objects.filter(empresa_id=empresa_id)

    return render(request, 'orcamentos.html', {
        'orcamentos': orcamentos,
        'clientes': clientes,
    })


@login_required
@require_POST
def criar_orcamento(request):
    try:
        data = request.POST
        empresa = get_empresa_do_usuario(request.user)
        itens = json.loads(data.get('itens', '[]'))
        desconto = float(data.get('desconto', 0) or 0)

        orcamento = Orcamento.objects.create(
            empresa=empresa,
            usuario=request.user,
            cliente_id=data.get('cliente'),
            solicitante=data.get('solicitante'),
            previsao_entrega=data.get('previsao_entrega') or None,
            forma_pagamento=data.get('forma_pagamento'),
            vencimento=data.get('vencimento') or None,
            observacao=data.get('observacao'),
            responsavel=data.get('responsavel'),
            desconto=desconto,
        )

        total = 0
        for item in itens:
            tipo = item.get('tipo')
            qtd = float(item.get('quantidade') or 0)
            valor = float(item.get('valor_unitario') or 0)
            subtotal = qtd * valor
            total += subtotal

            model = Produto if tipo == 'produto' else Servico
            ref = model.objects.filter(id=item.get('id_item')).first()

            ItemOrcamento.objects.create(
                orcamento=orcamento,
                produto=ref if tipo == 'produto' else None,
                servico=ref if tipo == 'servico' else None,
                quantidade=qtd,
                preco_unitario=valor
            )

        orcamento.save()
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

    try:
        data = request.POST
        itens = json.loads(data.get('itens', '[]'))
        desconto = float(data.get('desconto', 0) or 0)

        orcamento.cliente_id = data.get('cliente')
        orcamento.solicitante = data.get('solicitante')
        orcamento.previsao_entrega = data.get('previsao_entrega') or None
        orcamento.forma_pagamento = data.get('forma_pagamento')
        orcamento.vencimento = data.get('vencimento') or None
        orcamento.observacao = data.get('observacao')
        orcamento.responsavel = data.get('responsavel')
        orcamento.desconto = desconto

        # Limpa itens antigos
        ItemOrcamento.objects.filter(orcamento=orcamento).delete()

        total = 0
        for item in itens:
            tipo = item.get('tipo')
            qtd = float(item.get('quantidade') or 0)
            valor = float(item.get('valor_unitario') or 0)
            subtotal = qtd * valor
            total += subtotal

            model = Produto if tipo == 'produto' else Servico
            ref = model.objects.filter(id=item.get('id_item')).first()

            ItemOrcamento.objects.create(
                orcamento=orcamento,
                produto=ref if tipo == 'produto' else None,
                servico=ref if tipo == 'servico' else None,
                quantidade=qtd,
                preco_unitario=valor
            )

        orcamento.save()
        return JsonResponse({'status': 'ok'})

    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': str(e)})

@login_required
def obter_orcamento(request, orcamento_id):
    """Retorna os dados de um orçamento para edição (GET)."""
    if request.method != "GET":
        return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)

    orc = get_object_or_404(Orcamento, id=orcamento_id)
    itens = ItemOrcamento.objects.filter(orcamento=orc)

    data = {
        'id': orc.id,
        'cliente_id': orc.cliente_id,
        'cliente_nome': orc.cliente.razao_social if orc.cliente else '',
        'solicitante': orc.solicitante,
        'previsao_entrega': orc.previsao_entrega.strftime('%Y-%m-%d') if orc.previsao_entrega else '',
        'vencimento': orc.vencimento.strftime('%Y-%m-%d') if orc.vencimento else '',
        'forma_pagamento': orc.forma_pagamento,
        'responsavel': orc.responsavel,
        'desconto': float(orc.desconto or 0),
        'observacao': orc.observacao or '',
        'itens': [
            {
                'id_item': i.produto.id if i.produto else (i.servico.id if i.servico else None),
                'nome': i.produto.nome if i.produto else (i.servico.nome if i.servico else ''),
                'tipo': 'produto' if i.produto else 'servico',
                'quantidade': float(i.quantidade),
                'valor_unitario': float(i.preco_unitario),
            }
            for i in itens
        ]
    }

    return JsonResponse({'status': 'ok', 'orcamento': data})


@login_required
@require_POST
def excluir_orcamento(request, orcamento_id):
    orcamento = get_object_or_404(
        Orcamento,
        id=orcamento_id,
        empresa_id=request.session.get('empresa_id')  # ajuste se o nome da session for diferente
    )
    try:
        orcamento.delete()
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "erro", "mensagem": str(e)})


@login_required
def imprimir_orcamento(request, orcamento_id):
    empresa_id = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa_id)
    itens = ItemOrcamento.objects.filter(orcamento=orcamento)

    return render(request, 'imprimir.html', {
        'orcamento': orcamento,
        'itens': itens,
    })

@login_required
def orcamento_detalhe_json(request, orcamento_id):
    """Retorna os dados do orçamento em JSON para o modal de edição."""
    empresa_id = request.session.get('empresa_id')
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=empresa_id)
    itens = ItemOrcamento.objects.filter(orcamento=orcamento)

    data = {
        'id': orcamento.id,
        'cliente_id': orcamento.cliente.id if orcamento.cliente else None,
        'cliente_nome': orcamento.cliente.razao_social if orcamento.cliente else '',
        'solicitante': orcamento.solicitante,
        'previsao_entrega': orcamento.previsao_entrega.strftime('%Y-%m-%d') if orcamento.previsao_entrega else '',
        'vencimento': orcamento.vencimento.strftime('%Y-%m-%d') if orcamento.vencimento else '',
        'forma_pagamento': orcamento.forma_pagamento,
        'responsavel': orcamento.responsavel,
        'observacao': orcamento.observacao,
        'desconto': float(orcamento.desconto or 0),
        'itens': [
            {
                'id_item': i.produto.id if i.produto else (i.servico.id if i.servico else None),
                'tipo': 'produto' if i.produto else 'servico',
                'nome': i.produto.nome if i.produto else (i.servico.nome if i.servico else ''),
                'quantidade': float(i.quantidade),
                'valor_unitario': float(i.preco_unitario),
            }
            for i in itens
        ]
    }
    return JsonResponse({'status': 'ok', 'orcamento': data})


@login_required
@require_POST
def editar_orcamento(request, orcamento_id):
    """Salva alterações em um orçamento existente."""
    if request.method != "POST":
        return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido (use POST)'}, status=405)

    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=request.session.get('empresa_id'))
    try:
        data = request.POST
        itens = json.loads(data.get('itens', '[]'))
        desconto = float(data.get('desconto', 0) or 0)

        orcamento.cliente_id = data.get('cliente')
        orcamento.solicitante = data.get('solicitante')
        orcamento.previsao_entrega = data.get('previsao_entrega') or None
        orcamento.vencimento = data.get('vencimento') or None
        orcamento.forma_pagamento = data.get('forma_pagamento')
        orcamento.observacao = data.get('observacao')
        orcamento.responsavel = data.get('responsavel')
        orcamento.desconto = desconto

        # Remove os itens antigos
        ItemOrcamento.objects.filter(orcamento=orcamento).delete()

        total = 0
        for item in itens:
            tipo = item.get('tipo')
            qtd = float(item.get('quantidade') or 0)
            valor = float(item.get('valor_unitario') or 0)
            subtotal = qtd * valor
            total += subtotal

            model = Produto if tipo == 'produto' else Servico
            ref = model.objects.filter(id=item.get('id_item')).first()

            ItemOrcamento.objects.create(
                orcamento=orcamento,
                produto=ref if tipo == 'produto' else None,
                servico=ref if tipo == 'servico' else None,
                quantidade=qtd,
                preco_unitario=valor
            )

        orcamento.save()
        return JsonResponse({'status': 'ok'})

    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': str(e)})




# --------------------------------------------------------
# ITENS DE ORÇAMENTO INDIVIDUAIS (caso use via AJAX)
# --------------------------------------------------------

@login_required
@require_POST
def adicionar_item(request, orcamento_id):
    orcamento = get_object_or_404(Orcamento, id=orcamento_id, empresa_id=request.session.get('empresa_id'))
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
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))
    form = ItemOrcamentoForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro', 'erros': form.errors})


@login_required
@require_POST
def excluir_item(request, item_id):
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))
    item.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def detalhe_item(request, item_id):
    item = get_object_or_404(ItemOrcamento, id=item_id, orcamento__empresa_id=request.session.get('empresa_id'))
    data = {
        'id': item.id,
        'produto': {'id': item.produto.id, 'nome': item.produto.nome} if item.produto else None,
        'servico': {'id': item.servico.id, 'nome': item.servico.nome} if item.servico else None,
        'quantidade': item.quantidade,
        'preco_unitario': float(item.preco_unitario),
    }
    return JsonResponse(data)


# --------------------------------------------------------
# AUTOCOMPLETES
# --------------------------------------------------------

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
@login_required
def utf8_json_response(data):
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@login_required
def autocomplete_cliente(request):
    empresa_id = request.session.get('empresa_id')
    term = request.GET.get('term', '')
    cliente_id = request.GET.get('id')

    clientes = Cliente.objects.filter(empresa_id=empresa_id)

    if cliente_id:
        clientes = clientes.filter(id=cliente_id)
    elif term:
        clientes = clientes.filter(razao_social__icontains=term)

    results = [
        {
            "id": c.id,
            "label": c.razao_social,
            "nome_fantasia": c.nome_fantasia,
            "cpf_cnpj": c.cpf_cnpj,
            "email": c.email,
            "telefone": c.telefone,
            "endereco": c.endereco,
        }
        for c in clientes
    ]
    return JsonResponse(results, safe=False)


@login_required
def autocomplete_produto_servico(request):
    termo = request.GET.get('term', '')
    produtos = Produto.objects.filter(nome__icontains=termo)
    servicos = Servico.objects.filter(nome__icontains=termo)

    resultados = []
    for p in produtos:
        resultados.append({
            "id": p.id,
            "label": p.nome,
            "tipo": "produto",
            "preco": float(p.preco)
        })
    for s in servicos:
        resultados.append({
            "id": s.id,
            "label": s.nome,
            "tipo": "servico",
            "preco": float(s.preco)
        })
    return JsonResponse(resultados, safe=False)


# --------------------------------------------------------
# OUTROS
# --------------------------------------------------------

@login_required
@require_POST
def configuracoes(request):
    empresa = get_empresa_do_usuario(request.user)
    if not empresa:
        return redirect('core:index')

    context = {
        'clientes_list': Cliente.objects.filter(empresa=empresa),
        'produtos_list': Produto.objects.filter(empresa=empresa),
        'servicos_list': Servico.objects.filter(empresa=empresa),
    }
    context['empresa'] = empresa
    return render(request, 'configuracoes.html', context, ) 


@login_required
def suporte(request):
    empresa = get_empresa_do_usuario(request.user)
    modulos = ['Financeiro', 'Dashboard', 'Orçamentos', 'Configurações', 'Relatórios', 'Outro']
    
    context = {
    'usuario': request.user,
    'modulos': modulos,
    'empresa': empresa,
}
    return render(request, 'suporte.html', context)


from django.db import models
from datetime import date
from django.contrib.auth.models import User

# ------------------------
# EMPRESA
# ------------------------
class Empresa(models.Model):
    nome = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nome


# ------------------------
# RELAÇÃO USUÁRIO X EMPRESA
# ------------------------
class UserEmpresa(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'empresa')
        verbose_name = "Usuário da Empresa"
        verbose_name_plural = "Usuários da Empresa"

    def __str__(self):
        return f"{self.user.username} - {self.empresa.nome}"


# ------------------------
# PRODUTOS
# ------------------------
class Produto(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50, blank=True)
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"


# ------------------------
# CLIENTES
# ------------------------
class Cliente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cpf_cnpj = models.CharField(max_length=50, blank=True)
    telefone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade_uf = models.CharField(max_length=100, blank=True)
    cep = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.razao_social


# ------------------------
# SERVIÇOS
# ------------------------
class Servico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50, blank=True)
    nome = models.CharField(max_length=200)
    preco = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"


# ------------------------
# ORÇAMENTO (CABEÇALHO)
# ------------------------
class Orcamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    numero = models.PositiveIntegerField(editable=False, unique=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    previsao_entrega = models.DateField(null=True, blank=True)
    solicitante = models.CharField(max_length=200, blank=True)
    servicos_descricao = models.TextField(blank=True)
    escopo = models.TextField(blank=True)
    local_uso = models.CharField(max_length=255, blank=True)
    responsavel = models.CharField(max_length=200, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    observacao = models.TextField(blank=True)
    forma_pagamento = models.CharField(max_length=100, blank=True)
    vencimento = models.DateField(null=True, blank=True)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-criado_em']

    @property
    def subtotal(self):
        return sum([it.quantidade * float(it.preco_unitario) for it in self.itens.all()])

    @property
    def total(self):
        return self.subtotal - float(self.desconto or 0)

    def save(self, *args, **kwargs):
        
        if not self.numero:
            ano = date.today().year
            ultimo = Orcamento.objects.filter(
                empresa=self.empresa,
                criado_em__year=ano
            ).order_by('-numero').first()
            self.numero = (ultimo.numero + 1) if ultimo else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Orçamento #{self.numero} - {self.cliente.razao_social}"


# ------------------------
# ITENS DO ORÇAMENTO
# ------------------------
class ItemOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        nome = self.produto.nome if self.produto else (self.servico.nome if self.servico else "Item")
        return f"{nome} x{self.quantidade}"

        
from django.db import models
from django.contrib.auth.models import User

class InventoryItem(models.Model):
    nome = models.CharField(max_length=200)
    quantidade = models.IntegerField()
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.nome

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=150, blank=True, null=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.cpf}"


class Venda(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    data_venda = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venda #{self.id} para {self.cliente.nome} em {self.data_venda.strftime('%d/%m/%Y')}"
    
    def total(self):
        return sum(item.quantidade * item.preco_unitario for item in self.itens.all())

class ItemVenda(models.Model):
    venda = models.ForeignKey('Venda', on_delete=models.CASCADE, related_name='itens')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.item.quantidade >= self.quantidade:
                self.item.quantidade -= self.quantidade
                self.item.save()
            else:
                raise ValueError(f"Estoque insuficiente para o item {self.item.nome}.")
        super().save(*args, **kwargs)

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.item.nome} na venda #{self.venda.id}"
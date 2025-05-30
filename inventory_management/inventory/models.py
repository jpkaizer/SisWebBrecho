from django.db import models
from django.contrib.auth.models import User

class InventoryItem(models.Model):
    nome = models.CharField(max_length=200)
    quantidade = models.IntegerField()
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, blank=True, null=True)
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
from django.contrib import admin
from .models import InventoryItem, Categoria
from .models import Cliente

admin.site.register(InventoryItem)
admin.site.register(Categoria)


admin.site.register(Cliente)

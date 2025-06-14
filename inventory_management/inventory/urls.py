from django.contrib import admin
from django.urls import path
from .views import Index, Dashboard, AddItem, EditItem, DeleteItem, RealizarVenda, RelatorioSemanalExcel, PaginaPedidos
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name= 'edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name = 'delete-item'),
    path('vendas/', RealizarVenda.as_view(), name='realizar_venda'),
    path('pedidos/', PaginaPedidos.as_view(), name='pagina_pedidos'),
    path('relatorio/semana/', RelatorioSemanalExcel.as_view(), name='relatorio_semanal'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/logout.html'), name='logout')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

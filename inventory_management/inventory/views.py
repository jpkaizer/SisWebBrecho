from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from .forms import UserRegisterForm, InventoryItemForm
from .models import InventoryItem, Categoria, Cliente, Venda, ItemVenda
import datetime
from django.db import transaction 
from decimal import Decimal
from openpyxl import Workbook
import os

import json


class Index(TemplateView):
    template_name= 'inventory/index.html'


class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        itens = InventoryItem.objects.filter(user=self.request.user.id).order_by('id')
        return render(request, 'inventory/dashboard.html', {'itens': itens})
    
class SignUpView(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, 'inventory/signup.html',{'form': form})
    
    def post(self, request):
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )

            login(request, user)
            return redirect('index')

        return render(request, 'inventory/signup.html', {'form': form})
    

class AddItem(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class EditItem(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')


class DeleteItem(LoginRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = 'inventory/delete_item.html'
    success_url = reverse_lazy('dashboard')
    context_object_name = 'item'


class RealizarVenda(View):
    def get(self, request):
        itens = InventoryItem.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        return render(request, 'inventory/realizar_venda.html', {
            'itens': itens,
            'clientes': clientes
        })

    def post(self, request):
        cliente_id = request.POST.get('cliente')
        itens_json = request.POST.get('itens')

        if not cliente_id:
            return self.render_erro(request, 'Selecione um cliente.')

        if not itens_json:
            return self.render_erro(request, 'Nenhum item foi selecionado para a venda.')

        try:
            itens_data = json.loads(itens_json)
        except json.JSONDecodeError:
            return self.render_erro(request, 'Erro ao processar os dados dos itens.')

        if not itens_data:
            return self.render_erro(request, 'A lista de itens está vazia.')

        try:
            with transaction.atomic():
                cliente = Cliente.objects.get(id=cliente_id)
                venda = Venda.objects.create(cliente=cliente)

                for item_info in itens_data:
                    item = InventoryItem.objects.get(id=item_info['item_id'], user=request.user)
                    quantidade = int(item_info['quantidade'])

                    if quantidade <= 0:
                        raise ValueError("Quantidade inválida")
                    if quantidade > item.quantidade:
                        raise ValueError(f'Estoque insuficiente para o item {item.nome}.')

                    ItemVenda.objects.create(
                        venda=venda,
                        item=item,
                        quantidade=quantidade,
                        preco_unitario=item.preco
                    )

                    item.quantidade -= quantidade
                    item.save()

        except Exception as e:
            return self.render_erro(request, f'Erro ao adicionar item: {str(e)}')

        messages.success(request, f'Venda #{venda.id} realizada com sucesso!')
        return redirect('realizar_venda')

    def render_erro(self, request, erro_msg):
        itens = InventoryItem.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        print("Tá renderizando realizar_venda.html de verdade!")
        return render(request, 'inventory/realizar_venda.html', {
            'itens': itens,
            'clientes': clientes,
            'erro': erro_msg
        })


class RelatorioSemanalExcel(LoginRequiredMixin, View):
    def get(self, request):
        hoje = datetime.date.today()
        segunda = hoje - datetime.timedelta(days=hoje.weekday())  
        vendas = Venda.objects.filter(data_venda__date__gte=segunda)

        total_geral = 0
        wb = Workbook()
        ws = wb.active
        ws.title = "Relatório Semanal"

        ws.append(["ID Venda", "Data", "Cliente", "Total da Venda (R$)"])

        for venda in vendas:
            total = sum(item.quantidade * item.preco_unitario for item in venda.itens.all())
            total_geral += total
            ws.append([
                venda.id,
                venda.data_venda.strftime('%d/%m/%Y %H:%M'),
                venda.cliente.nome,
                f"{total:.2f}".replace('.', ',')
            ])

        ws.append([])
        ws.append(["", "", "Total Geral:", f"{total_geral:.2f}".replace('.', ',')])

        
        nome_arquivo = f"relatorio_semanal_{hoje.strftime('%Y%m%d')}.xlsx"
        caminho_pasta = os.path.join(settings.MEDIA_ROOT, 'relatorios')
        os.makedirs(caminho_pasta, exist_ok=True)
        caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)

        wb.save(caminho_arquivo)

        
        with open(caminho_arquivo, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={nome_arquivo}'
            return response
        

class PaginaPedidos(LoginRequiredMixin, View):
    def get(self, request):
        pedidos = Venda.objects.select_related('cliente').prefetch_related('itens__item').order_by('-data_venda')
        return render(request, 'inventory/pedidos.html', {'pedidos': pedidos})

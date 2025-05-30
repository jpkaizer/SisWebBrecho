from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm
from .models import InventoryItem, Categoria

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
        itens = ItemInventario.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        voltar_para = request.GET.get('next', '/dashboard/')
        return render(request, 'inventory/realizar_venda.html', {
            'itens': itens,
            'clientes': clientes,
            'voltar_para': voltar_para
        })

    def post(self, request):
        itens = ItemInventario.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        cliente_id = request.POST.get('cliente')
        itens_json = request.POST.get('itens')

        if not cliente_id:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'Selecione um cliente.'
            })

        if not itens_json:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'Nenhum item foi selecionado para a venda.'
            })

        try:
            itens_data = json.loads(itens_json)
        except json.JSONDecodeError:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'Erro ao processar os dados dos itens.'
            })

        if not itens_data:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'A lista de itens está vazia.'
            })

        cliente = Cliente.objects.get(id=cliente_id)

        with transaction.atomic():
            venda = Venda.objects.create(cliente=cliente)
            for item_info in itens_data:
                try:
                    item = ItemInventario.objects.get(id=item_info['item_id'], user=request.user)
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
                    transaction.set_rollback(True)
                    return render(request, 'inventory/realizar_venda.html', {
                        'itens': itens,
                        'clientes': clientes,
                        'erro': f'Erro ao adicionar item: {str(e)}'
                    })

        messages.success(request, f'Venda #{venda.id} realizada com sucesso!')
        return redirect('pagina_pedidos')


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

        # Salvar na pasta media/relatorios


        nome_arquivo = f"relatorio_semanal_{hoje.strftime('%Y%m%d')}.xlsx"
        caminho_pasta = os.path.join(settings.MEDIA_ROOT, 'relatorios')
        os.makedirs(caminho_pasta, exist_ok=True)
        caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)

        wb.save(caminho_arquivo)

        # Também retornar como download
        with open(caminho_arquivo, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={nome_arquivo}'
            return response

class PaginaPedidos(LoginRequiredMixin, View):
    def get(self, request):
        pedidos = Venda.objects.select_related('cliente').prefetch_related('itens__item').order_by('-data_venda')
        return render(request, 'inventory/pedidos.html', {'pedidos': pedidos})
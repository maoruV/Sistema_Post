from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Client
from .forms import ClientForm
from apps.accounts.decorators import role_required


@login_required
def client_list(request):
    qs = Client.objects.all().order_by('name')

    q = request.GET.get('q', '').strip()

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(phone__icontains=q) |
            Q(cc__icontains=q)
        )

    paginator = Paginator(qs, 6)
    page = request.GET.get('page', 1)
    clients_page = paginator.get_page(page)

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'clients/client_list_partial.html', {
            'clients': clients_page, 'page_obj': clients_page
        })

    return render(request, 'clients/client_list.html', {
        'clients': clients_page,
        'page_obj': clients_page,
        'current_q': q,
    })


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente.')
            return redirect('clients:client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Crear Cliente'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('clients:client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {'form': form, 'title': 'Editar Cliente'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente eliminado correctamente.')
        return redirect('clients:client_list')
    return render(request, 'clients/client_confirm_delete.html', {'client': client})


@login_required
def client_search(request):
    q = request.GET.get('q', '')
    clients = Client.objects.filter(name__icontains=q)[:10]
    data = [{'id': c.id, 'text': c.name} for c in clients]
    return JsonResponse(data, safe=False)

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .models import Sale, SaleItem
from .utils import next_invoice_number

User = get_user_model()
from .forms import SaleForm
from apps.inventory.models import Product
from apps.clients.models import Client
from apps.accounts.decorators import role_required


@login_required
def sale_list(request):
    qs = Sale.objects.select_related('client', 'user').all().order_by('-date')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(
            Q(client__name__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q)
        )
    if status:
        if status == 'cancelada':
            qs = qs.filter(is_active=False)
        elif status == 'pagada':
            qs = qs.filter(is_active=True, status='pagada')
        elif status == 'pendiente':
            qs = qs.filter(is_active=True, status='pendiente')

    paginator = Paginator(qs, 6)
    page = request.GET.get('page', 1)
    sales_page = paginator.get_page(page)

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'sales/sale_list_partial.html', {'sales': sales_page, 'page_obj': sales_page})

    return render(request, 'sales/sale_list.html', {
        'sales': sales_page,
        'page_obj': sales_page,
        'current_q': q,
        'current_status': status,
    })


@login_required
def sale_new(request):
    form = SaleForm()
    return render(request, 'sales/sale_new.html', {'form': form})


@login_required
@require_POST
def add_item(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    product = get_object_or_404(Product, pk=data.get('product_id'))
    if not product.is_active:
        return JsonResponse({'error': f'{product.name} está inactivo. No se puede agregar a la venta.'}, status=400)
    if product.stock < int(data['quantity']):
        return JsonResponse({'error': f'Stock insuficiente. Disponible: {product.stock}'}, status=400)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'price': float(product.price),
        'quantity': int(data['quantity']),
        'subtotal': float(product.price) * int(data['quantity']),
        'stock': product.stock,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('client', 'user'), pk=pk)
    items = sale.items.select_related('product').all()
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items})


@login_required
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('client', 'user'), pk=pk)
    items = sale.items.select_related('product').all()
    return render(request, 'sales/sale_invoice.html', {'sale': sale, 'items': items})


@login_required
@require_POST
@transaction.atomic
def sale_complete(request):
    try:
        data = json.loads(request.POST.get('sale_data', '{}'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')

    items_data = data.get('items', [])
    client_id = data.get('client_id')
    payment_method = data.get('payment_method', 'efectivo')
    status = data.get('status', Sale.Status.PAID)
    amount_received = data.get('amount_received')

    if not items_data:
        return JsonResponse({'error': 'No hay productos en la venta'}, status=400)

    invoice_number = next_invoice_number('VNT')

    sale = Sale.objects.create(
        invoice_number=invoice_number,
        client_id=client_id or None,
        user=request.user,
        payment_method=payment_method,
        status=status,
    )

    product_ids = [item['product_id'] for item in items_data]
    products = {p.id: p for p in Product.objects.filter(pk__in=product_ids).select_for_update()}

    subtotal_sum = 0
    for item_data in items_data:
        product = products.get(item_data['product_id'])
        if not product:
            raise ValueError(f'Producto {item_data["product_id"]} no encontrado')
        quantity = int(item_data['quantity'])
        unit_price = float(item_data['unit_price'])
        item_subtotal = quantity * unit_price

        if product.stock < quantity:
            raise ValueError(f'Stock insuficiente para {product.name}')

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=item_subtotal,
        )

        product.stock -= quantity
        product.save()
        subtotal_sum += item_subtotal

    sale.subtotal = subtotal_sum
    apply_iva = data.get('apply_iva', False)
    sale.tax = subtotal_sum * 0.19 if apply_iva else 0
    sale.total = subtotal_sum + sale.tax
    if amount_received and payment_method == 'efectivo':
        amount_rec = float(amount_received)
        sale.amount_received = amount_rec
        sale.change = max(0, amount_rec - sale.total)
    sale.save()

    messages.success(request, f'Venta {invoice_number} completada correctamente.')
    return redirect('sales:sale_detail', pk=sale.pk)


@login_required
def sale_collect(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('client', 'user'), pk=pk)
    items = sale.items.select_related('product').all()
    if sale.status != Sale.Status.PENDING or not sale.is_active:
        messages.error(request, 'Esta venta no está pendiente.')
        return redirect('sales:sale_list')
    return render(request, 'sales/sale_collect.html', {'sale': sale, 'items': items})


@login_required
@require_POST
@role_required(allowed_roles=['admin', 'supervisor'])
def sale_collect_save(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != Sale.Status.PENDING or not sale.is_active:
        messages.error(request, 'Esta venta no está pendiente.')
        return redirect('sales:sale_list')

    payment_method = request.POST.get('payment_method', 'efectivo')
    amount_received = request.POST.get('amount_received')
    change = request.POST.get('change', 0)

    sale.payment_method = payment_method
    sale.status = Sale.Status.PAID
    if payment_method == 'efectivo' and amount_received:
        sale.amount_received = float(amount_received)
        sale.change = float(change) if change else 0
    sale.save()

    messages.success(request, f'Venta {sale.invoice_number} cobrada correctamente.')
    return redirect('sales:sale_detail', pk=sale.pk)


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
@require_POST
def sale_pay(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != Sale.Status.PENDING:
        messages.error(request, f'La venta {sale.invoice_number} no está pendiente.')
        return redirect('sales:sale_list')
    if not sale.is_active:
        messages.error(request, f'La venta {sale.invoice_number} está cancelada.')
        return redirect('sales:sale_list')
    sale.status = Sale.Status.PAID
    sale.save()
    messages.success(request, f'Venta {sale.invoice_number} marcada como pagada.')
    return redirect('sales:sale_list')


@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('client', 'user'), pk=pk)
    items = sale.items.select_related('product').all()
    products = Product.objects.filter(is_active=True, stock__gt=0).select_related('category')
    if sale.status != Sale.Status.PENDING or not sale.is_active:
        messages.error(request, 'Solo se pueden editar ventas pendientes.')
        return redirect('sales:sale_list')
    import json
    items_json = json.dumps([{
        'id': i.product.id,
        'name': i.product.name,
        'sku': i.product.sku,
        'price': float(i.product.price),
        'quantity': i.quantity,
        'subtotal': float(i.subtotal),
    } for i in items if i.product])
    return render(request, 'sales/sale_edit.html', {
        'sale': sale,
        'items': items,
        'products': products,
        'items_json': items_json,
    })


@login_required
@require_POST
@transaction.atomic
@role_required(allowed_roles=['admin', 'supervisor'])
def sale_edit_save(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status != Sale.Status.PENDING or not sale.is_active:
        return JsonResponse({'error': 'Venta no editable'}, status=400)

    try:
        data = json.loads(request.POST.get('items_data', '{}'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')

    new_items = data.get('items', [])
    if not new_items:
        messages.info(request, 'No se agregaron productos nuevos.')
        return redirect('sales:sale_detail', pk=sale.pk)

    product_ids = [item['product_id'] for item in new_items]
    products = {p.id: p for p in Product.objects.filter(pk__in=product_ids).select_for_update()}

    added_subtotal = 0
    for item_data in new_items:
        product = products.get(item_data['product_id'])
        if not product:
            continue
        if not product.is_active:
            messages.error(request, f'{product.name} está inactivo.')
            return redirect('sales:sale_edit', pk=sale.pk)
        quantity = int(item_data['quantity'])
        unit_price = float(item_data['unit_price'])
        item_subtotal = quantity * unit_price
        if product.stock < quantity:
            messages.error(request, f'Stock insuficiente para {product.name}')
            return redirect('sales:sale_edit', pk=sale.pk)
        SaleItem.objects.create(
            sale=sale, product=product, quantity=quantity,
            unit_price=unit_price, subtotal=item_subtotal,
        )
        product.stock -= quantity
        product.save()
        added_subtotal += item_subtotal

    sale.subtotal = float(sale.subtotal) + added_subtotal
    if sale.tax > 0:
        sale.tax = sale.subtotal * 0.19
        sale.total = sale.subtotal + sale.tax
    else:
        sale.tax = 0
        sale.total = sale.subtotal
    sale.save()

    messages.success(request, f'Productos agregados a {sale.invoice_number}.')
    return redirect('sales:sale_detail', pk=sale.pk)


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def sale_cancel(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in sale.items.all():
                product = item.product
                if product:
                    product.stock += item.quantity
                    product.save()
            sale.is_active = False
            sale.save()
        messages.success(request, 'Venta cancelada y stock restaurado.')
        return redirect('sales:sale_list')
    return render(request, 'sales/sale_confirm_cancel.html', {'sale': sale})

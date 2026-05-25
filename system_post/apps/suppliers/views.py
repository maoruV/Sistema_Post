from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Supplier, SupplierInvoice
from .forms import SupplierForm, SupplierInvoiceForm
from apps.accounts.decorators import role_required


@login_required
def supplier_list(request):
    qs = Supplier.objects.all().order_by('name')

    q = request.GET.get('q', '').strip()

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q)
        )

    paginator = Paginator(qs, 6)
    page = request.GET.get('page', 1)
    suppliers_page = paginator.get_page(page)

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'suppliers/supplier_list_partial.html', {
            'suppliers': suppliers_page, 'page_obj': suppliers_page
        })

    return render(request, 'suppliers/supplier_list.html', {
        'suppliers': suppliers_page,
        'page_obj': suppliers_page,
        'current_q': q,
    })


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado correctamente.')
            return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Crear Proveedor'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Editar Proveedor'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Proveedor eliminado correctamente.')
        return redirect('suppliers:supplier_list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})


@login_required
def invoice_list(request):
    qs = SupplierInvoice.objects.select_related('supplier').all().order_by('-date')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(supplier__name__icontains=q)
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 6)
    page = request.GET.get('page', 1)
    invoices_page = paginator.get_page(page)

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'suppliers/invoice_list_partial.html', {
            'invoices': invoices_page, 'page_obj': invoices_page
        })

    return render(request, 'suppliers/invoice_list.html', {
        'invoices': invoices_page,
        'page_obj': invoices_page,
        'current_q': q,
        'current_status': status,
    })


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def invoice_create(request):
    if request.method == 'POST':
        form = SupplierInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Factura creada correctamente.')
            return redirect('suppliers:invoice_list')
    else:
        form = SupplierInvoiceForm()
    return render(request, 'suppliers/invoice_form.html', {'form': form, 'title': 'Crear Factura'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def invoice_update(request, pk):
    invoice = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        form = SupplierInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Factura actualizada correctamente.')
            return redirect('suppliers:invoice_list')
    else:
        form = SupplierInvoiceForm(instance=invoice)
    return render(request, 'suppliers/invoice_form.html', {'form': form, 'title': 'Editar Factura'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def invoice_delete(request, pk):
    invoice = get_object_or_404(SupplierInvoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Factura eliminada correctamente.')
        return redirect('suppliers:invoice_list')
    return render(request, 'suppliers/invoice_confirm_delete.html', {'invoice': invoice})

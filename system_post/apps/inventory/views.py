from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Category, Product
from .forms import CategoryForm, ProductForm
from apps.accounts.decorators import role_required


@login_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    paginator = Paginator(categories, 6)
    page = request.GET.get('page', 1)
    categories_page = paginator.get_page(page)
    return render(request, 'inventory/category_list.html', {'categories': categories_page, 'page_obj': categories_page})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Crear Categoría'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Editar Categoría'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Categoría eliminada correctamente.')
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})


@login_required
def product_list(request):
    products = Product.objects.select_related('category').all().order_by('name')
    categories = Category.objects.all().order_by('name')
    paginator = Paginator(products, 6)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    return render(request, 'inventory/product_list.html', {'products': products_page, 'categories': categories, 'page_obj': products_page})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Crear Producto'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Editar Producto'})


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@login_required
def product_search(request):
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    is_active = request.GET.get('is_active', '')

    filters = Q(name__icontains=q) | Q(sku__icontains=q) | Q(category__name__icontains=q)

    if category_id:
        filters &= Q(category_id=category_id)
    if is_active == 'activo':
        filters &= Q(is_active=True)
    elif is_active == 'inactivo':
        filters &= Q(is_active=False)

    products = Product.objects.filter(filters).select_related('category')[:6]

    if request.GET.get('format') == 'json':
        data = [{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'category_name': p.category.name if p.category else None,
            'price': float(p.price),
            'stock': p.stock,
            'is_active': p.is_active,
            'is_low_stock': p.is_low_stock,
        } for p in products]
        return JsonResponse(data, safe=False)

    return render(request, 'inventory/product_search_results.html', {'products': products})

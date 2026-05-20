from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db import models
from django.utils import timezone
from apps.inventory.models import Product
from apps.sales.models import Sale, SaleItem
from apps.clients.models import Client
from apps.suppliers.models import Supplier


@login_required
def dashboard(request):
    today = timezone.localdate()

    low_stock_products = Product.objects.filter(is_active=True, stock__lte=models.F('min_stock')).count()
    total_products = Product.objects.filter(is_active=True).count()
    total_clients = Client.objects.count()
    total_suppliers = Supplier.objects.count()

    today_sales = Sale.objects.filter(
        is_active=True,
        status='pagada',
        date__date=today
    ).aggregate(total=Sum('total'), count=Count('id'))

    recent_sales = Sale.objects.filter(
        is_active=True, status='pagada'
    ).select_related('client', 'user').order_by('-date')[:5]

    top_products = (
        SaleItem.objects
        .filter(sale__is_active=True, sale__status='pagada', product__isnull=False)
        .values('product_id', 'product__name', 'product__sku', 'product__category__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-total_qty')[:6]
    )

    top_category = (
        SaleItem.objects
        .filter(sale__is_active=True, sale__status='pagada', product__isnull=False, product__category__isnull=False)
        .values('product__category__id', 'product__category__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty').first()
    )

    return render(request, 'core/dashboard.html', {
        'low_stock_products': low_stock_products,
        'total_products': total_products,
        'total_clients': total_clients,
        'total_suppliers': total_suppliers,
        'today_sales_total': today_sales['total'] or 0,
        'today_sales_count': today_sales['count'] or 0,
        'recent_sales': recent_sales,
        'top_products': top_products,
        'top_category': top_category,
    })

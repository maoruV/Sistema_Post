from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from apps.sales.models import Sale
from apps.accounts.decorators import role_required


def _get_date_ranges():
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    return today, week_start, month_start


def _get_sales_data(start_date, end_date=None):
    filters = {'is_active': True, 'status': 'pagada', 'date__gte': start_date}
    if end_date:
        filters['date__lt'] = end_date + timedelta(days=1)

    sales = Sale.objects.filter(**filters)
    total = sales.aggregate(
        total=Sum('total'),
        count=Count('id')
    )

    breakdown = sales.values('payment_method').annotate(
        total=Sum('total'),
        count=Count('id')
    )
    payment_breakdown = {p['payment_method']: {'total': float(p['total'] or 0), 'count': p['count']} for p in breakdown}
    for method in ['efectivo', 'tarjeta', 'transferencia']:
        payment_breakdown.setdefault(method, {'total': 0, 'count': 0})

    return {
        'total_sales': float(total['total'] or 0),
        'count': total['count'],
        'payment_breakdown': payment_breakdown,
        'sales': sales.select_related('client', 'user').order_by('-date'),
    }


@login_required
def report_dashboard(request):
    today, week_start, month_start = _get_date_ranges()

    daily = _get_sales_data(today)
    weekly = _get_sales_data(week_start)
    monthly = _get_sales_data(month_start)
    all_time = _get_sales_data(datetime(2000, 1, 1).date())

    return render(request, 'reports/dashboard.html', {
        'daily': daily,
        'weekly': weekly,
        'monthly': monthly,
        'all_time': all_time,
        'today': today,
        'week_start': week_start,
        'month_start': month_start,
    })


def _parse_date_params(request, default_start, default_end):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from and date_to:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            return from_date, to_date, date_from, date_to
        except ValueError:
            pass
    return default_start, default_end, default_start.isoformat(), default_end.isoformat()


@login_required
def report_view(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    preset = request.GET.get('preset', 'hoy')

    if request.user.role == 'user':
        start = end = today
        date_from = date_to = today.isoformat()
    else:
        if preset == 'semana':
            default_start, default_end = week_start, today
        elif preset == 'mes':
            default_start, default_end = month_start, today
        else:
            default_start, default_end = today, today

        start, end, date_from, date_to = _parse_date_params(request, default_start, default_end)

    if start == end:
        title = 'Reporte Diario'
        period = start.strftime('%d/%m/%Y')
    elif start == week_start and end == today:
        title = 'Reporte Semanal'
        period = f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"
    elif start == month_start and end == today:
        title = 'Reporte Mensual'
        period = f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"
    else:
        title = 'Reporte de Ventas'
        period = f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}"

    data = _get_sales_data(start, end)
    sales_qs = data.pop('sales')
    paginator = Paginator(sales_qs, 6)
    page = request.GET.get('page', 1)
    sales_page = paginator.get_page(page)

    return render(request, 'reports/detail.html', {
        'title': title,
        'period': period,
        'data': data,
        'sales': sales_page,
        'page_obj': sales_page,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@role_required(allowed_roles=['admin', 'supervisor'])
def report_data(request):
    period = request.GET.get('period', 'daily')
    today, week_start, month_start = _get_date_ranges()

    ranges = {
        'daily': (today, today),
        'weekly': (week_start, today),
        'monthly': (month_start, today),
    }

    start, end = ranges.get(period, (today, today))
    data = _get_sales_data(start, end)

    return JsonResponse({
        'total_sales': data['total_sales'],
        'count': data['count'],
        'sales': [{
            'invoice': s.invoice_number,
            'client': s.client.name if s.client else 'Mostrador',
            'total': float(s.total),
            'date': s.date.strftime('%d/%m/%Y %H:%M'),
            'user': s.user.get_full_name() or s.user.username if s.user else '',
        } for s in data['sales']],
    })


@login_required
@role_required(allowed_roles=['admin'])
def chart_data(request):
    today = timezone.localdate()
    date_from = request.GET.get('date_from', today.isoformat())
    date_to = request.GET.get('date_to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = end = today

    data = _get_sales_data(start, end)

    daily_raw = (
        Sale.objects
        .filter(is_active=True, status='pagada', date__gte=start, date__lt=end + timedelta(days=1))
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('day')
    )
    daily_totals = [
        {'date': d['day'].strftime('%Y-%m-%d'), 'total': float(d['total'] or 0), 'count': d['count']}
        for d in daily_raw
    ]

    return JsonResponse({
        'payment_breakdown': {
            method: {'total': v['total'], 'count': v['count']}
            for method, v in data['payment_breakdown'].items()
        },
        'daily_totals': daily_totals,
    })

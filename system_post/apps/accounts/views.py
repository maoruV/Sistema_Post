from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import User
from .forms import UserCreateForm, UserUpdateForm, LoginForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('core:dashboard')
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return redirect('accounts:login')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
@admin_required
def user_list(request):
    qs = User.objects.all().order_by('-date_joined')

    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    is_active = request.GET.get('is_active', '')

    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(role__icontains=q) |
            Q(phone__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)
    if is_active:
        qs = qs.filter(is_active=(is_active == 'activo'))

    paginator = Paginator(qs, 6)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'accounts/user_list_partial.html', {
            'users': users_page, 'page_obj': users_page
        })

    return render(request, 'accounts/user_list.html', {
        'users': users_page,
        'page_obj': users_page,
        'current_q': q,
        'current_role': role,
        'current_is_active': is_active,
    })


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Crear Usuario'})


@login_required
@admin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Editar Usuario'})


@login_required
@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

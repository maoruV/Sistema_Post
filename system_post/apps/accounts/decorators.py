from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(allowed_roles=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_admin() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if allowed_roles and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('core:dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin():
            messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Decorator to restrict view access to specific roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to continue.')
                return redirect('login_selector')
            
            try:
                user_role = request.user.profile.role
            except AttributeError:
                messages.error(request, 'User profile not found.')
                return redirect('login_selector')
            
            if user_role not in roles:
                messages.error(
                    request,
                    f'Access denied. This page requires {", ".join(roles)} role.'
                )
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def hospital_required(view_func):
    """Shortcut for requiring HOSPITAL role."""
    return role_required('HOSPITAL')(view_func)


def approver_required(view_func):
    """Shortcut for requiring any approver role."""
    return role_required('JPO', 'PO', 'AS', 'GMM', 'CGM', 'JS','DIRECTOR')(view_func)

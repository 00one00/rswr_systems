"""
Custom decorators for technician portal views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def manager_required(view_func):
    """
    Decorator to restrict view access to managers and staff users only.

    Usage:
        @technician_required
        @manager_required
        def my_manager_view(request):
            # View logic here

    Permissions:
        - Staff users (is_staff=True) can always access
        - Technicians with is_manager=True can access
        - All others are redirected with error message
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Staff users always have access
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Check if user has technician profile with manager status
        if hasattr(request.user, 'technician'):
            technician = request.user.technician
            if technician and technician.is_manager:
                return view_func(request, *args, **kwargs)

        # Access denied
        messages.warning(request, "This page requires manager privileges.")
        return redirect('technician_dashboard')

    return _wrapped_view

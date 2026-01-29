from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import RoleBasedLoginForm, UserRegistrationForm
from .models import UserProfile
from .decorators import role_required
from documents.models import Document
from workflow.models import ApprovalLog


# Role configurations for each login page
ROLE_CONFIG = {
    'HOSPITAL': {
        'name': 'Hospital',
        'title': 'Hospital Portal Login',
        'color': '#2563eb',  # Blue
        'icon': '🏥',
        'template': 'accounts/hospital_login.html',
    },
    'JPO': {
        'name': 'JPO',
        'title': 'Junior Personnel Officer Login',
        'color': '#059669',  # Green
        'icon': '👤',
        'template': 'accounts/jpo_login.html',
    },
    'PO': {
        'name': 'PO',
        'title': 'Assistant Personnel Officer Login',
        'color': '#7c3aed',  # Purple
        'icon': '👥',
        'template': 'accounts/PO_login.html',
    },
    'AS': {
        'name': 'AS',
        'title': 'Assistant Secretary Login',
        'color': '#dc2626',  # Red
        'icon': '📋',
        'template': 'accounts/AS_login.html',
    },
    'GMM': {
        'name': 'FA & CAO',
        'title': 'Financial Advisor & CAO Login',
        'color': '#ca8a04',  # Yellow/Gold
        'icon': '💰',
        'template': 'accounts/GMM_login.html',
    },
    'CGM': {
        'name': 'CGM',
        'title': 'CHIEF GENERAL MANAGER Login',
        'color': '#0891b2',  # Cyan
        'icon': '⚙️',
        'template': 'accounts/de_login.html',
    },
    'JS': {
        'name': 'JS',
        'title': 'Joint Secretary',
        'color': '#be185d',  # Pink
        'icon': '👔',
        'template': 'accounts/se_cgm_login.html',
    },
        'DIRECTOR': {
        'name': 'DIRECTOR',
        'title': 'DIRECTOR_HRD',
        'color': '#be185d',  # Pink
        'icon': '👔',
        'template': 'accounts/se_cgm_login.html',
    },
    'CUSTOMER_ADMIN': {
        'name': 'Customer Admin',
        'title': 'TGNPDCL Admin Portal Login',
        'color': '#4b5563',  # Gray/Slate
        'icon': '🛡️',
        'template': 'accounts/customer_admin_login.html',
    },
}


def login_selector(request):
    """Show all available login options."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/login_selector.html', {
        'roles': ROLE_CONFIG,
    })


def role_login_view(request, role_key):
    """Generic login view for any role."""
    if role_key not in ROLE_CONFIG:
        messages.error(request, 'Invalid login portal.')
        return redirect('login_selector')
    
    config = ROLE_CONFIG[role_key]
    
    if request.method == 'POST':
        form = RoleBasedLoginForm(request, data=request.POST, expected_role=role_key)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
    else:
        form = RoleBasedLoginForm(request, expected_role=role_key)
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'config': config,
        'role_key': role_key,
    })


# Individual login views for each role
def hospital_login(request):
    return role_login_view(request, 'HOSPITAL')

def jpo_login(request):
    return role_login_view(request, 'JPO')

def PO_login(request):
    return role_login_view(request, 'PO')

def AS_login(request):
    return role_login_view(request, 'AS')

def GMM_login(request):
    return role_login_view(request, 'GMM')

def de_login(request):
    return role_login_view(request, 'CGM')

def se_cgm_login(request):
    return role_login_view(request, 'JS')

def director_login(request):
    return role_login_view(request, 'DIRECTOR')

def customer_admin_login(request):
    return role_login_view(request, 'CUSTOMER_ADMIN')


@login_required
def dashboard(request):
    """Main dashboard showing S3 files based on user role."""
    try:
        profile = request.user.profile
        role = profile.role
        role_config = ROLE_CONFIG.get(role, {})
    except AttributeError:
        messages.error(request, 'User profile not found.')
        return redirect('login_selector')
    
    # Redirect specific roles to their dedicated dashboards
    if profile.role == 'HOSPITAL':
        return redirect('hospitals:dashboard')
    elif profile.role == 'CUSTOMER_ADMIN':
        return redirect('workflow:customer_admin_allocation')
    
    # Get all documents (S3 files)
    documents = Document.objects.all().order_by('-uploaded_at')[:10]
    
    # Get recently processed requests by this user
    processed_logs = ApprovalLog.objects.filter(user=request.user).select_related('request', 'step').order_by('-timestamp')[:5]
    
    context = {
        'profile': profile,
        'role_config': role_config,
        'documents': documents,
        'processed_logs': processed_logs,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def logout_view(request):
    """Logout and redirect to login selector."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login_selector')


@login_required
@role_required('CUSTOMER_ADMIN')
def register(request):
    """Handle user creation by Customer Admin."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create the UserProfile
            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data.get('role'),
                designation=form.cleaned_data.get('designation'),
                phone=form.cleaned_data.get('phone'),
                hospital=form.cleaned_data.get('hospital') if form.cleaned_data.get('role') == 'HOSPITAL' else None
            )
            # No auto-login since admin is creating the account
            messages.success(request, f'Member account for {user.username} created successfully!')
            return redirect('register')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'form': form,
    })

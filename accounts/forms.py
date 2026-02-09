from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from .models import UserProfile
from hospitals.models import Hospital


class RoleBasedLoginForm(AuthenticationForm):
    """Login form that validates user role."""
    
    expected_role = None  # Set by view
    
    def __init__(self, *args, expected_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_role = expected_role
        
        # Style the form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'User ID',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Invalid User ID or password.',
                    code='invalid_login',
                )
            
            # Check if user has the required role
            if self.expected_role:
                try:
                    profile = self.user_cache.profile
                    print(f"DEBUG: Login - User: {username}, Expected: '{self.expected_role}', Actual: '{profile.role}'")
                    if profile.role != self.expected_role:
                        print("DEBUG: Role Mismatch!")
                        raise forms.ValidationError(
                            f'You are not authorized to login from this portal. '
                            f'Please use the correct login page for your role.',
                            code='wrong_role',
                        )
                except AttributeError:
                    print("DEBUG: No Profile Found")
                    raise forms.ValidationError(
                        'User profile not found. Please contact administrator.',
                        code='no_profile',
                    )
            
            self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data

class UserRegistrationForm(UserCreationForm):
    """Form for user self-registration."""
    
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    designation = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=15, required=False)
    
    # Conditional field for Hospital
    hospital = forms.ModelChoiceField(
        queryset=Hospital.objects.filter(is_active=True), 
        required=False,
        label="Select Hospital (Required for Hospital Administrators)"
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply standard styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        hospital = cleaned_data.get('hospital')

        if role == 'HOSPITAL' and not hospital:
            self.add_error('hospital', "Please select a hospital for the Hospital Admin role.")
        
        return cleaned_data

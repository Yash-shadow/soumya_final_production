from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory

from accounts.decorators import role_required, hospital_required
from .models import Hospital, Bill, BillDocument, BillItem, Service, Scheme
from .forms import BillForm, BillDocumentForm, BillItemForm
from workflow.models import SanctionRequest, WorkflowStep


@login_required
@hospital_required
def hospital_dashboard(request):
    """Dashboard for hospital users."""
    try:
        hospital = request.user.profile.hospital
    except AttributeError:
        messages.error(request, 'No hospital assigned to your account.')
        return redirect('dashboard')
    
    bills = Bill.objects.filter(hospital=hospital).order_by('-created_at')[:20]
    
    return render(request, 'hospitals/dashboard.html', {
        'hospital': hospital,
        'bills': bills,
    })


@login_required
@hospital_required
def submit_bill(request):
    """View to handle new bill submission with items and amounts."""
    hospital = request.user.profile.hospital
    
    # Create a formset for bill items (Service + Amount)
    BillItemFormSet = modelformset_factory(
        BillItem, 
        form=BillItemForm, 
        extra=0,
        can_delete=False
    )
    
    services = Service.objects.filter(is_active=True)
    
    if request.method == 'POST':
        bill_form = BillForm(request.POST, request.FILES)
        formset = BillItemFormSet(request.POST, request.FILES, queryset=BillItem.objects.none())
        
        if bill_form.is_valid() and formset.is_valid():
            if 'bill_attachment' not in request.FILES:
                messages.error(request, 'Please upload the supporting document for Gross Total (mandatory).')
                return render(request, 'hospitals/submit_bill.html', {
                    'bill_form': bill_form,
                    'formset': formset,
                    'services': services,
                })

            bill = bill_form.save(commit=False)
            bill.hospital = hospital
            
             # Assign default scheme as field is hidden
            default_scheme = Scheme.objects.order_by('id').first()
            if not default_scheme:
                 # Create a default scheme if none exists to avoid error
                 default_scheme, _ = Scheme.objects.get_or_create(
                     name="General Scheme",
                     code="GEN01", 
                     defaults={'description': 'Default Scheme'}
                 )
            bill.scheme = default_scheme
            
            bill.created_by = request.user
            bill.status = 'SUBMITTED'
            bill.save()
            
            # Save items and calculate gross total
            total_amount = 0
            print(f"DEBUG: Processing {len(formset)} forms")
            for i, form in enumerate(formset):
                # Process if Service FK is selected OR if a Custom Name is entered (with amounts)
                # Note: form.cleaned_data might rely on prefix names in template
                if form.cleaned_data.get('service') or form.cleaned_data.get('hospital_service_name'):
                    item = form.save(commit=False)
                    item.bill = bill
                    
                    # Ensure name is captured. If FK exists, use its name as fallback if custom name empty
                    if item.service and not item.hospital_service_name:
                        item.hospital_service_name = item.service.name
                    
                    # DEBUG: Print Item Data
                    print(f"DEBUG item {i}: Rate={item.claimed_rate}, Qty={item.claimed_quantity}, AmountInput={item.claimed_amount}")
                    
                    item.save()  # Model's save() handles calculation if amount is missing
                    
                    print(f"DEBUG item {i} Saved: Amount={item.claimed_amount}")
                    
                    total_amount += item.claimed_amount
            
            print(f"DEBUG: Total Amount Calculated: {total_amount}")
            
            # Update bill with calculated total
            bill.gross_claimed_amount = total_amount
            bill.save()
            
            # Handle Bill Attachment (under Gross Total)
            if 'bill_attachment' in request.FILES:
                BillDocument.objects.create(
                    bill=bill,
                    document_type='OTHER', # Using OTHER as a generic type for now
                    file=request.FILES['bill_attachment']
                )
            
            # Create SanctionRequest to enter workflow
            first_step = WorkflowStep.objects.order_by('order').first()
            SanctionRequest.objects.create(
                bill=bill,
                hospital_name=hospital.name,
                patient_name=bill.patient_name,
                claimed_amount=bill.gross_claimed_amount,
                current_step=first_step,
                status='PENDING'
            )
            
            messages.success(request, 'Bill submitted successfully and entered the approval workflow!')
            return redirect('hospitals:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        bill_form = BillForm()
        # bill_form.fields['scheme'].queryset = Scheme.objects.filter(is_active=True)
        formset = BillItemFormSet(queryset=BillItem.objects.none())
        
    return render(request, 'hospitals/submit_bill.html', {
        'bill_form': bill_form,
        'formset': formset,
        'services': services,
    })


@login_required
@hospital_required
def bill_list(request):
    """List all bills for the hospital."""
    try:
        hospital = request.user.profile.hospital
    except AttributeError:
        messages.error(request, 'No hospital assigned to your account.')
        return redirect('dashboard')
    
    bills = Bill.objects.filter(hospital=hospital).order_by('-created_at')
    
    return render(request, 'hospitals/bill_list.html', {
        'hospital': hospital,
        'bills': bills,
    })


@login_required
def bill_detail(request, bill_id):
    """View bill details with documents."""
    bill = get_object_or_404(Bill, id=bill_id)
    
    # Check access permissions
    profile = request.user.profile
    if profile.role == 'HOSPITAL':
        if profile.hospital != bill.hospital:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    documents = bill.documents.all()
    
    return render(request, 'hospitals/bill_detail.html', {
        'bill': bill,
        'documents': documents,
    })

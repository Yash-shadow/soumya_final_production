from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import approver_required, role_required
from .models import SanctionRequest, ApprovalLog, WorkflowStep


@login_required
@approver_required
def approval_queue(request):
    """Show pending approvals assigned to the current user."""
    profile = request.user.profile
    role = profile.role
    
    # Find ALL steps that match this role
    steps = WorkflowStep.objects.filter(role_name=role)
    
    if not steps.exists():
        messages.warning(request, 'No workflow steps configured for your role.')
        return redirect('dashboard')
    
    # Show requests at ANY of these steps assigned to this user OR unassigned
    pending_requests = SanctionRequest.objects.filter(
        Q(assigned_to=request.user) | Q(assigned_to__isnull=True),
        current_step__in=steps,
        status__in=['PENDING', 'IN_PROGRESS']
    ).order_by('created_at')
    
    return render(request, 'workflow/approval_queue.html', {
        'step': steps.first(),
        'pending_requests': pending_requests,
    })


@login_required
@role_required('CUSTOMER_ADMIN')
def customer_admin_allocation(request):
    """Dashboard for Customer Admin to allocate tasks."""
    requests = SanctionRequest.objects.exclude(status__in=['APPROVED', 'REJECTED'])
    
    # Get all potential assignees (officers)
    assignees = User.objects.filter(profile__role__in=['JPO', 'PO', 'AS', 'GMM', 'CGM', 'JS','DIRECTOR'])
    
    return render(request, 'workflow/task_allocation.html', {
        'requests': requests,
        'assignees': assignees,
    })


@login_required
@role_required('CUSTOMER_ADMIN')
def allocate_task(request, request_id):
    """View to handle task assignment."""
    if request.method == 'POST':
        sanction_request = get_object_or_404(SanctionRequest, id=request_id)
        user_id = request.POST.get('assignee_id')
        
        if user_id:
            assignee = get_object_or_404(User, id=user_id)
            sanction_request.assigned_to = assignee
            sanction_request.save()
            
            # Log the allocation
            ApprovalLog.objects.create(
                request=sanction_request,
                step=sanction_request.current_step,
                user=request.user,
                action='FORWARD', # Re-using FORWARD as a generic "moved to next step/person"
                comments=f"Task allocated to {assignee.get_full_name() or assignee.username} by Customer Admin."
            )
            
            messages.success(request, f'Task successfully allocated to {assignee.username}.')
        else:
            messages.error(request, 'No assignee selected.')
            
    return redirect('workflow:customer_admin_allocation')


@login_required
@approver_required
def request_detail(request, request_id):
    """View sanction request details."""
    sanction_request = get_object_or_404(SanctionRequest, id=request_id)
    logs = sanction_request.logs.all()
    
    # Get bill documents
    try:
        bill_documents = sanction_request.bill.documents.all()
    except:
        bill_documents = []
    
    # Pre-calculate rates for items where rate is missing/zero
    # Convert to list to ensure attributes persist to template and avoid re-evaluation
    items = list(sanction_request.bill.items.all())
    total_claimed_amount = 0
    
    # DEBUG LOGGING
    print(f"DEBUG: Processing Request {sanction_request.id}")
    print(f"DEBUG: Found {len(items)} items")

    for item in items:
        # Fix display rate
        if item.claimed_rate == 0 and item.claimed_amount > 0 and item.claimed_quantity > 0:
            item.display_rate = item.claimed_amount / item.claimed_quantity
            print(f"DEBUG: Item {item.id} Rate 0 -> Calc {item.display_rate}")
        else:
            item.display_rate = item.claimed_rate
            print(f"DEBUG: Item {item.id} Rate {item.claimed_rate} -> Display {item.display_rate}")
        
        # Sum total
        if item.claimed_amount:
            total_claimed_amount += item.claimed_amount
            
    print(f"DEBUG: Total Claimed calculated: {total_claimed_amount}")
    print(f"DEBUG: Stored Claimed: {sanction_request.claimed_amount}")

    # Auto-fix the SanctionRequest amount if it's out of sync (e.g. 0.00)
    if sanction_request.claimed_amount != total_claimed_amount:
        print(f"DEBUG: Fixing stored amount to {total_claimed_amount}")
        sanction_request.claimed_amount = total_claimed_amount
        sanction_request.save(update_fields=['claimed_amount'])
            
    # Logic to fetch the deemed/approved amount from the previous authenticator
    suggested_amount = total_claimed_amount
    
    # Get the latest approval log that has a valid approved amount
    latest_approval = ApprovalLog.objects.filter(
        request=sanction_request,
        approved_amount_at_stage__isnull=False
    ).order_by('-timestamp').first()
    
    if latest_approval:
        suggested_amount = latest_approval.approved_amount_at_stage
        print(f"DEBUG: Found previous approved amount: {suggested_amount}")
    
    steps = WorkflowStep.objects.all().order_by('order')
    
    return render(request, 'workflow/request_detail.html', {
        'sanction_request': sanction_request,
        'items': items, # Pass processed list of items
        'total_claimed_amount': total_claimed_amount,
        'suggested_amount': suggested_amount,
        'logs': logs,
        'bill_documents': bill_documents,
        'steps': steps,
    })


@login_required
@approver_required
def process_request(request, request_id):
    """Process (approve/reject/forward) a sanction request."""
    sanction_request = get_object_or_404(SanctionRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        amount = request.POST.get('approved_amount')
        
        # Update Bill Items (Remarks and Approved Amounts)
        for item in sanction_request.bill.items.all():
            save_item = False
            
            # Update comments/remarks
            remark_key = f'remarks_{item.id}'
            if remark_key in request.POST:
                item.comments = request.POST.get(remark_key)
                save_item = True
            
            # Update approved rate if present
            rate_key = f'approved_rate_{item.id}'
            if rate_key in request.POST and request.POST.get(rate_key):
                try:
                    item.approved_rate = float(request.POST.get(rate_key))
                    save_item = True
                except ValueError:
                    pass
            
            # Update approved amount if present
            amt_key = f'approved_amount_{item.id}'
            if amt_key in request.POST and request.POST.get(amt_key):
                try:
                    item.approved_amount = float(request.POST.get(amt_key))
                    save_item = True
                except ValueError:
                    pass
            
            # Update approved quantity if present
            qty_key = f'approved_quantity_{item.id}'
            if qty_key in request.POST and request.POST.get(qty_key):
                try:
                    item.approved_quantity = int(request.POST.get(qty_key))
                    save_item = True
                except ValueError:
                    pass

            if save_item:
                item.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            request=sanction_request,
            step=sanction_request.current_step,
            user=request.user,
            action=action,
            comments=comments,
            approved_amount_at_stage=amount if amount else None,
        )
        
        # Validate actions based on step permissions
        if action == 'APPROVE':
            if not sanction_request.current_step.can_approve_final:
                messages.error(request, 'You do not have permission for final approval.')
                return redirect('workflow:request_detail', request_id=request_id)
            sanction_request.status = 'APPROVED'
            sanction_request.sanctioned_amount = amount
            sanction_request.bill.status = 'APPROVED'
            sanction_request.bill.save()
            messages.success(request, 'Request approved successfully.')
        elif action == 'REJECT':
            if not sanction_request.current_step.can_reject:
                messages.error(request, 'You do not have permission to reject this request.')
                return redirect('workflow:request_detail', request_id=request_id)
            sanction_request.status = 'REJECTED'
            sanction_request.bill.status = 'REJECTED'
            sanction_request.bill.save()
            messages.warning(request, 'Request rejected.')
        elif action in ['FORWARD', 'REJECT_RECOMMENDED']:
            # Move to next step
            next_step = WorkflowStep.objects.filter(
                order__gt=sanction_request.current_step.order
            ).first()
            if next_step:
                sanction_request.current_step = next_step
                sanction_request.status = 'IN_PROGRESS'
                sanction_request.assigned_to = None
                if sanction_request.bill.status != 'UNDER_REVIEW':
                    sanction_request.bill.status = 'UNDER_REVIEW'
                    sanction_request.bill.save()
                
                msg = f'Request forwarded to {next_step.name}.'
                if action == 'REJECT_RECOMMENDED':
                    msg = f'Request forwarded to {next_step.name} with recommendation for rejection.'
                messages.success(request, msg)
            else:
                messages.error(request, 'No next step available.')
        elif action == 'CLARIFY':
            sanction_request.status = 'CLARIFICATION'
            sanction_request.bill.status = 'CLARIFICATION'
            sanction_request.bill.save()
            messages.info(request, 'Clarification requested.')
        
        sanction_request.save()
        return redirect('workflow:approval_queue')
    
    return redirect('workflow:request_detail', request_id=request_id)

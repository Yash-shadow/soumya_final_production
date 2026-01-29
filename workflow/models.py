from django.db import models
from django.contrib.auth.models import User


class WorkflowStep(models.Model):
    """Defines the 7 approval workflow steps."""
    
    name = models.CharField(max_length=100)
    order = models.IntegerField(unique=True)  # 1 to 7
    role_name = models.CharField(max_length=100)  # e.g., "JPO"
    can_reject = models.BooleanField(default=False)
    can_approve_final = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.order}. {self.name}"


class SanctionLimit(models.Model):
    """Sanction limits for different categories."""
    
    CATEGORY_CHOICES = (
        ('EMPLOYEE', 'Employee'),
        ('PENSIONER', 'Pensioner'),
        ('FAMILY_PENSIONER', 'Family Pensioner'),
        ('ARTISAN', 'Artisan'),
    )
    TYPE_CHOICES = (
        ('MINOR', 'Minor'),
        ('MAJOR', 'Major'),
        ('SELF_FUNDING', 'Self Funding'),
    )
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    limit_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ['category', 'limit_type']
    
    def __str__(self):
        return f"{self.category} - {self.limit_type}: ₹{self.amount}"


class SanctionRequest(models.Model):
    """Approval request for a bill."""
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CLARIFICATION', 'Clarification Needed'),
    )
    
    bill = models.OneToOneField(
        'hospitals.Bill',
        on_delete=models.CASCADE,
        related_name='sanction_request'
    )
    hospital_name = models.CharField(max_length=255)
    patient_name = models.CharField(max_length=255)
    claimed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    sanctioned_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.PROTECT,
        null=True,
        related_name='pending_requests'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sanction_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_limit_exceeded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SR-{self.id} - {self.hospital_name}"


class ApprovalLog(models.Model):
    """Audit trail for approval actions."""
    
    ACTION_CHOICES = (
        ('FORWARD', 'Forward'),
        ('REJECT', 'Reject'),
        ('REJECT_RECOMMENDED', 'Submitted for Rejection'),
        ('APPROVE', 'Approve (Final)'),
        ('CLARIFY', 'Seek Clarification'),
        ('RESPOND', 'Respond to Clarification'),
    )
    
    request = models.ForeignKey(
        SanctionRequest,
        related_name='logs',
        on_delete=models.CASCADE
    )
    step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField()
    approved_amount_at_stage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.user.username}"

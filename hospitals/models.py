from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Hospital(models.Model):
    TIER_CHOICES = (
        ('TIER1', 'Tier-I'),
        ('TIER2', 'Tier-II'),
        ('TIER3', 'Tier-III'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='hospital_profile',
        null=True,
        blank=True
    )

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, help_text="Hospital Code")
    serial_number = models.CharField(max_length=50, blank=True, null=True, help_text="Serial Number")
    
    # Legal & Tax Info
    pan_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="PAN Number")
    gst_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="GST Number")
    cin_number = models.CharField(max_length=30, blank=True, null=True, verbose_name="CIN Number")
    
    # Classification
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    category = models.CharField(max_length=100, blank=True, null=True, help_text="Hospital Category")
    
    # Contact & Address
    address = models.TextField(verbose_name="Hospital Address")
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True, verbose_name="Pin Code")
    
    phone = models.CharField(max_length=15, blank=True, verbose_name="Contact Number")
    email = models.EmailField(blank=True)
    valid_upto = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Service(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    base_rate_tier1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_rate_tier2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

class Scheme(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Bill(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CLARIFICATION', 'Clarification Needed'),
    )

    EMPLOYEE_TYPE_CHOICES = (
        ('EMPLOYEE', 'Employee'),
        ('PENSIONER', 'Pensioner'),
        ('FAMILY_PENSIONER', 'Family Pensioner'),
        ('ARTISAN', 'Artisan'),
    )

    RELATIONSHIP_CHOICES = (
        ('SELF', 'Self'),
        ('DEPENDENT', 'Dependent'),
    )

    SEX_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    claim_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        related_name='claims'
    )

    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.PROTECT,
        related_name='claims'
    )

    patient_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50)

    employee_type = models.CharField(
        max_length=30,
        choices=EMPLOYEE_TYPE_CHOICES
    )

    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES
    )

    credit_card_number = models.CharField(max_length=50)
    ip_number = models.CharField(max_length=50)

    mobile_number = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)

    disease_details = models.TextField()

    admission_date = models.DateField()
    discharge_date = models.DateField()
    
    gross_claimed_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    gross_approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    submitted_at = models.DateTimeField(null=True, blank=True)

    # Secondary Info
    bill_number = models.CharField(max_length=50, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    tgnpdcl_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    gst_number = models.CharField(max_length=50, blank=True)
    
    # Mandatory Documents
    id_card_file = models.FileField(upload_to='bills/id_cards/', blank=True, null=True)
    id_card_detail = models.CharField(max_length=100, blank=True, null=True, help_text="Manual entry for ID Card")
    cc_card_file = models.FileField(upload_to='bills/cc_cards/', blank=True, null=True)
    cc_card_detail = models.CharField(max_length=100, blank=True, null=True, help_text="Manual entry for CC Card")
    discharge_summary_file = models.FileField(upload_to='bills/discharge_summaries/', blank=True, null=True)
    discharge_summary_detail = models.CharField(max_length=255, blank=True, null=True, help_text="Manual entry for Discharge Summary")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_bills')

    def submit_claim(self):
        self.status = 'SUBMITTED'
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at'])

    def __str__(self):
        return f"Claim {self.claim_id} - {self.bill_number}"

class BillItem(models.Model):
    """Individual service claim in a bill."""
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT, null=True, blank=True)
    hospital_service_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    
    claimed_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    claimed_quantity = models.PositiveIntegerField(default=1)
    claimed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    approved_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    approved_quantity = models.PositiveIntegerField(null=True, blank=True)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    supporting_document = models.FileField(upload_to='bills/supporting_docs/', blank=True, null=True)
    comments = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.claimed_amount:
            self.claimed_amount = self.claimed_rate * self.claimed_quantity
        if self.approved_rate is not None and self.approved_quantity is not None:
            self.approved_amount = self.approved_rate * self.approved_quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.hospital_service_name or self.service.name} - {self.claimed_amount}"

class BillDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('ID_CARD', 'Employee / Pensioner / Artisan ID Card'),
        ('CC_CARD', 'Approved CC Card'),
        ('FINAL_BILL', 'Final Hospital Bill'),
        ('DETAIL_BILL', 'Detailed Hospital Bill'),
        ('PHARMACY', 'Pharmacy Bill'),
        ('INVOICE', 'Invoice'),
        ('DISCHARGE', 'Discharge Summary'),
        ('OTHER', 'Other'),
    )

    bill = models.ForeignKey(
        Bill,
        related_name='documents',
        on_delete=models.CASCADE
    )

    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='medical_bills/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.bill.claim_id}"

class WorkflowHistory(models.Model):
    ACTION_CHOICES = (
        ('FORWARDED', 'Forwarded'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    bill = models.ForeignKey(
        Bill,
        related_name='workflow_history',
        on_delete=models.CASCADE
    )

    action_by = models.ForeignKey(User, on_delete=models.PROTECT)
    role = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    remarks = models.TextField(blank=True)
    action_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bill.claim_id} - {self.action}"

class SanctionOrder(models.Model):
    bill = models.OneToOneField(
        Bill,
        on_delete=models.CASCADE,
        related_name='sanction_order'
    )

    order_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateField(auto_now_add=True)
    sanctioned_amount = models.DecimalField(max_digits=14, decimal_places=2)

    pdf_file = models.FileField(upload_to='sanction_orders/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sanction Order {self.order_number}"
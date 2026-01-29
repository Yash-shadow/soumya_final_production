from django.contrib import admin
from .models import (
    Hospital,
    Service,
    Scheme,
    Bill,
    BillItem,
    BillDocument,
    WorkflowHistory,
    SanctionOrder
)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'tier', 'district', 'is_active')
    list_filter = ('tier', 'district', 'is_active')
    search_fields = ('name', 'code', 'district')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1

class BillDocumentInline(admin.TabularInline):
    model = BillDocument
    extra = 0

class WorkflowHistoryInline(admin.TabularInline):
    model = WorkflowHistory
    extra = 0
    readonly_fields = ('action_by', 'role', 'action', 'remarks', 'action_at')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'claim_id',
        'hospital',
        'patient_name',
        'status',
        'created_at',
        'submitted_at',
    )

    list_filter = ('status', 'hospital', 'scheme')
    search_fields = ('patient_name', 'employee_id', 'claim_id')
    readonly_fields = ('claim_id', 'created_at', 'submitted_at')

    inlines = [BillItemInline, BillDocumentInline, WorkflowHistoryInline]

@admin.register(SanctionOrder)
class SanctionOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'bill', 'sanctioned_amount', 'order_date')
    search_fields = ('order_number',)

@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ('bill', 'role', 'action', 'action_by', 'action_at')
    list_filter = ('role', 'action')

@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    list_display = ('bill', 'service', 'claimed_amount')

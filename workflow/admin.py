from django.contrib import admin
from .models import WorkflowStep, SanctionLimit, SanctionRequest, ApprovalLog


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'role_name', 'can_reject', 'can_approve_final', 'is_active')
    list_filter = ('is_active', 'can_reject', 'can_approve_final')
    ordering = ['order']


@admin.register(SanctionLimit)
class SanctionLimitAdmin(admin.ModelAdmin):
    list_display = ('category', 'limit_type', 'amount')
    list_filter = ('category', 'limit_type')


class ApprovalLogInline(admin.TabularInline):
    model = ApprovalLog
    extra = 0
    readonly_fields = ('user', 'step', 'action', 'comments', 'approved_amount_at_stage', 'timestamp')


@admin.register(SanctionRequest)
class SanctionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'bill', 'hospital_name', 'claimed_amount', 'sanctioned_amount', 'status', 'current_step')
    list_filter = ('status', 'current_step', 'created_at')
    search_fields = ('hospital_name', 'patient_name')
    inlines = [ApprovalLogInline]
    raw_id_fields = ('bill',)

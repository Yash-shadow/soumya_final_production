
from django import forms
from .models import Bill, BillDocument, BillItem


class BillForm(forms.ModelForm):
    """
    Hospital – Create and Submit Medical Claim
    (As per Annexure-D of requirements)
    """
    gross_claimed_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = Bill
        fields = [
            'scheme',
            'patient_name',
            'designation',
            'employee_id',
            'employee_type',
            'relationship',
            'credit_card_number',
            'ip_number',
            'mobile_number',
            'age',
            'sex',
            'disease_details',
            'admission_date',
            'discharge_date',
            'bill_number',
            'bill_date',
            'gross_claimed_amount',
            'id_card_file',
            'id_card_detail',
            'cc_card_file',
            'cc_card_detail',
            'discharge_summary_file',
            'discharge_summary_detail'
        ]

        widgets = {
            'scheme': forms.Select(attrs={'class': 'form-control'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient Name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'employee_type': forms.Select(attrs={'class': 'form-control'}),
            'relationship': forms.Select(attrs={'class': 'form-control'}),
            'credit_card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CC Card Number'}),
            'ip_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP Number'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female')], attrs={'class': 'form-control'}),
            'disease_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'discharge_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bill_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invoice Number'}),
            'id_card_file': forms.FileInput(attrs={'class': 'form-control'}),
            'cc_card_file': forms.FileInput(attrs={'class': 'form-control'}),
            'discharge_summary_file': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_detail': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ID details'}),
            'cc_card_detail': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter CC Card details'}),
            'discharge_summary_detail': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Discharge Summary details'}),
        }
        labels = {
            'id_card_file': 'Attach ID',
            'cc_card_file': 'Attach Approval CC Card',
            'discharge_summary_file': 'Attach Discharge Summary',
            'id_card_detail': 'ID Details',
            'cc_card_detail': 'CC Card Details',
            'discharge_summary_detail': 'Discharge Summary Details',

        }


class BillDocumentForm(forms.ModelForm):
    """
    Annexure-C – Upload Mandatory / Optional Documents
    """

    class Meta:
        model = BillDocument
        fields = [
            'document_type',
            'file',
        ]

        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ['service', 'hospital_service_name', 'claimed_quantity', 'claimed_rate', 'claimed_amount', 'description', 'supporting_document']
    
    # Make amount optional so it can be auto-calculated
    claimed_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Amount'}))
    
    widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'hospital_service_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter service name'}),
            'claimed_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Qty'}),
            'claimed_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rate'}),
            'claimed_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Amount'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'placeholder': 'Optional details'}),
            'supporting_document': forms.FileInput(attrs={'class': 'form-control'}),
        }

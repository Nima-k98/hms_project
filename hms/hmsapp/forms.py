from django import forms
from .models import *

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'  # Includes all fields in the Department model
        widgets = {
            'dpt_name': forms.TextInput(attrs={'class': 'form_control', 'placeholder': "Department Name"}),
            'desc': forms.Textarea(attrs={'class': 'form_control', 'placeholder': "Description"}),
            'depart_pic': forms.ClearableFileInput(attrs={'class': 'form_control'}),
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['doctor_id']
        fields = [
            'doc_name', 'email', 'mobile_number',
            'specialization', 'qualification',
            'department', 'doc_pic'
        ]
        widgets = {
            'doc_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'doc_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['doc_pic'].required = False

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['patient_pic', 'patient_name', 'mobile_number', 'email', 'gender', 'address', 'dob']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter patient name'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'patient_pic': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient_pic'].required = False

class AvailabilityForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}))

    class Meta:
        model = DoctorAvailability
        fields = ['day', 'start_time', 'end_time', 'consultation_fee']

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['department', 'patient', 'date_of_appointment', 'time_of_appointment', 'doctor', 'reason']

class MedicalRecordForm(forms.ModelForm):

        class Meta:
            model = MedicalRecord
            fields = ['diagnosis', 'description','prescription', 'report_files']
        widgets = {
            'diagnosis': forms.TextInput(attrs={'placeholder': 'Enter diagnosis'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter description'}),
            'prescription': forms.Textarea(attrs={'placeholder': 'Enter prescription'}),
            }

import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Max



# Phone number validator
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# Create your models here.
class CustomUser(AbstractUser):
    USER_CHOICES = [
        ('1', 'admin'),
        ('2', 'doctor'),
        ('3', 'patient'),
    ]
    user_type = models.CharField(choices=USER_CHOICES, max_length=50, default=1)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class Department(models.Model):
    dpt_name = models.CharField(max_length=200)
    desc = models.TextField(blank=True)
    depart_pic = models.ImageField(upload_to='department/images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dpt_name

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    doc_pic = models.ImageField(upload_to='doctor/images/',null=True, blank=True)
    doc_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    mobile_number = models.CharField(max_length=15, validators=[phone_regex])
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    doctor_id = models.CharField(max_length=6, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = f"D{uuid.uuid4().int % 100000:05}"
        super().save(*args, **kwargs)

    def __str__(self):
            return self.user.username if self.user else "Doctor without user"

class Patient(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient_pic = models.ImageField(upload_to='user/images/', null=True, blank=True)
    patient_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=15, validators=[phone_regex])
    email = models.EmailField(max_length=200)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES)
    address = models.TextField()
    dob = models.DateField(null=True, blank=True)
    patient_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = f"P{uuid.uuid4().int % 1000000000:09}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username if self.user else "Patient without user"

class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=300.00)

    def __str__(self):
        return f"{self.doctor.doc_name}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    appointment_number = models.IntegerField(default=0,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, default=0)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, default=0)
    date_of_appointment = models.DateField()
    time_of_appointment = models.TimeField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    reason = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=200, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically generate an appointment number
        if not self.appointment_number:
            # Get the highest current appointment number and increment it
            max_appointment_number = Appointment.objects.aggregate(Max('appointment_number'))[
                                         'appointment_number__max'] or 0
            self.appointment_number = max_appointment_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Appointment {self.appointment_number} - {self.get_status_display()}"


class Bill(models.Model):
    PAYMENT_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
    ]

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='bill')
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bill for Appointment {self.appointment.id} - {'Paid' if self.is_paid else 'Unpaid'}"

class MedicalRecord(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='medicalRecord')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    report_files = models.FileField(upload_to='medical_records/images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record for {self.patient.patient_name}"
from datetime import datetime, date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.templatetags.static import static
from django.utils.html import strip_tags
from xhtml2pdf import pisa
from hmsapp.decorators import admin_required
from hmsapp.forms import DepartmentForm, DoctorForm, PatientForm, AppointmentForm, MedicalRecordForm, AvailabilityForm
from hmsapp.models import CustomUser, Patient, Doctor, Department, DoctorAvailability, Appointment, Bill, MedicalRecord
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string


def home(request):
    departments = Department.objects.all()
    doctors = Doctor.objects.all()
    department_count = Department.objects.count()
    doctor_count = Doctor.objects.count()
    patient_count = Patient.objects.count()
    patient_details = None
    if request.user.is_authenticated and request.user.user_type == "3":
        try:
            patient_details = Patient.objects.get(user=request.user)

        except Patient.DoesNotExist:
            patient_details = {}

    return render(request, 'home.html', {
        'patient_details': patient_details,
        'departments': departments,
        'doctors': doctors,
        'department_count': department_count,
        'doctor_count': doctor_count,
        'patient_count': patient_count})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            print(user.user_type)
            if user.user_type == "1":  # Admin
                messages.success(request, "You have successfully logged in.Welcome Admin!")
                return redirect('admin_home')  # Replace with your admin dashboard URL
            elif user.user_type == "2":  # Doctor
                messages.success(request, "You have successfully logged in.")
                return redirect('doctor_home')  # Replace with your doctor dashboard URL
            elif user.user_type == "3":  # Patient
                messages.success(request, "You have successfully logged in.")
                return redirect('home')  # Replace with your patient dashboard URL
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'login.html', {'form_type': 'login'})  # Render login forms


# View to handle signup forms submission
def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        gender = request.POST.get('gender')
        profile_pic = request.FILES.get('profile_pic')
        address = request.POST.get('address')
        dob = request.POST.get('dob')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        # Validate passwords
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('signup')

        # Create new user
        user = CustomUser.objects.create_user(username=name, email=email, password=password, user_type=3)
        Patient.objects.create(user=user, address=address, mobile_number=mobile, gender=gender,
                               patient_pic=profile_pic, dob=dob, patient_name=name, email=email)
        user.save()

        # Log the user in after signup
        login(request, user)
        messages.success(request, "Signup successful. You are now logged in!")
        return redirect('login')  # Redirect to the home page after signup

    return render(request, 'login.html', {'form_type': 'signup'})


def user_logout(request):
    auth_logout(request)  # Use Django's logout function
    messages.success(request, "You have been logged out.")
    print(request.user.is_authenticated)
    print("Message set for logout.")  # Debugging line
    return redirect('login')


# patient section
def appointment(request):
    patient_details = None

    if request.user.is_authenticated and request.user.user_type == "3":
        try:
            patient_details = Patient.objects.get(user=request.user)

        except Patient.DoesNotExist:
            patient_details = {}

    departments = Department.objects.all()
    doctors = Doctor.objects.all()

    context = {
        'departments': departments,
        'doctors': doctors,
        'patient_details': patient_details,
    }

    return render(request, 'make_appointment.html', context)

def get_doctors_by_department(request):
    department_id = request.GET.get('department_id')
    if department_id:
        doctors = Doctor.objects.filter(department_id=department_id)
    else:
        doctors = Doctor.objects.all()

    doctor_list = [{'id': doctor.id, 'name': f'Dr. {doctor.doc_name}'} for doctor in doctors]
    return JsonResponse({'doctors': doctor_list})

def get_doctor_details(request):
    doctor_id = request.GET.get('doctor_id')
    if doctor_id:
        doctor = Doctor.objects.get(id=doctor_id)
        availability = DoctorAvailability.objects.filter(doctor=doctor)
        availability_data = [
            {
                'day': av.day,
                'start_time': av.start_time.strftime('%H:%M'),
                'end_time': av.end_time.strftime('%H:%M'),
            }
            for av in availability
        ]
        doctor_data = {
            'doctor': {
                'name': doctor.doc_name,
                'specialization': doctor.specialization,
                'qualification': doctor.qualification,
            },
            'availability': availability_data
        }
        return JsonResponse(doctor_data)
    return JsonResponse({'error': 'Invalid doctor ID'}, status=400)

def make_appointment(request):
    if request.method == "POST":
        patient = None
        if request.user.is_authenticated and request.user.user_type == "3":  # Assuming '3' is for patients
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                messages.error(request, "Patient profile not found.")
                return redirect('appointment')  # Redirect to the form page

        if not patient:
            messages.error(request, "You need to log in as a patient to book an appointment.")
            return redirect('login')

        department_id = request.POST.get('department')
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('message')

        try:
            department = get_object_or_404(Department, id=department_id)
            doctor = get_object_or_404(Doctor, id=doctor_id)
            try:
                appointment_time_24hr = datetime.strptime(appointment_time, "%I:%M %p").time()
            except ValueError:
                messages.error(request, "Invalid time format. Please use the format HH:MM AM/PM.")
                return redirect('appointment')
            # Create an appointment
            appointment = Appointment.objects.create(
                department=department,
                patient=patient,
                date_of_appointment=appointment_date,
                time_of_appointment=appointment_time_24hr,
                doctor=doctor,
                reason=reason,
                status='pending'

            )
            messages.success(request, f"Appointment successfully booked!.")
            return redirect('appointment_success', appointment_id=appointment.id)  # Redirect to a success page
        except Exception as e:
            messages.error(request, f"Please check your details and try again.")
            print(f"Error: {e}")
            return redirect('appointment')  # Redirect to the form page

    return redirect('appointment')

def appointment_success(request, appointment_id):
    return render(request, 'appointment_success.html', {'appointment_number': appointment_id})


# Admin Section
@admin_required
def admin_home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.user_type != "1":
        return redirect('login')

    departments = Department.objects.all()
    doctors = Doctor.objects.all()
    patients = Patient.objects.all()
    appointments = Appointment.objects.all()
    for patient in patients:
        if patient.dob:
            today = date.today()
            patient.age = (
                    today.year - patient.dob.year -
                    ((today.month, today.day) < (patient.dob.month, patient.dob.day))
            )
        else:
            patient.age = None
    context = {
        'department_count': departments.count(),
        'doctor_count': Doctor.objects.count(),
        'patient_count': Patient.objects.count(),
        'departments': departments,
        'doctors': doctors,
        'patients': patients,
        'appointments': appointments,
    }
    admin_details = {
        'name': request.user.username,
        'email': request.user.email,
    }
    context['admin_details'] = admin_details
    return render(request, 'admin/admin_home.html',context)

def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added successfully.")
            return redirect('admin_home')
    else:
        form = DepartmentForm()
    return render(request, 'admin/add_department.html', {'form': form})
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "department update successfully.")
            return redirect('admin_home')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'admin/edit_department.html', {'forms': form})

def delete_department(request, id):
    department = get_object_or_404(Department, id=id)
    department.delete()
    messages.success(request, "Department delete successfully.")
    return redirect('admin_home')

def add_doctor(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            email = form.cleaned_data['email']
            doc_name = form.cleaned_data['doc_name']
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "This email is already associated with another account.")
                return redirect('add_doctor', form=form)

            temp_password = f"{doc_name[:3]}@{CustomUser.objects.make_random_password()[:4]}"
            # Create user
            user = CustomUser.objects.create_user(
                username=doc_name,
                email=email,
                password=temp_password,
                user_type=2
            )
            doctor.user = user
            doctor.save()
            subject = 'Your Password for login from Lifeline Hospital'
            message = f'Hello Dr. {doc_name},\n\n' \
                      f'Your account has been successfully created. ' \
                      f'Your temporary password is: {temp_password}.\n' \
                      'Please change your password after logging in.\n\n' \
                      'Thank you.'

            send_mail(
                subject,
                strip_tags(message),
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "Doctor added successfully.")
            print(temp_password);
            return redirect('admin_home')
    else:
        form = DoctorForm()
    return render(request, 'admin/add_doctor.html', {'form': form,'departments':departments})


def edit_doctor(request, doctor_id):
    departments = Department.objects.all()
    doctor = get_object_or_404(Doctor, id=doctor_id)
    user = doctor.user

    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            # Validate email and username for conflicts
            email = form.cleaned_data['email']
            doc_name = form.cleaned_data['doc_name']

            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "This email is already associated with another account.")
                return redirect('edit_doctor', doctor_id=doctor.id)

            # if CustomUser.objects.filter(username=doc_name).exclude(id=user.id).exists():
            #     messages.error(request, "This name is already associated with another account.")
            #     return redirect('edit_doctor', doctor_id=doctor.id)

            # Update user fields
            user.email = email
            user.username = doc_name
            user.save()
            form.save()
            messages.success(request, "Doctor updated successfully.")
            return redirect('admin_home')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'admin/edit_doctor.html', {'form': form, 'departments' : departments })

def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    user = doctor.user
    user.delete()
    messages.success(request, "Doctor deleted successfully.")
    return redirect('admin_home')

def doctor_availability(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    availabilities = DoctorAvailability.objects.filter(doctor=doctor)
    form = AvailabilityForm()
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = doctor
            availability.save()
            return redirect('doctor_availability', doctor_id=doctor_id)
    return render(request, 'admin/availability_list.html', {'doctor': doctor, 'availabilities': availabilities, 'form': form})

def add_availability(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = doctor
            availability.save()
            return redirect('doctor_availability', doctor_id=doctor_id)
    else:
        form = AvailabilityForm()
    return render(request, 'admin/availability_form.html', {'form': form, 'doctor': doctor})

def edit_availability(request, availability_id):
    availability = get_object_or_404(DoctorAvailability, id=availability_id)
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('doctor_availability', doctor_id=availability.doctor.id)
    else:
        form = AvailabilityForm(instance=availability)
    return render(request, 'admin/availability_form.html', {'form': form, 'doctor': availability.doctor})

def delete_availability(request, availability_id):
    availability = get_object_or_404(DoctorAvailability, id=availability_id)
    doctor_id = availability.doctor.id
    availability.delete()
    return redirect('doctor_availability', doctor_id=doctor_id)

def add_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            mobile_number = form.cleaned_data['mobile_number']
            email = form.cleaned_data['email']
            patient_name = form.cleaned_data['patient_name']

            # if Patient.objects.filter(mobile_number=mobile_number).exists():
            #     messages.error(request, "Patient with this mobile number already exists.")
            #     return render(request, 'admin/add_patient.html', {'form': form})

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "This email is already associated with another account.")
                return render(request, 'admin/add_patient.html', {'form': form})

            patient = form.save(commit=False)
            temp_password = f"{patient_name[:3]}@{CustomUser.objects.make_random_password()[:4]}"
            # Create user
            user = CustomUser.objects.create_user(
                username=patient_name,
                email=email,
                password=temp_password,  # Reset or share with the patient
                user_type=3
            )
            patient.user = user
            patient.save()
            subject = 'Your Password for login from Lifeline Hospital'
            message = f'Hello {patient_name},\n\n' \
                      f'Your account has been successfully created. ' \
                      f'Your temporary password is: {temp_password}.\n' \
                      'Please change your password after logging in.\n\n' \
                      'Thank you.'

            send_mail(
                subject,
                strip_tags(message),
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "Patient added successfully.")
            print(temp_password)
            return redirect('admin_home')
    else:
        form = PatientForm()
    return render(request, 'admin/add_patient.html', {'form': form})

def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    user = patient.user

    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            # Validate email and username for conflicts
            email = form.cleaned_data['email']
            patient_name = form.cleaned_data['patient_name']

            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "This email is already associated with another account.")
                return redirect('edit_patient', patient_id=patient.id)

            # if CustomUser.objects.filter(username=patient_name).exclude(id=user.id).exists():
            #     messages.error(request, "This name is already associated with another account.")
            #     return redirect('edit_patient', patient_id=patient.id)

            # Update user fields
            user.email = email
            user.username = patient_name
            user.save()

            # Update patient fields
            form.save()
            messages.success(request, "Patient updated successfully.")
            return redirect('admin_home')  # Redirect to the patient list or admin home
    else:
        form = PatientForm(instance=patient)

    return render(request, 'admin/edit_patient.html', {'form': form})

def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    user = patient.user
    user.delete()
    messages.success(request, "Patient deleted successfully.")
    return redirect('admin_home')

def add_appointment(request):
    departments = Department.objects.all()
    patients = Patient.objects.all()
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment added successfully.")
            return redirect('admin_home')  # Adjust the redirect as needed
    else:
        form = AppointmentForm()

    return render(request, 'admin/add_appointment.html', {
        'form': form,
        'departments': departments,
        'patients': patients,
        'doctors': doctors,
    })

def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    messages.success(request, "Appointment delete successfully.")
    return redirect('admin_home')

def generate_invoice(request, appointment_id):
    # Fetch appointment details
    appointment = get_object_or_404(Appointment, id=appointment_id)
    consultation_fee = appointment.doctor.doctoravailability_set.first().consultation_fee if appointment.doctor.doctoravailability_set.exists() else 0
    # Ensure status is 'Pending'
    if appointment.status != 'pending':
        return JsonResponse({'error': 'Invoice can only be generated for pending appointments.'}, status=400)

    # Render invoice page
    return render(request, 'admin/invoice.html', {'appointment': appointment ,'consultation_fee': consultation_fee})

def process_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":

        Bill.objects.create(
            appointment=appointment,
            consultation_fee=appointment.doctor.doctoravailability_set.first().consultation_fee,  # Example: get fee
            payment_method=request.POST.get('payment_method'),
            is_paid=True,
        )
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, "Payment Confirmed! The invoice will download shortly.")

    return render(request, 'admin/process_payment.html', {'appointment': appointment})

def download_invoice(request, appointment_id):
    # Fetch appointment and associated bill
    appointment = get_object_or_404(Appointment, id=appointment_id)
    bill = appointment.bill

    # Render the invoice template to HTML
    html_string = render_to_string('admin/download_invoice.html', {'appointment': appointment, 'bill': bill})

    # Create a HttpResponse object to return as a PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{appointment.patient.patient_name}.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    # If there is an error while creating the PDF, send a response with an error message
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=400)

    return response


# Doctor Section
def doctor_signup(request):
    departments = Department.objects.all()

    if request.method == 'POST':
        department_id = request.POST.get('department')
        # Get the corresponding Department instance
        department = Department.objects.get(id=department_id)

        name = request.POST.get('name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        specialization = request.POST.get('specialization')
        qualification = request.POST.get('qualification')
        department = department
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        profile_pic = request.FILES.get('profile_pic')

        # Validate passwords
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('doctor_signup')

        # Check if the user already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('doctor_signup')

        # Create the user
        user = CustomUser.objects.create_user(
            username=name,
            email=email,
            password=password,
            user_type=2
        )
        user.save()

        # Create the Doctor profile
        Doctor.objects.create(
            user=user,
            doc_pic=profile_pic,
            doc_name=name,
            email=email,
            mobile_number=mobile,
            specialization=specialization,
            qualification=qualification,
            department=department
        )

        # Log the user in
        login(request, user)
        messages.success(request, "Signup successful. Welcome, Doctor!")
        print(departments)
        return redirect('login')
    return render(request, 'login.html', {'form_type': 'doctor-signup', 'departments': departments})


def doctor_home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.user_type != "2":  # Ensure the user is a doctor
        return redirect('login')

    doctor = Doctor.objects.get(user=request.user)  # Fetch doctor object related to the current user

    appointments_today = Appointment.objects.filter(
        doctor=doctor,
        date_of_appointment=date.today(),
        status='confirmed'
    )
    all_appointments = Appointment.objects.filter(doctor=doctor)

    patient_total = all_appointments.values('patient').distinct()

    patients = Patient.objects.filter(id__in=[patient['patient'] for patient in patient_total])

    patients_count = patient_total.count()

    for patient in patients:
        today = date.today()
        birth_date = patient.dob
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        patient.age = age
        # patient.confirmed_appointment = Appointment.objects.filter(
        #     patient=patient, doctor=doctor, status='confirmed'
        # ).first()
    # Prepare context data
    context = {
        'doctor_details': doctor,
        'appointments_today': appointments_today,
        'appointments': all_appointments,
        'patients': patients,
        'patients_count': patients_count,
    }

    return render(request, 'doctor/doctor_home.html', context)


def complete_appointment(request, appointment_id):
    if not request.user.is_authenticated:
        return redirect('login')

    appointment = get_object_or_404(Appointment, id=appointment_id)


    if appointment.doctor.user != request.user:
        messages.error(request, "You are not authorized to complete this appointment.")
        return redirect('doctor_home')

    # Update the status to 'completed'
    appointment.status = 'completed'
    appointment.save()

    messages.success(request, f"Appointment marked as completed.")
    return redirect('doctor_home')

def add_medical_record(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Check if the user is authenticated and authorized (admin or doctor)
    if not request.user.is_authenticated or request.user.user_type not in ["1", "2"]:
        return redirect('login')

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)

        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = patient

            # If the user is a doctor, assign the doctor
            if request.user.user_type == "2":  # Doctor
                try:
                    doctor = Doctor.objects.get(user=request.user)
                    medical_record.doctor = doctor
                except Doctor.DoesNotExist:
                    messages.error(request, "Doctor not found!")
                    return redirect('doctor_home')

            if request.user.user_type == "1":
                medical_record.doctor = None

            medical_record.save()

            messages.success(request, "Medical record added successfully.")

            # Redirect to a page that shows the medical record details
            return redirect('view_medical_record', medical_record_id=medical_record.id)

    else:
        form = MedicalRecordForm()

    return render(request, 'doctor/add_medical_records.html', {'form': form, 'patient': patient})


def generate_prescription_pdf(request, medical_record_id):
    medical_record = get_object_or_404(MedicalRecord, id=medical_record_id)
    patient = medical_record.patient
    doctor = medical_record.doctor
    today = date.today()
    birth_date = patient.dob
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    patient.age = age

    logo_url = request.build_absolute_uri(static('img/logo.png'))
    html_content = render_to_string('doctor/prescription_pdf.html', {
        'medical_record': medical_record,
        'patient': patient,
        'doctor': doctor,
        'hospital_name': 'Lifeline Hospital',
        'hospital_address': 'Kuttisahib Road Cheranelloor,South Chittoor Kochi, Kerala, 682027',
        'logo_url': logo_url,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{patient.patient_name}.pdf"'
    pisa_status = pisa.CreatePDF(html_content, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response


def view_medical_record(request, medical_record_id):
    medical_record = get_object_or_404(MedicalRecord, id=medical_record_id)
    patient = medical_record.patient
    doctor = medical_record.doctor

    return render(request, 'doctor/view_medical_record.html', {
        'medical_record': medical_record,
        'patient': patient,
        'doctor': doctor,
    })

def patient_details(request, patient_id):
    if not request.user.is_authenticated:
        return redirect('login')

    patient = get_object_or_404(Patient, id=patient_id)
    medical_records = MedicalRecord.objects.filter(patient=patient)
    appointments = Appointment.objects.filter(patient=patient)

    today = date.today()
    birth_date = patient.dob
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    patient.age = age

    context = {
        'patient': patient,
        'medical_records': medical_records,
        'appointments': appointments,
    }

    return render(request, 'doctor/patient_details.html', context)
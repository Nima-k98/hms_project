from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.login_view, name="login"),  # Login view
    path('signup/', views.signup_view, name="signup"),  # Signup view
    path('logout/', views.user_logout, name='logout'),  # logout view

    # Patient
    path('appointment/', views.appointment, name='appointment'),
    path('get-doctors/', views.get_doctors_by_department, name='get_doctors'),
    path('get-doctor-details/', views.get_doctor_details, name='get_doctor_details'),
    path('make-appointment/', views.make_appointment, name='make_appointment'),
    path('appointment/success/<int:appointment_id>/', views.appointment_success, name='appointment_success'),

    #  Admin
    path('admin-home/', views.admin_home, name='admin_home'),
    path('department/add/', views.add_department, name='add_department'),
    path('department/edit/<int:id>/', views.edit_department, name='edit_department'),
    path('department/delete/<int:id>/', views.delete_department, name='delete_department'),
    path('doctor/add/', views.add_doctor, name='add_doctor'),
    path('doctors/edit/<int:doctor_id>/', views.edit_doctor, name='edit_doctor'),
    path('doctors/delete/<int:doctor_id>/', views.delete_doctor, name='delete_doctor'),
    path('doctor/<int:doctor_id>/availability/', views.doctor_availability, name='doctor_availability'),
    path('availability/add/<int:doctor_id>/', views.add_availability, name='add_availability'),
    path('availability/edit/<int:availability_id>/', views.edit_availability, name='edit_availability'),
    path('availability/delete/<int:availability_id>/', views.delete_availability, name='delete_availability'),
    path('patients/add/', views.add_patient, name='add_patient'),
    path('patients/edit/<int:patient_id>/', views.edit_patient, name='edit_patient'),
    path('patients/delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),
    path('appointment/add/', views.add_appointment, name='add_appointment'),
    path('appointment/delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('generate-invoice/<int:appointment_id>/', views.generate_invoice, name='generate_invoice'),
    path('process_payment/<int:appointment_id>/', views.process_payment, name='process_payment'),
    path('download_invoice/<int:appointment_id>/', views.download_invoice, name='download_invoice'),


    #  Doctor
    path('doctor/signup/', views.doctor_signup, name='doctor_signup'),
    path('doctor-home/', views.doctor_home, name='doctor_home'),
    path('complete_appointment/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    path('add_medical_record/<int:patient_id>/', views.add_medical_record, name='add_medical_record'),
    path('patient/<int:patient_id>/', views.patient_details, name='patient_details'),
    path('view_medical_record/<int:medical_record_id>/', views.view_medical_record, name='view_medical_record'),
    path('generate-prescription/<int:medical_record_id>/', views.generate_prescription_pdf,
         name='generate_prescription_pdf'),
    ]

from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import suggest_companies
from .views import select_student, suggest_companies
from .views import download_cluster_excel
from .views import download_suggested_students_excel
from .views import predict_recruitment


# Initialize urlpatterns list first
urlpatterns = [


    # Home Page
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('add-student-from-preview/', views.add_student_from_preview, name='add_student_from_preview'),
    path('', views.index, name="index"),

    path('predict_recruitment/', predict_recruitment, name='predict_recruitment'),
        
    path('download-cluster-excel/', download_cluster_excel, name='download_cluster_excel'),
    path('download-suggested-students-excel/', download_suggested_students_excel, name='download_suggested_students_excel'),

    path('top-skills/', views.top_skills, name='top_skills'),

    path('get_company/', views.get_company, name='get_company'),

    # Authentication
    path('register/', views.register_page, name="register_page"),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),

    # Student Management
    path('students/', views.students_list, name='students_list'),  # View all students
    path('add_student/', views.add_student, name='add_student'),  # Admin-only student addition
    path('students/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('delete_student/<int:id>/', views.delete_student, name='delete_student'),

    # Student Registration (for events)
    path('TPO_app/', views.register_student, name="register_student"),
    path('register_student_submit/', views.register_student_submit, name="register_student_submit"),

    # Job Registration
    path('register_job/', views.register_job, name="register_job"),
    path('register_job_submit/', views.register_job_submit, name="register_job_submit"),


    # Events
    path('upcoming_events/', views.upcoming_events, name="upcoming_events"),
    path('upcoming_events_submit/', views.upcoming_events_submit, name="upcoming_events_submit"),

    # Placement Statistics
    path('Statistics/', views.Statistics, name="Statistics"),

    path('cluster_students/', views.cluster_students_view, name='cluster_students'),
    path('suggest_students_to_company/', views.suggest_students_to_company, name='suggest_students_to_company'),
    #path('suggest_companies/<int:student_id>/', views.suggest_companies_view, name='suggest_companies'),

    # Admin: Add Company Details
    path('add_company_ml/', views.add_company_ml, name='add_company_ml'),
    path('add_company/', views.add_company_ml, name='add_company'),
    path('companies/', views.company_list, name='company_list'),


    path('companies/<int:company_id>/edit/', views.edit_company, name="edit_company"),  # Edit company
    path('companies/<int:company_id>/delete/', views.delete_company, name='delete_company'),

    # Machine Learning - Clustering & Recommendation (Admin Only)
    path('suggest_companies/', views.suggest_companies, name='suggest_companies'),
    path("select_student/", select_student, name="select_student"),

    # Success Page
    path('student_success/', views.student_success, name='student_success'),

    # Django Admin Panel - This is the only declaration for the 'admin' namespace
    path('admin/', admin.site.urls, name='admin'), 
    ]

# Add static handling for media files (only in development mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

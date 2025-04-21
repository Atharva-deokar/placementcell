from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import RegisterForm, StudentForm, CompanyForm
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import StudentInfo, JobInfo, EventInfo, CompanyInfo, Student, Company
from .ml_model import vectorize_skills_and_cluster, recommend_companies
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.utils.html import format_html
from .models import Company_ML
from .forms import CompanyMLForm
from django.db.models import Count
from collections import Counter
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Student
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sklearn.linear_model import LinearRegression
from .utils import extract_pdf_details 
from collections import Counter
import re

from .models import Company  
import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Student  # Assuming you have a Student model

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage  # Add this import
from .forms import StudentForm
from .utils import extract_pdf_details

@login_required
def upload_resume(request):
    # Your existing logic to handle file upload and extract details
    if request.method == 'POST':
        if 'preview_details' in request.POST:
            # Logic for previewing extracted data
            extracted_data = extract_pdf_details(request.FILES['resume'])
            return render(request, 'TPO_app/upload_resume.html', {'extracted_data': extracted_data})
        
        if 'add_student' in request.POST:
            # Logic to save student data
            student = Student(
                name=request.POST['name'],
                email=request.POST['email'],
                phone_number=request.POST['phone_number'],
                skills=request.POST['skills'],
                experience=request.POST['experience'],
                cgpa=request.POST['cgpa'],
                course_subdomain=request.POST['course_subdomain']
            )
            student.save()
            return redirect('students_list')  # Redirecting to the students list page

    return render(request, 'TPO_app/upload_resume.html')


def add_student_from_preview(request):
    """ Allow only admin to add a new student. """
    
    if request.method == 'POST':
        # Get extracted details from the session
        details = request.session.get('student_details')
        if not details:
            # If no details in session, redirect to upload resume page
            return redirect('upload_resume')

        # Initialize the form with POST data
        form = StudentForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully!")
            return redirect('students_list')
    else:
        form = StudentForm()
    return render(request, 'TPO_app/add_student.html', {'form': form})


def save_uploaded_file(pdf_file):
    """
    Saves the uploaded PDF file and returns its path.
    """
    fs = FileSystemStorage()
    filename = fs.save(pdf_file.name, pdf_file)
    file_path = fs.url(filename)  # This gives the relative URL of the uploaded file
    return file_path


def predict_recruitment(request):
    """  
    📊 Perform Time-Series Forecasting on Recruitment Trends  
    Utilizes Linear Regression to predict future job openings based on historical hiring data.  
    """
    
    companies = Company_ML.objects.all()  # Fetch company dataset
    
    recruitment_forecast = {}  # Store predictions
    
    for company in companies:
        # Extract historical hiring patterns
        historical_data = [
            company.prev_yr_5, 
            company.prev_yr_4, 
            company.prev_yr_3, 
            company.prev_yr_2, 
            company.prev_yr_1
        ]
        
        # Ensure we have sufficient data for modeling
        if any(historical_data):  
            X = np.array([[1], [2], [3], [4], [5]])  # Temporal dimension (Years)
            y = np.array(historical_data)  # Hiring volume
            
            # Initialize and fit the regression model
            predictive_model = LinearRegression()
            predictive_model.fit(X, y)
            
            # Forecast hiring needs for the upcoming year (6th year)
            projected_openings = int(predictive_model.predict([[6]])[0])
            
            # Store non-negative predictions
            recruitment_forecast[company.name] = max(projected_openings, 0)
    
    return render(request, 'TPO_app/predict_recruitment.html', {'recruitment_forecast': recruitment_forecast})


def top_skills(request):
    # Fetch required_skills from all companies
    all_skills = Company_ML.objects.values_list('required_skills', flat=True)

    # Split and clean skills (assuming comma-separated values)
    skill_list = []
    for skills in all_skills:
        if skills:
            skill_list.extend(skills.split(','))  # Split into individual skills

    # Count occurrences of each skill
    skill_counts = Counter(skill.strip().lower() for skill in skill_list if skill.strip())  
    top_skills = skill_counts.most_common(3)  # Get top 3 most common skills

    return render(request, 'TPO_app/top_skills.html', {'top_skills': top_skills})

@login_required
@user_passes_test(lambda u: u.is_staff)
def download_suggested_students_excel(request):
    """ Export suggested students for companies into an Excel file """

    # Fetch all companies and students
    companies = Company_ML.objects.all()
    students = Student.objects.all()

    # Create a dictionary mapping companies to students based on skill match
    company_suggestions = {}
    for company in companies:
        matched_students = [
            student for student in students if set(company.required_skills.split(",")).intersection(set(student.skills.split(",")))
        ]
        company_suggestions[company] = matched_students

    # Prepare data for Excel
    data = []
    for company, students in company_suggestions.items():
        for student in students:
            data.append({
                "Company Name": company.name,
                "Required Skills": company.required_skills,
                "Open Positions": company.num_posts,
                "Student Name": student.name,
                "Student Email": student.email,
                "Student Skills": student.skills,
                "CGPA": student.cgpa,
                "Course Subdomain": student.course_subdomain,
                "Experience": student.experience,
                "Phone Number": student.phone_number,
            })

    if not data:
        return HttpResponse("No data available", content_type="text/plain")

    # Convert list to DataFrame
    df = pd.DataFrame(data)

    # Create Excel response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="suggested_students.xlsx"'

    # Save DataFrame to Excel
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Suggested Students')

    return response


@login_required
@user_passes_test(lambda u: u.is_staff)
def download_cluster_excel(request):
    """ Export student clusters to an Excel file based on computed cluster labels. """

    # Fetch all students
    students = list(Student.objects.all())

    if not students:
        return HttpResponse("No data available", content_type="text/plain")

    # Apply clustering algorithm
    labels, kmeans, vectorizer = vectorize_skills_and_cluster(students)

    # Create list of student data with assigned cluster labels
    student_data = []
    for student, cluster in zip(students, labels):
        student_data.append({
            "Name": student.name,
            "Email": student.email,
            "Skills": student.skills,
            "CGPA": student.cgpa,
            "Course Subdomain": student.course_subdomain,
            "Experience": student.experience,
            "Phone Number": student.phone_number,
            "Cluster": cluster  # ✅ Take cluster from algorithm, NOT the database
        })

    # Convert list to DataFrame
    df = pd.DataFrame(student_data)

    # Create Excel response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="student_clusters.xlsx"'

    # Save DataFrame to Excel
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clusters')

    return response


def get_company(request):
    shortlisted_companies = []

    if request.method == "POST":
        student_skills = request.POST.get("student_skills", "").lower().split(",")  
        student_skills = [skill.strip() for skill in student_skills]  # Clean spaces

        companies = Company_ML.objects.all()
        company_matches = []  # Store (company, match_count)

        for company in companies:
            required_skills = company.required_skills.lower().split(",")
            required_skills = [skill.strip() for skill in required_skills]  # Clean spaces
            
            # Count how many skills match
            match_count = sum(skill in required_skills for skill in student_skills)

            if match_count > 0:
                company_matches.append((company, match_count))

        # Sort companies by match_count in descending order & take top 3
        company_matches.sort(key=lambda x: x[1], reverse=True)
        shortlisted_companies = [company[0] for company in company_matches[:3]]

    return render(request, 'TPO_app/Get_Company.html', {'shortlisted_companies': shortlisted_companies})


def select_student(request):
    students = Student.objects.all()
    return render(request, "select_student.html", {"students": students})

def suggest_companies(request):
    """ Recommend companies based on student skills using ML. """
    students = Student.objects.all()
    selected_student = None
    suggested_companies = []

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        if student_id:
            selected_student = get_object_or_404(Student, id=student_id)
            
            # Logic for matching skills and recommending companies
            student_skills = set(selected_student.skills.lower().split(','))
            
            for company in Company_ML.objects.all():
                company_skills = set(company.required_skills.lower().split(','))
                common_skills = student_skills.intersection(company_skills)
                
                # Calculate match percentage
                match_percentage = (len(common_skills) / len(company_skills)) * 100 if company_skills else 0
                
                # Only consider companies with at least 50% match
                if match_percentage >= 50:
                    suggested_companies.append({
                        'company': company,
                        'match_percentage': match_percentage
                    })

            # Sort companies by match percentage and take the top 3
            suggested_companies = sorted(suggested_companies, key=lambda x: x['match_percentage'], reverse=True)[:3]

    return render(
        request,
        "TPO_app/suggest_companies.html",
        {
            "students": students,
            "selected_student": selected_student,
            "companies": suggested_companies,
        },
    )


def suggest_students_to_company(request):
    """ Suggests students to companies based on at least 75% required skill match """
    companies = Company_ML.objects.all()
    students = Student.objects.all()
    
    company_suggestions = {}
    for company in companies:
        company_skills = preprocess_skills(company.required_skills)  # Preprocess company skills
        
        matched_students = []
        for student in students:
            student_skills = preprocess_skills(student.skills)  # Preprocess student skills
            
            # Find the number of matching skills
            matching_skills = company_skills.intersection(student_skills)
            match_percentage = len(matching_skills) / len(company_skills) if company_skills else 0
            
            # Ensure at least 75% of required skills match
            if match_percentage >= 0.75:
                matched_students.append(student)

        company_suggestions[company] = matched_students

    return render(request, 'TPO_app/suggest_students_to_company.html', {'company_suggestions': company_suggestions})


# ================================
# Company Management Views
# ================================

@staff_member_required
def add_company_ml(request):
    """ Allows the admin to add or update a company and store previous years' recruitment data """
    if request.method == 'POST':
        form = CompanyMLForm(request.POST)
        if form.is_valid():
            company_ml, created = Company_ML.objects.update_or_create(
                name=form.cleaned_data['name'],
                defaults={
                    'required_skills': form.cleaned_data['required_skills'],
                    'num_posts': form.cleaned_data['num_posts'],
                    'prev_yr_1': form.cleaned_data.get('prev_yr_1', 0),
                    'prev_yr_2': form.cleaned_data.get('prev_yr_2', 0),
                    'prev_yr_3': form.cleaned_data.get('prev_yr_3', 0),
                    'prev_yr_4': form.cleaned_data.get('prev_yr_4', 0),
                    'prev_yr_5': form.cleaned_data.get('prev_yr_5', 0),
                }
            )

            messages.success(request, f"Company {'added' if created else 'updated'} successfully!")
            return redirect('company_list')

        else:
            messages.error(request, "Invalid form submission. Please check your input.")

    else:
        form = CompanyMLForm()

    return render(request, 'TPO_app/add_company_ml.html', {'form': form})


@login_required
def company_list(request):
    """ Display a list of all companies. """
    companies = Company_ML.objects.all()
    return render(request, 'TPO_app/company_list.html', {'companies': companies})


@staff_member_required
def edit_company(request, company_id):
    """Allow only staff members to edit company details."""
    company = get_object_or_404(Company_ML, id=company_id)

    if request.method == 'POST':
        form = CompanyMLForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company details updated successfully!")
            return redirect('company_list')  # Ensure 'company_list' exists in URLs
        else:
            messages.error(request, "Error updating company details. Please check the form.")
    else:
        form = CompanyMLForm(instance=company)

    return render(request, 'TPO_app/edit_company.html', {'form': form, 'company': company})


@staff_member_required
def delete_company(request, company_id):
    """ Allow only admin to delete a company. """
    company = get_object_or_404(Company_ML, id=company_id)
    company.delete()
    messages.success(request, "Company deleted successfully!")
    return redirect('company_list')

@staff_member_required
def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_company_ml')  # Redirect to add_company_ml
    else:
        form = CompanyForm()
    return render(request, 'TPO_app/add_company.html', {'form': form})


# Check if the user is an admin
def is_admin(user):
    return user.is_staff

def index(request):
    """ Render the home page. """
    return render(request, 'includes/index.html')

# ==============================
# Student Management Views
# ==============================

@login_required
def students_list(request):
    """ Display a list of all students. """
    students = Student.objects.all()
    return render(request, 'students_list.html', {'students': students})

@staff_member_required  # Restrict access to admins only
def add_student(request):
    """ Allow only admin to add a new student. """
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully!")
            return redirect('students_list')
    else:
        form = StudentForm()
    return render(request, 'TPO_app/add_student.html', {'form': form})

@staff_member_required  # Restrict access to admins only
def edit_student(request, id):
    """ Allow only admin to edit a student's details. """
    student = get_object_or_404(Student, id=id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student details updated successfully!")
            return redirect('students_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'TPO_app/edit_student.html', {'form': form, 'student': student})

@staff_member_required  # Restrict access to admins only
def delete_student(request, id):
    """ Allow only admin to delete a student. """
    student = get_object_or_404(Student, id=id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect('students_list')

# ==============================
# Student Registration Views
# ==============================

def register_page(request):
    """ Allow users to register an account. """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You are successfully registered.')
            return redirect("/")
    else:
        form = RegisterForm()
        
    return render(request, "registration/register.html", {"form": form})

def login_request(request):
    """ Handle user login. """
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect("/")
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})

@login_required
def logout_request(request):
    """ Logout the user and redirect to home page. """
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("/")

# ==============================
# Student Info Management
# ==============================

@login_required(login_url='/login/')
def register_student(request):
    """ Render the student registration page. """
    return render(request, 'TPO_app/register_student.html')

@login_required(login_url='/login/')
def register_student_submit(request):
    """ Handle student event registration submission. """
    name = request.POST['name']
    email = request.POST['email']
    phoneno = request.POST['phoneno']
    event = request.POST['event']

    Student_Info = StudentInfo(uname=name, email=email, phoneno=phoneno, event=event)
    Student_Info.save()
    messages.success(request, 'You have successfully registered.')
    
    return render(request, 'TPO_app/register_student.html')

# ==============================
# Job Registration Views
# ==============================

@login_required(login_url='/login/')
def register_job(request):
    """ Render the job registration page. """
    return render(request, 'includes/register_job.html')

@login_required(login_url='/login/')
def register_job_submit(request):
    """ Handle job application submission. """
    name = request.POST['name']
    email = request.POST['email']
    phoneno = request.POST['phoneno']
    college = request.POST['college']
    graduation = request.POST['graduation']
    company = request.POST['company']
    profile = request.POST['profile']

    Job_Info = JobInfo(uname=name, email=email, phoneno=phoneno, college=college, 
                       graduation=graduation, company=company, profile=profile)
    Job_Info.save()
    messages.success(request, 'Your Application is successfully sent.')
    
    return render(request, 'includes/register_job.html')

# ==============================
# Event Management Views
# ==============================

def upcoming_events(request):
    """ Render upcoming events page. """
    return render(request, 'includes/upcoming_events.html')

def upcoming_events_submit(request):
    """ Handle event creation. """
    eventname = request.POST['eventname']
    description = request.POST['description']
    eventdate = request.POST['eventdate']

    Event_Info = EventInfo(eventname=eventname, description=description, eventdate=eventdate)
    Event_Info.save()
    messages.success(request, 'Your Event is successfully saved.')
    
    return render(request, 'includes/upcoming_events.html')

# ==============================
# Company Management Views
# ==============================

def companies_list(request):
    companies = CompanyInfo.objects.all()
    return render(request, 'companies_list.html', {'companies': companies})

def add_company(request):
    """ Render company addition form. """
    return render(request, 'includes/add_company.html')

def add_company_submit(request):
    """ Handle new company submission. """
    cname = request.POST['cname']
    role = request.POST['role']
    salary = request.POST['salary']

    Company_Info = CompanyInfo(cname=cname, role=role, salary=salary)
    Company_Info.save()
    messages.success(request, 'Your Company is successfully saved.')
    
    return render(request, 'includes/add_company.html')

# ==============================
# Machine Learning-Based Student Clustering
# ==============================
def preprocess_skills(skill_string):
    """ 
    Convert skills to lowercase, remove spaces, and return a set for case-insensitive, order-independent matching. 
    """
    if not skill_string:
        return set()  # Handle missing values safely

    return set(map(str.strip, skill_string.casefold().split(",")))

def cluster_students_by_similarity(students, threshold=0.60):
    """ Cluster students based on skill similarity using Cosine Similarity & Agglomerative Clustering. """

    if not students:
        return [], None, None

    # Extract and preprocess skills
    skills_list = [student.skills for student in students]
    preprocessed_skills = [" ".join(sorted(preprocess_skills(skill))) for skill in skills_list]

    # Vectorize skills using TF-IDF
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(preprocessed_skills)

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(X)

    # Convert similarity matrix to a distance matrix
    distance_matrix = 1 - similarity_matrix

    # Perform Agglomerative Clustering
    clustering = AgglomerativeClustering(
        n_clusters=None, metric="precomputed", linkage="average", distance_threshold=1 - threshold
    )
    
    labels = clustering.fit_predict(distance_matrix)

    return labels, clustering, vectorizer

@staff_member_required
def cluster_students_view(request):
    """ Cluster students based on 75% skill similarity and display them by cluster labels. """
    students = Student.objects.all()

    if not students.exists():
        return render(request, 'TPO_app/cluster_students.html', {'message': "No students found."})

    labels, clustering, vectorizer = cluster_students_by_similarity(students, threshold=0.75)

    # Assign clusters to students
    for student, label in zip(students, labels):
        student.cluster_label = label
        student.save()

    # Group students by cluster
    students_by_cluster = {}
    for student in students:
        cluster_name = f"Cluster {student.cluster_label + 1}"
        if cluster_name not in students_by_cluster:
            students_by_cluster[cluster_name] = []
        students_by_cluster[cluster_name].append(student)

    return render(request, 'TPO_app/cluster_students.html', {'students_by_cluster': students_by_cluster})

def recommend_companies(student_skills, companies, top_n=5):
    """ Recommend companies based on the student's skills using Cosine Similarity. """

    if not companies:
        return []

    # Preprocess student skills
    student_skills = " ".join(sorted(preprocess_skills(student_skills)))

    # Extract and preprocess company skill requirements
    company_skills = [" ".join(sorted(preprocess_skills(company.required_skills))) for company in companies]

    # Vectorize skills using TF-IDF
    vectorizer = TfidfVectorizer()
    skill_vectors = vectorizer.fit_transform([student_skills] + company_skills)

    # Compute cosine similarity (Student vs. Companies)
    similarity_scores = cosine_similarity(skill_vectors[0], skill_vectors[1:]).flatten()

    # Rank companies based on similarity scores
    sorted_indices = similarity_scores.argsort()[::-1]  # Sort in descending order
    top_companies = [companies[i] for i in sorted_indices[:top_n]]

    return top_companies

@staff_member_required
def suggest_companies_view(request, student_id):
    """ Recommend companies based on student skills using ML. """
    student = get_object_or_404(Student, id=student_id)
    companies = Company_ML.objects.all()

    # Convert skills to lowercase for case-insensitive matching
    student_skills = set(student.skills.lower().split(','))
    
    recommended_companies = []

    for company in companies:
        # Assuming company.skills is a string of skills in a similar format as student.skills
        company_skills = set(company.skills.lower().split(','))
        
        # Calculate the intersection of skills
        common_skills = student_skills.intersection(company_skills)

        # Calculate the percentage match
        match_percentage = (len(common_skills) / len(company_skills)) * 100 if company_skills else 0

        # If the match percentage is greater than or equal to 50%, recommend the company
        if match_percentage >= 50:
            recommended_companies.append({
                'company': company,
                'match_percentage': match_percentage
            })

    return render(request, 'TPO_app/recommended_companies.html', {
        'student': student,
        'recommended_companies': recommended_companies
    })

# ==============================
# Miscellaneous Views
# ==============================

def Statistics(request):
    """ Render placement statistics page. """
    return render(request, 'includes/Statistics.html')

def student_success(request):
    """ Render student success page after successful form submission. """
    return render(request, 'student_success.html')


def companies(request):
    """ Render a list of all companies. """
    companies = CompanyInfo.objects.all()  # Fetch all companies from the database
    return render(request, 'TPO_app/companies_list.html', {'companies': companies})

def companies_list(request):
    """ View to display the list of companies. """
    companies = CompanyInfo.objects.all()  # Fetch all companies from the database
    return render(request, 'TPO_app/companies_list.html', {'companies': companies})

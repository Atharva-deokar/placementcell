from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student
from .models import Company
from .models import CompanyInfo
from .models import Company_ML

class CompanyMLForm(forms.ModelForm):
    class Meta:
        model = Company_ML
        fields = ['name', 'required_skills', 'num_posts', 'prev_yr_1', 'prev_yr_2', 'prev_yr_3', 'prev_yr_4', 'prev_yr_5']

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'  # Or specify the fields you want in the form
        # You can customize widgets if needed (e.g., for the image field)
        widgets = {
            'image': forms.FileInput,  # Makes it a file input field
        }

# ===========================
# Student Form (Admin Only)
# ===========================
class StudentForm(forms.ModelForm):
    """ Form to allow admin to add student details """
    
    class Meta:
        model = Student
        fields = ['name', 'email', 'phone_number', 'skills', 'experience', 'cgpa', 'course_subdomain']
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter skills separated by commas'}),
            'experience': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter relevant experience'}),
        }

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})  # Apply Bootstrap styling

# ===========================
# User Registration Form
# ===========================
class RegisterForm(UserCreationForm):
    """ Form for user registration """
    
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})  # Apply Bootstrap styling

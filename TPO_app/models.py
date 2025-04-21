from django.db import models


class Company_ML(models.Model):
    name = models.CharField(max_length=255, unique=True)
    required_skills = models.TextField(help_text="Comma-separated skills required")
    num_posts = models.IntegerField(default=1, help_text="Number of job openings")
    prev_yr_1 = models.IntegerField(default=0, help_text="Job openings 1 year ago")
    prev_yr_2 = models.IntegerField(default=0, help_text="Job openings 2 years ago")
    prev_yr_3 = models.IntegerField(default=0, help_text="Job openings 3 years ago")
    prev_yr_4 = models.IntegerField(default=0, help_text="Job openings 4 years ago")
    prev_yr_5 = models.IntegerField(default=0, help_text="Job openings 5 years ago")

    def __str__(self):
        return f"{self.name} ({self.num_posts} Posts)"


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='company_images/', blank=True, null=True)  # For company logos
    salary_range = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    posted_date = models.DateField(blank=True, null=True) # Date when the job was posted

    def __str__(self):
        return self.name

class RoundResult(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.CharField(max_length=255, blank=True, null=True)
    result_file = models.FileField(upload_to='round_results/', blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.company.name} - {self.role} - Result"

class UpcomingCompany(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    brochure = models.FileField(upload_to='upcoming_company_brochures/', blank=True, null=True)

    def __str__(self):
        return f"{self.company.name} - Upcoming"

# Create your models here.

class Student(models.Model):
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    skills = models.TextField(help_text="List of skills, separated by commas.")
    experience = models.TextField(help_text="Any relevant experience.")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    course_subdomain = models.CharField(max_length=25)

    def __str__(self):
        return self.name
    
class StudentInfo(models.Model):
    uname = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=200)
    phoneno = models.CharField(max_length=200)
    event = models.CharField(max_length=20)
    
    def __str__(self):
        return self.uname

class JobInfo(models.Model):
    uname = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=200)
    phoneno = models.CharField(max_length=200)
    college = models.CharField(max_length=20)
    graduation = models.DecimalField(max_digits=19, decimal_places=2)
    company = models.CharField(max_length=200)
    profile = models.CharField(max_length=200)

    def __str__(self):
        return self.company
        
class EventInfo(models.Model):
    eventname = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    eventdate = models.CharField(max_length=200)
    
    def __str__(self):
        return self.eventname

class CompanyInfo(models.Model):
    cname = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    salary = models.CharField(max_length=200)
    
    def __str__(self):
        return self.cname


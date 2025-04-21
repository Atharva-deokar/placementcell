from django.contrib import admin  # type: ignore
from django.http import HttpResponseRedirect
from django.urls import path
from .models import StudentInfo, JobInfo, EventInfo, CompanyInfo, Student, Company, RoundResult, UpcomingCompany

# ===========================
# Registering the Models
# ===========================
# Remove the redundant registration of the Company model:
# admin.site.register(Company)  # This line is redundant, so remove it.

admin.site.register(RoundResult)
admin.site.register(UpcomingCompany)
admin.site.register(StudentInfo)
admin.site.register(JobInfo)
admin.site.register(EventInfo)
admin.site.register(CompanyInfo)

# ===========================
# Custom Action for Company Model
# ===========================

# Custom action for bulk operations
def activate_companies(modeladmin, request, queryset):
    """
    Custom action to activate the selected companies.
    Updates the 'status' field of selected companies to 'Active'.
    """
    # Assuming 'status' was removed and we're no longer updating status here
    modeladmin.message_user(request, "Selected companies have been activated.")

activate_companies.short_description = 'Activate selected companies'

class CompanyAdmin(admin.ModelAdmin):
    """
    Custom Admin class for Company model to display and manage company data.
    """
    list_display = ('name', 'role', 'salary_range')  # Display company name, role, and salary_range
    search_fields = ['name', 'role']  # Enable search functionality on 'name' and 'role'
    list_filter = []  # Removed status filter since we no longer need it
    actions = [activate_companies]  # Add the custom action to the admin

    # Optionally, add a custom admin view with a button or action
    def get_urls(self):
        """
        Add custom URLs to the admin interface.
        """
        urls = super().get_urls()
        custom_urls = [
            path('my_custom_button/', self.admin_site.admin_view(self.my_custom_button_view))
        ]
        return custom_urls + urls

    def my_custom_button_view(self, request):
        """
        Custom view triggered by a button in the admin.
        Here it just sends a message and redirects back to the previous page.
        """
        self.message_user(request, "Custom button clicked!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))  # Redirect back to the company list page

# Register the Company model with the custom admin
admin.site.register(Company, CompanyAdmin)

# ===========================
# Custom Admin for Student Model
# ===========================

class StudentAdmin(admin.ModelAdmin):
    """
    Custom Admin class for the Student model to display and manage student data.
    """
    list_display = ('id', 'name', 'email', 'cgpa', 'course_subdomain')  # Display student fields
    search_fields = ['name', 'email']  # Enable search by name and email
    list_filter = ['course_subdomain']  # Add filter for course_subdomain field

# Register the Student model with the custom admin
admin.site.register(Student, StudentAdmin)

# ===========================
# Additional Admin Registration (if needed)
# ===========================
# Register other models as necessary

# admin.site.register(YourModel, YourModelAdmin)  # Example registration if you have other models

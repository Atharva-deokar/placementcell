import fitz  # PyMuPDF
import tempfile
import os
import re
from datetime import datetime


def save_temp_file(pdf_file):
    """Temporarily save uploaded PDF."""
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, pdf_file.name)
    with open(temp_file_path, 'wb') as temp_file:
        for chunk in pdf_file.chunks():
            temp_file.write(chunk)
    return temp_file_path

def extract_pdf_details(file):
    """Extract details from the uploaded PDF resume."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text("text") for page in doc])

    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone_number': extract_phone(text),
        'skills': extract_skills(text),
        'experience': extract_experience(text),
        'cgpa': extract_cgpa(text),
        'course_subdomain': extract_course_subdomain(text),
    }

def extract_name(text):
    """Extracts name from the top of the resume."""
    lines = text.strip().split('\n')
    for line in lines:
        if re.match(r'^[A-Z][A-Za-z\s]+$', line.strip()):
            return line.strip()
    return "Name not found"

def extract_phone(text):
 # Updated regex to capture different variations of phone numbers
    phone_pattern = r'(?:Phone|Phone\.Mobile|Ph)[:\s]*(?:\+91[-\s]?|91[-\s]?)*(\d{10})'
    
    match = re.search(phone_pattern, text)
    if match:
        return match.group(1)  # Return the 10-digit phone number
    else:
        return None  # Return None if no phone number is found

def extract_email(text):
    """Extracts all email addresses in the resume."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return ', '.join(set(emails)) if emails else "Email not found"

def extract_skills(text):
    """Match known engineering skills from resume text."""
    skills_list = [
        'Python', 'Machine Learning', 'Deep Learning', 'Data Science', 'Data Analysis',
        'Tableau', 'SQL', 'R', 'C', 'C++', 'Java', 'JavaScript', 'Django', 'Flask',
        'Node.js', 'HTML', 'CSS', 'React', 'Angular', 'MongoDB', 'MySQL', 'PostgreSQL',
        'AWS', 'Azure', 'Google Cloud', 'TensorFlow', 'Keras', 'PyTorch', 'OpenCV',
        'MATLAB', 'AutoCAD', 'Linux', 'Git', 'GitHub', 'Docker', 'Kubernetes', 'PHP',
        'TypeScript', 'Blockchain', 'IoT', 'VLSI', 'Embedded Systems', 'UI/UX Design',
        'Operating Systems', 'Software Engineering', 'Agile', 'Scrum', 'DevOps',
        'Data Structures', 'Algorithms', 'Cyber Security', 'Network Security',
        'Virtualization', 'Cloud Computing', 'Microservices', 'Power BI', 'Excel',
        'Business Intelligence', 'Statistics', 'Natural Language Processing',
        'Project Management', 'Business Analysis', 'Rest APIs', 'Matplotlib', 'Seaborn',
        'Jenkins', 'C#', 'Ruby', 'Go', 'Rust', 'Shell Scripting', 'Revit', 'SolidWorks',
        'Simulink', 'Control Systems', 'Signal Processing', 'Quantum Computing'
    ]
    text_lower = text.lower()
    return ', '.join(sorted({s for s in skills_list if s.lower() in text_lower})) or "Skills not found"

def extract_experience(text):
    """ Extract experience duration from internships or jobs, avoiding academic projects. """

    # Remove 'ACADEMIC PROJECT' and everything after to exclude that section
    non_academic_text = text.split("ACADEMIC PROJECT")[0]

    # 1. Check for explicit duration mentions like '3 months' or '2 years'
    duration_matches = re.findall(r'(\d+)\s+(month|months|year|years)', non_academic_text, re.IGNORECASE)
    if duration_matches:
        total_months = 0
        for value, unit in duration_matches:
            value = int(value)
            if 'year' in unit.lower():
                total_months += value * 12
            else:
                total_months += value

        years = total_months // 12
        months = total_months % 12
        if years > 0:
            return f"{years} year(s) {months} month(s)"
        else:
            return f"{months} month(s)"

    # 2. Check for date range format like 'Jun’24 - Sep’24'
    range_match = re.search(r'([A-Za-z]{3})[’\']?(\d{2})\s*[-–]\s*([A-Za-z]{3})[’\']?(\d{2})', non_academic_text)
    if range_match:
        start_month, start_year, end_month, end_year = range_match.groups()
        try:
            start_date = datetime.strptime(f"{start_month} {start_year}", "%b %y")
            end_date = datetime.strptime(f"{end_month} {end_year}", "%b %y")
            duration_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            years = duration_months // 12
            months = duration_months % 12
            if years > 0:
                return f"{years} year(s) {months} month(s)"
            else:
                return f"{months} month(s)"
        except ValueError:
            pass

    return "Experience not found"

def extract_cgpa(text):
    """Extracts CGPA assuming it's near the keyword 'CGPA'."""
    cgpa_match = re.search(r'CGPA[:\s]*([0-9]+\.[0-9]+)', text, re.IGNORECASE)
    return cgpa_match.group(1) if cgpa_match else "CGPA not found"

def extract_course_subdomain(text):
    """Detect course subdomain based on keywords."""
    course_keywords = [
        "Artificial Intelligence", "Machine Learning", "Data Science", "Cyber Security",
        "Cloud Computing", "Computer Networks", "Operating Systems", "Software Engineering",
        "Web Development", "Mobile Development", "Embedded Systems", "Blockchain"
    ]
    for keyword in course_keywords:
        if keyword.lower() in text.lower():
            return keyword
    return "Course Subdomain not found"

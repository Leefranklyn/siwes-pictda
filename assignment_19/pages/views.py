from django.db.models import Count, Max
from django.shortcuts import render

from .forms import ContactForm, RegisterForm
from .models import Student


def home(request):
    """Render the landing page with live registration stats."""
    students = Student.objects.all()
    context = {
        'student_count': students.count(),
        'course_count': students.aggregate(total=Count('course', distinct=True))['total'],
        'latest_date': students.aggregate(latest=Max('registered_at'))['latest'],
    }
    return render(request, 'pages/home.html', context)


def about(request):
    """Render the about page."""
    return render(request, 'pages/about.html')


def contact(request):
    """Render the contact page with a contact form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            print(f"Contact message from {name} <{email}>: {message}")
            return render(request, 'pages/contact.html', {'form': ContactForm(), 'submitted': True})

    else:
        form = ContactForm()

    return render(request, 'pages/contact.html', {'form': form})


def register(request):
    """Render the register page with a student registration form."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'pages/register.html', {'form': RegisterForm(), 'submitted': True})

    else:
        form = RegisterForm()

    return render(request, 'pages/register.html', {'form': form})


def students(request):
    """Render the roster of all registered students, newest first."""
    students = Student.objects.order_by('-registered_at')
    course_count = students.aggregate(total=Count('course', distinct=True))['total']
    return render(request, 'pages/students.html', {'students': students, 'course_count': course_count})

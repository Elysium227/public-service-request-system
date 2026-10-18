from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import ServiceRequestForm
from .models import ServiceRequest


# Decorator: only allows logged-in staff users, others get a 403 page
def staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


# Landing page
def home(request):
    return render(request, "home.html")


# Citizen registration, logs the user in after signing up
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


# Citizen submits a new service request
@login_required
def submit_request(request):
    if request.method == "POST":
        form = ServiceRequestForm(request.POST, request.FILES)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.citizen = request.user
            service_request.save()
            return redirect("my_requests")
    else:
        form = ServiceRequestForm()
    return render(request, "submit_request.html", {"form": form})


# Shows only the logged-in citizen's own requests
@login_required
def my_requests(request):
    requests_list = ServiceRequest.objects.filter(citizen=request.user).order_by("-created_at")
    return render(request, "my_requests.html", {"requests_list": requests_list})


# Admin view: all requests, filters and analytics counts
@staff_required
def admin_dashboard(request):
    all_requests = ServiceRequest.objects.select_related("citizen").order_by("-created_at")
    pending_count = ServiceRequest.objects.filter(status="pending").count()
    in_progress_count = ServiceRequest.objects.filter(status="in_progress").count()
    resolved_count = ServiceRequest.objects.filter(status="resolved").count()
    context = {
        "all_requests": all_requests,
        "status_choices": ServiceRequest.STATUS_CHOICES,
        "total_count": ServiceRequest.objects.count(),
        "open_count": pending_count + in_progress_count,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
    }
    return render(request, "admin_dashboard.html", context)


# Admin changes the status of one request
@staff_required
def update_status(request, pk):
    if request.method == "POST":
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        new_status = request.POST.get("status")
        valid_statuses = [choice[0] for choice in ServiceRequest.STATUS_CHOICES]
        if new_status in valid_statuses:
            service_request.status = new_status
            service_request.save()
    return redirect("admin_dashboard")
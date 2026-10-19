import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
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
            messages.success(request, "Account created. Welcome!")
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
            messages.success(request, f"Your request has been submitted. Reference: {service_request.reference}")
            return redirect("my_requests")
    else:
        form = ServiceRequestForm()
    return render(request, "submit_request.html", {"form": form})


# Shows only the logged-in citizen's own requests
@login_required
def my_requests(request):
    requests_list = ServiceRequest.objects.filter(citizen=request.user).order_by("-created_at")
    return render(request, "my_requests.html", {"requests_list": requests_list})


# Applies the status and category filters from the query string.
# Shared by the dashboard and the CSV export so both show the same rows.
def filtered_requests(request):
    queryset = ServiceRequest.objects.select_related("citizen").order_by("-created_at")
    status_filter = request.GET.get("status", "")
    category_filter = request.GET.get("category", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category_filter:
        queryset = queryset.filter(category=category_filter)
    return queryset, status_filter, category_filter


# Admin view: all requests, filters, analytics counts and charts
@staff_required
def admin_dashboard(request):
    all_requests, status_filter, category_filter = filtered_requests(request)

    total_count = ServiceRequest.objects.count()
    pending_count = ServiceRequest.objects.filter(status="pending").count()
    in_progress_count = ServiceRequest.objects.filter(status="in_progress").count()
    resolved_count = ServiceRequest.objects.filter(status="resolved").count()

    def percent(count):
        return round(count * 100 / total_count) if total_count else 0

    # Doughnut chart: one coloured slice per status
    pending_end = percent(pending_count)
    progress_end = min(100, pending_end + percent(in_progress_count))
    chart_gradient = (
        f"conic-gradient(#f59e0b 0 {pending_end}%, "
        f"#3b82f6 {pending_end}% {progress_end}%, "
        f"#22c55e {progress_end}% 100%)"
    )

    # Bar chart: number of requests per category, longest bar is 100% wide
    category_names = dict(ServiceRequest.CATEGORY_CHOICES)
    category_rows = list(
        ServiceRequest.objects.values("category").annotate(n=Count("id")).order_by("-n")
    )
    longest_bar = category_rows[0]["n"] if category_rows else 1
    category_stats = [
        {
            "label": category_names.get(row["category"], row["category"]),
            "count": row["n"],
            "width": round(row["n"] * 100 / longest_bar),
        }
        for row in category_rows
    ]

    context = {
        "all_requests": all_requests,
        "status_choices": ServiceRequest.STATUS_CHOICES,
        "category_choices": ServiceRequest.CATEGORY_CHOICES,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "total_count": total_count,
        "open_count": pending_count + in_progress_count,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
        "pending_pct": percent(pending_count),
        "in_progress_pct": percent(in_progress_count),
        "resolved_pct": percent(resolved_count),
        "chart_gradient": chart_gradient,
        "category_stats": category_stats,
    }
    return render(request, "admin_dashboard.html", context)


# Stops spreadsheet apps from treating a cell as a formula
def csv_safe(value):
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text


# Admin downloads the requests as a CSV file, respecting the dashboard filters
@staff_required
def export_csv(request):
    queryset, _, _ = filtered_requests(request)
    filename = f"service_requests_{timezone.localdate()}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")  # lets Excel read the file as UTF-8
    writer = csv.writer(response)
    writer.writerow(["Reference", "Citizen", "Category", "Priority", "Status", "Location", "Description", "Submitted"])
    for r in queryset:
        writer.writerow([
            r.reference,
            csv_safe(r.citizen.username),
            r.get_category_display(),
            r.get_priority_display(),
            r.get_status_display(),
            csv_safe(r.location),
            csv_safe(r.description),
            timezone.localtime(r.created_at).strftime("%Y-%m-%d %H:%M"),
        ])
    return response


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
            messages.success(request, f"Status updated to {service_request.get_status_display()}.")
    return redirect("admin_dashboard")


# Detail page for one request: only the owner or staff can open it
@login_required
def request_detail(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if service_request.citizen != request.user and not request.user.is_staff:
        raise PermissionDenied
    return render(request, "request_detail.html", {"r": service_request})
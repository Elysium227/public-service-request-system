from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import ServiceRequestForm
from .models import ServiceRequest


def home(request):
    return render(request, "home.html")


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


@login_required
def my_requests(request):
    requests_list = ServiceRequest.objects.filter(citizen=request.user).order_by("-created_at")
    return render(request, "my_requests.html", {"requests_list": requests_list})
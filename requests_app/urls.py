from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("submit/", views.submit_request, name="submit_request"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
        path("dashboard/update/<int:pk>/", views.update_status, name="update_status"),
]
from django.db import models
from django.contrib.auth.models import User


class ServiceRequest(models.Model):
    CATEGORY_CHOICES = [
        ("streetlight", "Broken Streetlight"),
        ("water", "Water Issue"),
        ("garbage", "Garbage Collection"),
        ("road", "Road Damage"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="request_images/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} at {self.location}"
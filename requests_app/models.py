from django.db import models
from django.contrib.auth.models import User


# A service request submitted by a citizen, tracked through three statuses
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

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    location = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="request_images/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} at {self.location}"

    @property
    def reference(self):
        # Readable reference number built from the database id, e.g. REQ-0007
        return f"REQ-{self.pk:04d}"
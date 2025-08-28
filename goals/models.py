from django.db import models
from users.models import User

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Goal(models.Model):
    STATE_CHOICES = [
        ("pending", "Pendiente"),
        ("done", "Realizado"),
        ("cancelled", "Cancelado"),
    ]

    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    ]

    FOCUS_CHOICES = [
        ("Depth", "Depth"),
        ("Breadth", "Breadth"),
        ("Speed", "Speed"),
    ]

    CHECKPOINTS_CHOICES = [
        ("weekly", "Weekly"),
        ("biweekly", "Biweekly"),
        ("none", "None"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goals"
    )

    title = models.CharField(max_length=255)
    deadline = models.DateField()
    availability = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="pending")

    # Campos nuevos
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True)
    formats = models.JSONField(blank=True, null=True)  # lista de strings
    session_length = models.PositiveIntegerField(blank=True, null=True)  # minutos
    focus = models.CharField(max_length=20, choices=FOCUS_CHOICES, blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)  # "es", "en", etc.
    checkpoints = models.CharField(max_length=20, choices=CHECKPOINTS_CHOICES, blank=True, null=True)

    # Ubicación
    country_code = models.CharField(max_length=5, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_state_display()})"

class Objective(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("done", "Realizado"),
        ("cancelled", "Cancelado"),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="objectives")
    title = models.CharField(max_length=255)
    description = models.TextField()
    scheduled_at = models.DateTimeField()  # Fecha y hora del objetivo
    youtube_links = models.TextField(blank=True, null=True)  # Guardamos links separados por comas
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # 🔹 Nuevo campo para imagen Base64
    image_url = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Objective for {self.goal.title}: {self.description[:30]}"

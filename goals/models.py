from django.db import models
from users.models import User

class Goal(models.Model):
    STATE_CHOICES = [
        ("pending", "Pendiente"),
        ("done", "Realizado"),
        ("cancelled", "Cancelado"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=255)  # La meta principal
    deadline = models.DateField()  # Plazo límite
    availability = models.TextField(blank=True, null=True)  # Ej: horarios disponibles
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="pending")

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Objective for {self.goal.title}: {self.description[:30]}"

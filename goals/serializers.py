
# serializers.py
from rest_framework import serializers
from .models import Goal, Objective

class ObjectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Objective
        fields = "__all__"

class GoalSerializer(serializers.ModelSerializer):
    objectives = ObjectiveSerializer(many=True, read_only=True)  # Relación con objectives

    class Meta:
        model = Goal
        fields = "__all__"

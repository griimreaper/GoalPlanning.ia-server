# my_app/urls.py
from django.urls import path
from .views import (
    generate_objectives,
    get_goal_detail,
    get_goals,
    delete_goal,
    update_goal,
    update_objective,
    review_objective,
    extend_goal,
)

urlpatterns = [
    path('generate-objectives/', generate_objectives, name='generate_objectives'),
    path('', get_goals, name='get_goals'),
    path('<int:goal_id>/', get_goal_detail, name='get_goal_detail'),
    path('<int:goal_id>/delete/', delete_goal, name='delete_goal'),
    path('<int:goal_id>/update/', update_goal, name='update_goal'),
    path('<int:goal_id>/objectives/<int:objective_id>/update/', update_objective, name='update_objective'),
    path("<int:goal_id>/objectives/<int:objective_id>/review/", review_objective, name="review_objective"),
    path('<int:goal_id>/extend/', extend_goal, name='extend_goal'),
]

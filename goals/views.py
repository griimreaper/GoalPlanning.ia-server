# my_app/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from google import genai
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
import json, re
from .models import Goal, Objective
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .serializers import GoalSerializer
from rest_framework import status
from googleapiclient.discovery import build
import os

load_dotenv()
client = genai.Client()

hoy = date.today().strftime("%Y-%m-%d")

def get_youtube_first_video(query: str) -> str:
    api_key = os.getenv("YOUTUBE_API_KEY")
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=1
    )
    response = request.execute()
    items = response.get("items", [])
    if not items:
        return ""
    video_id = items[0]["id"]["videoId"]
    return f"https://www.youtube.com/watch?v={video_id}"

@api_view(['POST'])
def generate_objectives(request):
    data = request.data
    user = request.user
    meta = data.get("meta")
    plazo_dias = data.get("plazo_dias")
    disponibilidad = data.get("disponibilidad")

    if not meta or not plazo_dias or not disponibilidad:
        return Response({"error": "Faltan parámetros"}, status=400)

    hoy = date.today().strftime("%Y-%m-%d")

    prompt = f"""
Eres un asistente que planifica metas de aprendizaje de manera práctica.
Meta del usuario: "{meta}"
Plazo: {plazo_dias} días
Disponibilidad diaria: {disponibilidad}
Genera un plan de objetivos diarios empezando desde hoy ({hoy}), la cantidad de objetivos debe ser acorde al plazo fijado por el usuario.
- Cada objetivo debe incluir: título, descripción, fecha y hora exacta (no solo la fecha), basadas en la disponibilidad horaria del usuario.
- 1 frases de búsqueda en YouTube.
Devuelve la respuesta en JSON con el formato:
{{
  "goal": {{"title": "...", "plazo_dias": X, "disponibilidad": "..."}},
  "objectives": [
    {{"title": "...", "description": "...", "deadline": "YYYY-MM-DD HH:MM", "youtube_search": "URL"}},
    ...
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw_text = response.text
    match = re.search(r'```json\n(.*)```', raw_text, re.DOTALL)
    json_text = match.group(1) if match else raw_text

    try:
        ia_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print("Error al parsear JSON generado por la IA:", e)
        print("Texto crudo recibido de la IA:", raw_text)
        return Response(
            {"error": "No se pudo parsear el JSON generado por la IA", "raw": raw_text},
            status=500
        )

    goal_data = ia_data["goal"]
    deadline = date.today() + timedelta(days=int(goal_data["plazo_dias"]))
    goal = Goal.objects.create(
        user=user,
        title=goal_data["title"],
        deadline=deadline,
        availability=goal_data.get("disponibilidad", ""),
        state="pending"
    )

    for obj in ia_data.get("objectives", []):
        # La IA debe entregar fecha + hora en 'deadline'
        scheduled_at = datetime.strptime(obj['deadline'], "%Y-%m-%d %H:%M")

        # Buscar el primer video de YouTube según título o descripción
        youtube_link = get_youtube_first_video(obj.get('youtube_search'))

        Objective.objects.create(
            goal=goal,
            title=obj.get('title', ''),
            description=obj.get('description', ''),
            scheduled_at=scheduled_at,
            youtube_links=youtube_link,
            status='pending'
        )

    return Response({"goal_id": goal.id}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_goals(request):
    """
    Devuelve todas las metas del usuario autenticado (sin objetivos).
    """
    user = request.user
    metas = Goal.objects.filter(user=user).order_by('-id')  # las más recientes primero

    resultado = [
        {
            "id": goal.id,
            "title": goal.title,
            "plazo_dias": (goal.deadline - date.today()).days,  # calcular al vuelo
            "disponibilidad": goal.availability,
            "state": goal.state
        }
        for goal in metas
    ]

    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_goal_detail(request, goal_id):
    """
    Devuelve una meta específica con todos sus objetivos.
    """
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)

    # obtener objetivos relacionados
    serializer = GoalSerializer(goal)
    return Response(serializer.data)

# Eliminar una meta
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_goal(request, goal_id):
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    goal.delete()
    return Response({"message": "Meta eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)

# Actualizar una meta (opcional)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_goal(request, goal_id):
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    serializer = GoalSerializer(goal, data=request.data, partial=True)  # partial=True permite actualizar solo algunos campos
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Actualizar un objetivo individual
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_objective(request, goal_id, objective_id):
    """
    Actualiza un objetivo específico de una meta del usuario.
    Se puede actualizar: title, description, scheduled_at, youtube_links, status
    """
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    objective = get_object_or_404(Objective, id=objective_id, goal=goal)

    # Actualización parcial
    data = request.data
    if 'title' in data:
        objective.title = data['title']
    if 'description' in data:
        objective.description = data['description']
    if 'scheduled_at' in data:
        try:
            # se espera formato "YYYY-MM-DD HH:MM"
            objective.scheduled_at = datetime.strptime(data['scheduled_at'], "%Y-%m-%d %H:%M")
        except ValueError:
            return Response({"error": "Formato de fecha incorrecto, usar YYYY-MM-DD HH:MM"}, status=400)
    if 'youtube_links' in data:
        objective.youtube_links = data['youtube_links']
    if 'status' in data:
        objective.status = data['status']

    objective.save()
    return Response({
        "id": objective.id,
        "title": objective.title,
        "description": objective.description,
        "scheduled_at": objective.scheduled_at,
        "youtube_links": objective.youtube_links,
        "status": objective.status
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_objective(request, goal_id, objective_id):
    """
    Recibe feedback del usuario (difficulty, interest, time, comment)
    y usa la IA para adaptar el objetivo.
    """
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    objective = get_object_or_404(Objective, id=objective_id, goal=goal)

    data = request.data
    difficulty = data.get("difficulty")
    interest = data.get("interest")
    time = data.get("time")
    comment = data.get("comment", "")

    if not difficulty or not interest or not time:
        return Response({"error": "Faltan parámetros obligatorios"}, status=400)

    # Prompt para la IA
    prompt = f"""
Eres un asistente que adapta planes de aprendizaje según el feedback del usuario.
El objetivo original es:
"{objective.description}"

El usuario dio este feedback:
- Dificultad: {difficulty}
- Interés: {interest}
- Tiempo: {time}
- Comentario adicional: {comment}

Tu tarea es reescribir o ajustar el objetivo para que:
- Se mantenga alineado con la meta general.
- Se adapte mejor al nivel de dificultad, interés y tiempo del usuario.
- 1 frases de búsqueda en YouTube.

Devuelve SOLO un JSON con el formato:
{{
  "title": "...",
  "description": "...",
  "scheduled_at": "YYYY-MM-DD HH:MM",
  "youtube_search": "..."
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text
        match = re.search(r'```json\n(.*)```', raw_text, re.DOTALL)
        json_text = match.group(1) if match else raw_text

        new_data = json.loads(json_text)
    except Exception as e:
        return Response(
            {"error": "No se pudo procesar la respuesta de la IA", "raw": raw_text if 'raw_text' in locals() else str(e)},
            status=500
        )

    # Actualizamos el objetivo
    if "title" in new_data:
        objective.title = new_data["title"]
    if "description" in new_data:
        objective.description = new_data["description"]
    if "scheduled_at" in new_data:
        try:
            objective.scheduled_at = datetime.strptime(new_data["scheduled_at"], "%Y-%m-%d %H:%M")
        except ValueError:
            pass
    if "youtube_search" in new_data:
        objective.youtube_links = get_youtube_first_video(new_data['youtube_search'])

    objective.save()

    return Response({
        "id": objective.id,
        "title": objective.title,
        "description": objective.description,
        "scheduled_at": objective.scheduled_at,
        "youtube_links": objective.youtube_links,
        "status": objective.status
    }, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extend_goal(request, goal_id):
    """
    Extiende una meta agregando objetivos nuevos según el wizard del usuario.
    Recibe: extension (1 week / 1 month), level (easier / harder / same),
             priority (tipo de organización), comment (opcional)
    """
    user = request.user
    goal = get_object_or_404(Goal, id=goal_id, user=user)
    data = request.data
    extension = data.get("extension")
    level = data.get("level")
    priority = data.get("priority")
    comment = data.get("comment", "")

    if not extension or not level or not priority:
        return Response({"error": "Faltan parámetros obligatorios"}, status=400)

    # 1️⃣ Calcular días a agregar
    if extension == "1 week":
        days_to_add = 7
    elif extension == "1 month":
        days_to_add = 30
    else:
        return Response({"error": "Valor de extensión no válido"}, status=400)

    # 2️⃣ Obtener fecha del último objetivo
    last_objective = goal.objectives.order_by('-scheduled_at').first()
    start_date = last_objective.scheduled_at + timedelta(days=1) if last_objective else datetime.now()

    # 3️⃣ Generar prompt para IA
    prompt = f"""
Eres un asistente que planifica objetivos diarios para metas de aprendizaje.
Meta actual: "{goal.title}"
Último objetivo: "{last_objective.description if last_objective else 'Ninguno'}" ({start_date.strftime('%Y-%m-%d')})

Agrega {days_to_add} nuevos objetivos diarios empezando desde el día siguiente.
- Dificultad: {level}
- Organización: {priority}
- Comentario adicional del usuario: {comment}

Devuelve SOLO un JSON con la clave "objectives":
- Cada objetivo debe incluir: título, descripción, fecha y hora exacta (no solo la fecha), basadas en la disponibilidad horaria del usuario.
- 1 frases de búsqueda en YouTube.
[
  {{"title": "...", "description": "...", "scheduled_at": "YYYY-MM-DD HH:MM", youtube_search": "..."}},
  ...
]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text
        match = re.search(r'```json\n(.*)```', raw_text, re.DOTALL)
        json_text = match.group(1) if match else raw_text
        new_objectives_data = json.loads(json_text).get("objectives", [])
    except Exception as e:
        return Response({"error": "Error procesando la IA", "raw": raw_text if 'raw_text' in locals() else str(e)}, status=500)

    # 4️⃣ Crear los nuevos objetivos
    created_objectives = []
    for obj in new_objectives_data:
        try:
            scheduled_at = datetime.strptime(obj['scheduled_at'], "%Y-%m-%d %H:%M")

            # Buscar el primer video de YouTube según título o descripción
            youtube_link = get_youtube_first_video(obj.get('youtube_search'))
        except ValueError:
            scheduled_at = start_date
        new_obj = Objective.objects.create(
            goal=goal,
            title=obj.get('title', ''),
            description=obj.get('description', ''),
            scheduled_at=scheduled_at,
            youtube_links=youtube_link,
            status='pending'
        )
        created_objectives.append({
            "id": new_obj.id,
            "title": new_obj.title,
            "description": new_obj.description,
            "scheduled_at": new_obj.scheduled_at,
            "youtube_links": youtube_link,
            "status": new_obj.status
        })

    # 5️⃣ Actualizar deadline de la meta
    goal.deadline += timedelta(days=days_to_add)
    goal.save()

    return Response({"new_objectives": created_objectives, "new_deadline": goal.deadline}, status=200)
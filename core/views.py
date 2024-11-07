from datetime import timezone
from typing import List

from django.http import Http404
from django.shortcuts import get_object_or_404
from core.models import Formation, UserFormationPurchase
from core.schemas import FormationDetailSchema, FormationResponseSchema, FormationSchema, ModuleSchema, RegisterSchema, LoginSchema
from .jwt_utils import create_token, verify_token
from django.contrib.auth.models import User
from ninja import Router
from django.contrib.auth.hashers import make_password, check_password

# Router Ninja pour l'API d'authentification
router = Router()

# Vue d'inscription


@router.post("/register", response={201: dict, 400: dict})
def register(request, data: RegisterSchema):
    if User.objects.filter(email=data.email).exists():
        return 400, {"detail": "Un utilisateur avec cet e-mail existe déjà."}

    # Création de l'utilisateur avec un mot de passe hashé
    user = User.objects.create(
        username=data.username,
        email=data.email,
        password=make_password(data.password)
    )

    return 201, {"detail": "Utilisateur créé avec succès."}

# Exemple de création de token lors de la connexion


@router.post("/login", response={200: dict, 401: dict})
def login(request, data: LoginSchema):
    try:
        user = User.objects.get(email=data.email)
        if not check_password(data.password, user.password):
            return 401, {"detail": "Mot de passe incorrect"}

        # Créer le token d'accès
        access_token = create_token({"id": user.id, "email": user.email})

        return 200, {"access_token": access_token, "name": user.username,"id":user.id}
    except User.DoesNotExist:
        return 401, {"detail": "Utilisateur non trouvé"}

# FORMATION


@router.get("/formations", response=List[FormationSchema])
def get_formations(request):
    # Récupérer toutes les formations
    formations = Formation.objects.all()
    # Formater les données pour chaque formation
    formatted_courses = []
    for formation in formations:
        # Compter le nombre de vidéos associées à la formation
        video_count = formation.videos.count()

        # Formater les données dans le style souhaité
        formatted_course = {
            "id":formation.id,
            "title": formation.title,
            "price": f"{formation.price}",
            "lessons": f"{video_count} Leçons",
            "description": formation.description,
            # Convertir en chaîne de caractères
            "image": str(formation.image_url),
        }
        print(formatted_course)
        formatted_courses.append(formatted_course)

    return formatted_courses



@router.get("/formations/{formation_id}", response=FormationResponseSchema)
def get_formation_by_id(request, formation_id: int):
    try:
        # Retrieve the formation by ID
        formation = Formation.objects.get(id=formation_id)

        # Count the number of videos associated with the formation (if you have a "videos" relationship)
        video_count = formation.videos.count() if hasattr(formation, 'videos') else 0

        # Ensure that content is properly converted to string (in case it's a rich text field)
        content = str(formation.content) if hasattr(formation, 'content') else ""

        # Format the response
        formatted_course = FormationResponseSchema(
            title=formation.title,
            price=str(formation.price),  # Regular price of the course
            promoPrice=str(formation.promo_price),  # Promotional price
            promoDuration=(formation.promo_duration - timezone.now()).total_seconds() if formation.promo_duration else None,  # Promotion duration in seconds
            imageUrl=str(formation.image_url),  # Convert to string
            modules=[ModuleSchema(content=content)]  # List of modules
        )

        # Return the formatted response directly
        return formatted_course.dict()  # Return the dict, Ninja will handle the rest

    except Formation.DoesNotExist:
        raise Http404("Formation not found")
    

@router.get("/user/{user_id}/formations", response=list[FormationDetailSchema])
def get_user_formations(request, user_id: int):
    """
    Récupère les formations achetées par l'utilisateur, incluant le nom et l'URL de l'image de la formation.
    """
    # Vérifier si l'utilisateur existe
    user = get_object_or_404(User, id=user_id)

    # Récupérer les formations achetées par l'utilisateur
    purchases = UserFormationPurchase.objects.filter(user=user)

    # Construire la réponse avec le nom et l'URL de l'image pour chaque formation
    return [
        {"id":purchase.formation.id,"title": purchase.formation.title, "image_url": purchase.formation.image_url or ""}
        for purchase in purchases
    ]
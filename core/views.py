from datetime import timezone
import json
import mimetypes
import re
from typing import List, Optional
from urllib.parse import quote
from uuid import UUID
import uuid
import requests
from decouple import config
from django.http import Http404
from django.shortcuts import get_object_or_404
from core.minio_utils import generate_presigned_url_for_upload
from core.models import Formation, Payment, UserFormationPurchase
from core.schemas import FormationDetailSchema, FormationResponseSchema, FormationSchema, ModuleSchema, PaymentSchema, RegisterSchema, LoginSchema
from core.utils import get_currency_by_country
from .jwt_utils import create_token, verify_token
from django.contrib.auth.models import User
from ninja import File, Router, UploadedFile
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

        return 200, {"access_token": access_token, "name": user.username, "id": user.id}
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
            "id": formation.id,
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
def get_formation_by_id(request, formation_id: UUID):
    try:
        # Retrieve the formation by ID
        formation = Formation.objects.get(id=formation_id)

        # Count the number of videos associated with the formation (if you have a "videos" relationship)
        video_count = formation.videos.count() if hasattr(formation, 'videos') else 0

        # Ensure that content is properly converted to string (in case it's a rich text field)
        content = str(formation.content) if hasattr(
            formation, 'content') else ""

        # Format the response
        formatted_course = FormationResponseSchema(
            id=formation.id,
            title=formation.title,
            price=str(formation.price),  # Regular price of the course
            promoPrice=str(formation.promo_price),  # Promotional price
            promoDuration=(formation.promo_duration - timezone.now()).total_seconds(
            ) if formation.promo_duration else None,  # Promotion duration in seconds
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
        {"id": purchase.formation.id, "title": purchase.formation.title,
            "image_url": purchase.formation.image_url or ""}
        for purchase in purchases
    ]


@router.get("/formations/view/{formation_id}")
def get_formation_with_videos(request, formation_id: UUID):
    token = request.headers.get("Authorization").split(" ")[1]
    user_data = verify_token(token)
    user_id = user_data.get('id')
    # Vérifier si l'utilisateur a acheté la formation
    has_purchased = UserFormationPurchase.objects.filter(
        user_id=user_id,
        formation_id=formation_id
    ).exists()
    if not has_purchased:
        raise Http404("Formation not found")
    
    formation = get_object_or_404(Formation, id=formation_id)
    videos = formation.videos.all().order_by("ordre")

    # Adapter le retour pour le composant React
    return {
        "videos": [
            {
                "url": video.video_url,
                "title": video.title,
                "description": formation.title,
                "thumbnail": formation.image_url,
                "views": "",  # Champ vide
                "author": "Karine Academy",
            }
            for video in videos
        ],
    }


BASE_URL = "https://soleaspay.com/api/"


@router.post("pay/licence")
def creer_paiement(request, payment_data: PaymentSchema):
    print(payment_data)
    token = request.headers.get("Authorization").split(" ")[1]
    user_data = verify_token(token)
    user_id = user_data.get('id')
    # Récupérer l'utilisateur
    user = get_object_or_404(User, id=user_id)
    devise = get_currency_by_country(payment_data.country)
    formation = get_object_or_404(Formation, id=payment_data.formation_id)
    # Créer une instance de Payment
    payment = Payment.objects.create(
        user=user,
        formation=formation,
        name=payment_data.name,
        country=payment_data.country,
        mobile_number=payment_data.mobile_number,
        email=payment_data.email,
        otp=payment_data.otp,
        orderId=payment_data.orderId,
        operator=payment_data.operator,
        montant=payment_data.montant,
        devise_client=devise,
    )

    # Appeler l'API de paiement
    url = f"{BASE_URL}agent/bills"
    headers = {
        "x-api-key": config("X-API-KEY"),
        "operation": "2",
        # Utilisez l'opérateur depuis le schéma
        "service": str(payment_data.operator),
        "Content-Type": "application/json",
        "otp": payment_data.otp,
    }

    wallet = payment_data.mobile_number or payment_data.email

    payload = {
        "wallet": wallet,
        "amount": float(payment_data.montant),
        "currency": devise,
        "order_id": payment_data.orderId,
    }

    response = requests.post(url, headers=headers,
                             data=json.dumps(payload), timeout=300)
    response_data = response.json()
    print(response_data)
    if not response_data.get("success"):
        payment.status = "Echec"
        payment.save()
        return {"status": 400, "message": "Votre paiement a échoué. Merci de réessayer."}

    # Vérifier le lien de paiement
    if "data" in response_data and "payLink" in response_data["data"]:
        payUrl = response_data["data"]["payLink"]
        return {
            "status": 201,
            "url": payUrl,
            "message": "Vous allez être rediriger sur votre page de paiement.",
        }
    # Cas où la réponse indique un succès
    if response_data.get("success"):
        # Mise à jour du statut du paiement en "success"
        payment.status = "success"
        payment.save()
        user_formation_purchase, created = UserFormationPurchase.objects.get_or_create(
            user=user,
            formation=formation
        )

        # Retourner une réponse indiquant que le paiement a réussi
        return {
            "status": 200,
            "message": "Votre paiement a été effectué avec succès."
        }
    return {"status": 200, "message": "Paiement non traité, et aucun lien disponible."}


@router.post("callback/payin", auth=None)
def callbackPayin(request):
    # Récupérer le header
    header = request.headers
    key = header.get("X-Private-Key")
    print(header)
    if key == config("PAYOUT_KEY"):
        # Récupérer le contenu brut (Raw Content)
        raw_content = json.loads(request.body)
        print("status = ", raw_content.get("status"))
        if raw_content.get("status") == "SUCCESS":
            print("CALLBACK-------------------------------")
            order_id = raw_content.get("externalRef")
            payment = Payment.objects.filter(orderId=order_id).first()
            payment.status = "succes"
            payment.save()
            formation = payment.formation
            UserFormationPurchase.objects.create(
                user=payment.user, formation=formation)
            print('ok completed payin')
            # EMAIL
            return {"status": "success", "message": "Payment verified and user formation purchase created."}


@router.post("/generate-presigned-url", summary="Générer une URL présignée pour upload")
def get_presigned_url(request, file: UploadedFile = File(...)):
    """
    Endpoint pour générer une URL présignée permettant l'upload d'une vidéo.

    :param file: Fichier à uploader.
    :return: URL présignée, nom généré et type MIME du fichier.
    """
    try:
        # Extraire le nom et l'extension du fichier
        filename = file.name
        if '.' not in filename:
            raise ValueError("Le fichier doit avoir une extension valide (ex. .mp4).")
        base_name, ext = filename.rsplit('.', 1)

        # Valider l'extension
        valid_extensions = {'mp4', 'mov', 'avi', 'mkv'}  # Ajouter les extensions valides ici
        if ext.lower() not in valid_extensions:
            raise ValueError(f"L'extension '{ext}' n'est pas autorisée. Extensions valides : {', '.join(valid_extensions)}.")

        # Nettoyer le nom de base
        base_name = re.sub(r'[^a-zA-Z0-9\s]', '', base_name)  # Supprimer les caractères spéciaux
        base_name = base_name.replace(' ', '-')  # Remplacer les espaces par des tirets
        base_name = base_name.lower()  # Convertir en minuscules

        # Ajouter un UUID unique
        unique_filename = f"{base_name}_{uuid.uuid4()}.{ext}"

        # Encoder le nom pour l'URL
        encoded_filename = quote(unique_filename)

        # Déterminer le type MIME automatiquement
        content_type = mimetypes.guess_type(filename)[0]
        if not content_type:
            raise ValueError("Impossible de déterminer le type MIME du fichier.")

        # Générer l'URL présignée
        presigned_url = generate_presigned_url_for_upload(
            filename=encoded_filename,
            content_type=content_type,
            expires_in_minutes=60
        )

        return {
            "url": presigned_url,
            "filename": unique_filename,
            "content_type": content_type
        }

    except ValueError as e:
        return {
            "error": str(e)
        }

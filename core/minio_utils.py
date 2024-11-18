from datetime import timedelta
import os
from typing import Optional
import uuid
from django.conf import settings
from minio import Minio
from minio.error import S3Error
from tempfile import TemporaryFile
import logging
from urllib3 import PoolManager, Retry, Timeout
import time
# Configuration de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

http_client = PoolManager(
    timeout=Timeout(connect=5.0, read=15.0),
    retries=Retry(
        total=5,
        backoff_factor=0.2,
        status_forcelist=[500, 502, 503, 504],
    ),
)

# Initialiser le client MinIO
minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL,
    http_client=http_client
)


def upload_image_to_minio(file, filename):
    try:
        # Générer le chemin complet pour le fichier
        filename = f"images/{filename}"
        minio_client.put_object(
            settings.MINIO_IMAGE_BUCKET_NAME,
            filename,
            file,
            length=-1,  # -1 pour taille inconnue
            part_size=10 * 1024 * 1024,  # Diviser en parties de 10 MB si nécessaire
            content_type=file.content_type
        )
        file_url = f"https://{settings.MINIO_ENDPOINT}/{settings.MINIO_IMAGE_BUCKET_NAME}/{filename}"
        return file_url
    except S3Error as e:
        print(f"Erreur lors de l'upload de l'image : {e}")
        return None


def delete_image_from_minio(file_url):
    """Supprime une image de MinIO en utilisant son URL complète."""
    try:
        # Extraire le chemin du fichier après le bucket
        filename = '/'.join(file_url.split('/')[-2:])
        minio_client.remove_object(settings.MINIO_IMAGE_BUCKET_NAME, filename)
        print(f"Image {filename} supprimée avec succès.")
    except S3Error as e:
        print(f"Erreur lors de la suppression de l'image : {e}")
        


# def upload_video_to_minio(file, filename, content_type=None, retries=3, part_size=1 * 1024 * 1024):
#     """
#     Uploads a large video file to MinIO with retry logic and chunked uploads.

#     :param file: File to upload
#     :param filename: Name of the file on MinIO
#     :param content_type: MIME type of the file (optional)
#     :param retries: Number of retries in case of failure (default is 3)
#     :param part_size: Size of each part for chunked upload (default is 10MB)
#     :return: The URL of the uploaded file if successful, None otherwise
#     """
#     try:
#         # Génération du chemin complet pour le fichier dans MinIO
#         filename = f"videos/{filename}"

#         # Taille totale du fichier pour calculer la progression
#         file_size = file.size
#         uploaded_size = 0  # Initialisation de la taille uploadée

#         # Calcul du nombre de morceaux nécessaires
#         total_parts = (file_size // part_size) + 1
#         minio_client = Minio(
#             settings.MINIO_ENDPOINT,
#             access_key=settings.MINIO_ACCESS_KEY,
#             secret_key=settings.MINIO_SECRET_KEY,
#             secure=settings.MINIO_USE_SSL
#         )

#         # Essayez de charger le fichier en plusieurs morceaux
#         for attempt in range(retries):
#             try:
#                 # Chargement progressif en utilisant un fichier temporaire
#                 with TemporaryFile() as temp_file:
#                     for chunk in file.chunks():  # Lecture par chunks
#                         temp_file.write(chunk)
#                         uploaded_size += len(chunk)

#                         # Calcul de la progression en pourcentage
#                         progress_percentage = (uploaded_size / file_size) * 100
#                         logger.info(
#                             f"Progression de l'upload : {progress_percentage:.2f}%")

#                     temp_file.seek(0)  # remettre le pointeur au début

#                     # Upload de la vidéo par parties
#                     minio_client.put_object(
#                         bucket_name=settings.MINIO_VIDEO_BUCKET_NAME,
#                         object_name=filename,
#                         data=temp_file,
#                         length=file_size,
#                         part_size=part_size,  # Décompose en parties de 10 Mo
#                         content_type=content_type,
#                     )

#                 # Si l'upload a réussi, sortir de la boucle
#                 break

#             except S3Error as e:
#                 logger.error(
#                     f"Erreur lors de l'upload de la vidéo, tentative {attempt + 1}/{retries}: {e}")
#                 if attempt < retries - 1:
#                     logger.info(f"Nouvelle tentative dans 3 secondes...")
#                     time.sleep(3)  # Attendre un peu avant de réessayer

#         else:
#             logger.error("Échec de l'upload après plusieurs tentatives.")
#             return None

#         # URL de la vidéo une fois l'upload réussi
#         file_url = f"https://{settings.MINIO_ENDPOINT}/{settings.MINIO_VIDEO_BUCKET_NAME}/{filename}"
#         logger.info(f"Vidéo uploadée avec succès : {file_url}")
#         return file_url

#     except S3Error as e:
#         logger.error(f"Erreur lors de l'upload de la vidéo : {e}")
#         return None


def upload_video_to_minio(file, filename, content_type=None):
    try:
        # Génération du chemin complet pour le fichier dans MinIO
        filename = f"videos/{filename}"

        # Taille totale du fichier pour calculer la progression
        file_size = file.size
        uploaded_size = 0  # Initialisation de la taille uploadée

        # Upload de la vidéo directement par chunks
        minio_client.put_object(
            bucket_name=settings.MINIO_VIDEO_BUCKET_NAME,
            object_name=filename,
            data=file,  # Envoie le fichier directement
            length=file_size,  # Spécifiez la taille totale
            part_size=10 * 1024 * 1024,  # Décompose en parties de 10 Mo
            content_type=content_type,
            # Utilisation d'un callback pour suivre la progression
            #progress_callback=lambda bytes_uploaded: log_progress(bytes_uploaded, file_size)
        )

        file_url = f"https://{settings.MINIO_ENDPOINT}/{settings.MINIO_VIDEO_BUCKET_NAME}/{filename}"
        logger.info(f"Vidéo uploadée avec succès : {file_url}")
        return file_url

    except S3Error as e:
        logger.error(f"Erreur lors de l'upload de la vidéo : {e}")
        return None

def log_progress(bytes_uploaded, total_size):
    progress_percentage = (bytes_uploaded / total_size) * 100
    logger.info(f"Progression de l'upload : {progress_percentage:.2f}%")


def delete_video_from_minio(file_url):
    """Supprime une video de MinIO en utilisant son URL complète."""
    try:
        # Extraire le chemin du fichier après le bucket
        filename = '/'.join(file_url.split('/')[-2:])
        minio_client.remove_object(settings.MINIO_VIDEO_BUCKET_NAME, filename)
        print(f"video {filename} supprimée avec succès.")
    except S3Error as e:
        print(f"Erreur lors de la suppression de l'video : {e}")


def test_minio_connection():
    # Test de connexion en listant les buckets disponibles
    try:
        buckets = minio_client.list_buckets()
        print("Connexion réussie. Buckets disponibles :")
        for bucket in buckets:
            print(f"- {bucket.name}")
        return True
    except S3Error as e:
        print("Échec de la connexion :", e)
        return False


# Exécuter le test
test_minio_connection()


def upload_static_files_to_minio():
    static_root = settings.STATIC_ROOT
    bucket_name = settings.MINIO_BUCKET_STATIC

    # Créer le bucket s'il n'existe pas
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # Parcourir les fichiers dans STATIC_ROOT
    for root, dirs, files in os.walk(static_root):
        for file in files:
            file_path = os.path.join(root, file)
            # Chemin relatif pour conserver la hiérarchie
            file_name = os.path.relpath(file_path, static_root)

            # Télécharger le fichier dans le bucket
            with open(file_path, 'rb') as f:
                minio_client.put_object(
                    bucket_name,
                    file_name,
                    f,
                    length=os.path.getsize(file_path),
                    content_type="application/octet-stream"  # Ajustez selon le type de fichier
                )
            print(f"Fichier {file_name} téléchargé avec succès dans MinIO.")
            
            
def generate_presigned_url_for_upload(filename, content_type=None, expires_in_minutes=60):
    """
    Génère une URL présignée pour permettre l'upload direct d'une vidéo sur MinIO.

    :param filename: Nom du fichier à uploader
    :param content_type: MIME type du fichier (optionnel, mais non utilisé dans presigned_put_object)
    :param expires_in_minutes: Durée de validité de l'URL présignée en minutes (par défaut 60 minutes)
    :return: URL présignée pour l'upload
    """
    try:
        # Création d'un client MinIO
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )

        # Génération du chemin complet pour le fichier dans MinIO
        object_name = f"videos/{filename}"

        # Génération de l'URL présignée
        presigned_url = minio_client.presigned_put_object(
            bucket_name=settings.MINIO_VIDEO_BUCKET_NAME,
            object_name=object_name,
            expires=timedelta(minutes=expires_in_minutes)
        )

        return presigned_url

    except S3Error as e:
        raise ValueError(f"Erreur lors de la génération de l'URL présignée : {str(e)}")

import os
import uuid
from django.conf import settings
from minio import Minio
from minio.error import S3Error
from tempfile import TemporaryFile
import logging

# Configuration de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser le client MinIO
minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
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


def upload_video_to_minio(file, filename, content_type=None):
    try:
        # Génération du chemin complet pour le fichier dans MinIO
        filename = f"videos/{filename}"
        
        # Taille totale du fichier pour calculer la progression
        file_size = file.size
        uploaded_size = 0  # Initialisation de la taille uploadée

        # Chargement progressif en utilisant un fichier temporaire
        with TemporaryFile() as temp_file:
            for chunk in file.chunks():  # lecture par chunks
                temp_file.write(chunk)
                uploaded_size += len(chunk)
                
                # Calcul de la progression en pourcentage
                progress_percentage = (uploaded_size / file_size) * 100
                logger.info(f"Progression de l'upload : {progress_percentage:.2f}%")

            temp_file.seek(0)  # remettre le pointeur au début

            # Upload de la vidéo
            minio_client.put_object(
                bucket_name=settings.MINIO_VIDEO_BUCKET_NAME,
                object_name=filename,
                data=temp_file,
                length=-1,  # La taille est inconnue si on utilise -1
                part_size=10 * 1024 * 1024,  # Décompose en parties de 10 Mo
                content_type=content_type
            )

        file_url = f"https://{settings.MINIO_ENDPOINT}/{settings.MINIO_VIDEO_BUCKET_NAME}/{filename}"
        logger.info(f"Vidéo uploadée avec succès : {file_url}")
        return file_url

    except S3Error as e:
        logger.error(f"Erreur lors de l'upload de la vidéo : {e}")
        return None

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
            file_name = os.path.relpath(file_path, static_root)  # Chemin relatif pour conserver la hiérarchie

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
            
#upload_static_files_to_minio()
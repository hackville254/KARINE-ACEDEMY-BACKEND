import mimetypes
from django_quill.fields import QuillField
from django.db import models
import uuid
from django.core.exceptions import ValidationError
from .minio_utils import delete_image_from_minio, delete_video_from_minio, upload_image_to_minio, upload_video_to_minio
from django.contrib.auth.models import User

def validate_video_file(value):
    """Valide que le fichier téléchargé est bien une vidéo"""
    valid_video_extensions = ['mp4', 'avi', 'mov', 'mkv']
    ext = value.name.split('.')[-1].lower()

    # Vérification de l'extension du fichier
    if ext not in valid_video_extensions:
        raise ValidationError(
            f"Le fichier doit être une vidéo. Formats valides : {', '.join(valid_video_extensions)}.")


class Formation(models.Model):
    title = models.CharField(
        max_length=255, verbose_name="Titre de la formation")
    description = models.CharField(
        max_length=50, verbose_name="Mini description de la formation")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix")
    promo_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix promotionnel")
    promo_duration = models.DateTimeField(
        verbose_name="Durée de la promotion", blank=True, null=True)
    # Champs FileField pour l'image
    image = models.ImageField(
        upload_to="images/", blank=True, verbose_name="Image de présentation")
    image_url = models.URLField(
        max_length=500, blank=True, verbose_name="URL de l'image de présentation")
    content = models.TextField(verbose_name="Contenu de la formation")

    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(
        auto_now=True, verbose_name="Date de mise à jour")

    def save(self, *args, **kwargs):


        # Téléverser la nouvelle image si elle est présente
        if self.image:
                    # Supprimer l'ancienne image si une nouvelle image est fournie
            if self.image_url:
                delete_image_from_minio(self.image_url)
            ext = self.image.name.split('.')[-1].lower()
            filename = f"{self.title}_{uuid.uuid4()}.{ext}"
            self.image_url = upload_image_to_minio(self.image.file, filename)
            self.image = None  # Efface le fichier temporaire après l'upload

        super(Formation, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Supprimer l'image de MinIO lors de la suppression de l'objet
        if self.image_url:
            delete_image_from_minio(self.image_url)
        super(Formation, self).delete(*args, **kwargs)

    def __str__(self):
        return self.title


class VideoFormation(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre de la vidéo")
    video_file = models.FileField(
        upload_to="videos/", blank=True, verbose_name="Fichier vidéo", validators=[validate_video_file])
    video_url = models.URLField(
        max_length=500, blank=True, verbose_name="URL du fichier vidéo")
    formation = models.ForeignKey(
        'Formation', related_name='videos', on_delete=models.CASCADE)
    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(
        auto_now=True, verbose_name="Date de mise à jour")

    def save(self, *args, **kwargs):


        # Vérifier si un fichier vidéo est uploadé
        if self.video_file:
            # Supprimer l'ancienne vidéo si une nouvelle est fournie
            if self.video_url:
                delete_video_from_minio(self.video_url)
            # Valider l'extension du fichier vidéo
            ext = self.video_file.name.split('.')[-1].lower()
            valid_video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'flv']
            if ext not in valid_video_extensions:
                raise ValidationError("Le fichier n'est pas un format vidéo valide.")

            # Générer un nom de fichier unique
            filename = f"{self.title}_{uuid.uuid4()}.{ext}"

            # Obtenir le type MIME du fichier
            content_type, _ = mimetypes.guess_type(self.video_file.name)
            if content_type is None:
                raise ValidationError("Impossible de déterminer le type de contenu du fichier.")

            # Upload de la vidéo vers MinIO et récupérer l'URL
            uploaded_url = upload_video_to_minio(self.video_file, filename, content_type)
            if uploaded_url:
                self.video_url = uploaded_url
            else:
                raise ValidationError("Échec du téléchargement de la vidéo vers MinIO.")

            # Effacer le fichier temporaire après l'upload
            self.video_file = None

        # Sauvegarder l'instance
        super(VideoFormation, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class UserFormationPurchase(models.Model):  # Nouveau nom de classe
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_formations')
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='purchased_by_users')
    achat_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} a acheté {self.formation.title}"

    class Meta:
        verbose_name = 'Formation Acheter'
        verbose_name_plural = 'Formation Acheter'
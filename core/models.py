import mimetypes
import re
from django_quill.fields import QuillField
from django.db import models
import uuid
from django.core.exceptions import ValidationError
from .minio_utils import delete_image_from_minio, delete_video_from_minio, upload_image_to_minio, upload_video_to_minio
from django.contrib.auth.models import User
from urllib.parse import quote

# Ajouter manuellement le type MIME pour .m4v
mimetypes.add_type('video/x-m4v', '.m4v')


def validate_video_file(value):
    """Valide que le fichier téléchargé est bien une vidéo"""
    valid_video_extensions = [
        'mp4', 'avi', 'mov', 'mkv', 'm4v',  # Formats de base
        'wmv',  # Windows Media Video
        'flv',  # Flash Video
        'webm',  # WebM Video
        'mpeg',  # MPEG Video
        'mpg',  # MPEG Video
        '3gp',  # 3GPP Video
        '3g2',  # 3GPP2 Video
        'divx',  # DivX Video
        'xvid',  # Xvid Video
        'vob',  # Video Object
        'rm',  # RealMedia
        'rmvb',  # RealMedia Variable Bitrate
        'f4v',  # Flash MP4 Video
        'ts',  # MPEG Transport Stream
        'm2ts',  # MPEG-2 Transport Stream
        'svi',  # Samsung Video Interchange
        'drc',  # Dynamic Adaptive Streaming over HTTP
        'mjpeg',  # Motion JPEG
        'asf',  # Advanced Streaming Format
        'h264',  # H.264 Video
        'h265',  # H.265 Video (HEVC)
        'mp2',  # MPEG-2 Video
        'mpv',  # MPEG Video
        'nsv',  # Nullsoft Streaming Video
        'ogv',  # Ogg Video
        'm4p',  # MPEG-4 Video (Protected)
    ]
    ext = value.name.split('.')[-1].lower()

    # Vérification de l'extension du fichier
    if ext not in valid_video_extensions:
        raise ValidationError(
            f"Le fichier doit être une vidéo. Formats valides : {', '.join(valid_video_extensions)}.")


class Formation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        max_length=500, blank=True, null=True, verbose_name="URL de l'image de présentation")
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
            # Remplacer les espaces dans le titre par des underscores pour éviter les problèmes d'URL
            safe_title = self.title.replace(" ", "_")

            # Générer un nom de fichier unique avec un UUID
            filename = f"{safe_title}_{uuid.uuid4()}.{ext}"
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Titre de la vidéo")
    ordre = models.IntegerField(
        ("Ordre d'affichage de la formation"), default=1)
    video_file = models.FileField(
        upload_to="videos/", blank=True, null=True, verbose_name="Fichier vidéo", validators=[validate_video_file])
    video_url = models.URLField(
        max_length=500, blank=True, null=True, verbose_name="URL du fichier vidéo")
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
            # valid_video_extensions = ['mp4', 'avi', 'mov', 'mkv', 'flv']
            # if ext not in valid_video_extensions:
            #     raise ValidationError(
            #         "Le fichier n'est pas un format vidéo valide.")

            # Générer un nom de fichier unique
            # Nettoyer et générer un nom de fichier unique
            # Supprime les caractères spéciaux
            filename_base = re.sub(r'[^a-zA-Z0-9\s]', '', self.title)
            # Remplace les espaces par des tirets
            filename_base = filename_base.replace(' ', '-')
            filename_base = filename_base.lower()                    # Convertir en minuscules

            # Ajouter un UUID unique pour garantir l'unicité du fichier
            filename = f"{filename_base}_{uuid.uuid4()}.{ext}"

            # Encoder le nom du fichier pour l'URL
            filename = quote(filename)             # Convertir en minuscules
            # Obtenir le type MIME du fichier
            content_type, _ = mimetypes.guess_type(self.video_file.name)
            if content_type is None:
                raise ValidationError(
                    "Impossible de déterminer le type de contenu du fichier.")

            # Upload de la vidéo vers MinIO et récupérer l'URL
            uploaded_url = upload_video_to_minio(
                self.video_file, filename, content_type)
            if uploaded_url:
                self.video_url = uploaded_url
            else:
                raise ValidationError(
                    "Échec du téléchargement de la vidéo vers MinIO.")

            # Effacer le fichier temporaire après l'upload
            self.video_file = None

        # Sauvegarder l'instance
        super(VideoFormation, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserFormationPurchase(models.Model):  # Nouveau nom de classe
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='purchased_formations')
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, related_name='purchased_by_users')
    achat_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} a acheté {self.formation.title}"

    class Meta:
        verbose_name = 'Formation Acheter'
        verbose_name_plural = 'Formation Acheter'


# Classe pour les paiements

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)
    montant = models.FloatField()  # Montant
    devise_client = models.CharField(max_length=10)  # Devise
    status = models.CharField(
        max_length=20, default="initialiser")  # Statut de paiement
    name = models.CharField(max_length=255)  # Nom de l'utilisateur
    country = models.CharField(
        max_length=255, blank=True, null=True)  # Pays de l'utilisateur
    mobile_number = models.CharField(
        max_length=20, blank=True, null=True)  # Numéro Mobile Money
    email = models.EmailField(blank=True, null=True)  # E-mail de l'utilisateur
    otp = models.CharField(max_length=6, blank=True, null=True)  # Code OTP
    orderId = models.CharField(max_length=10)  # Code OTP
    operator = models.CharField(
        max_length=50, blank=True, null=True)  # Opérateur Mobile Money
    created_at = models.DateTimeField(auto_now_add=True)  # Date de création
    updated_at = models.DateTimeField(auto_now=True)  # Date de mise à jour

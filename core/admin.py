from django.contrib import admin
from .models import Formation, UserFormationPurchase, VideoFormation

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    # Champs affichés dans la liste admin
    list_display = ('title', 'price', 'promo_price', 'promo_duration', 'created', 'updated')
    # Champs par lesquels l'admin peut trier les objets
    ordering = ('created', 'updated', 'price')
    # Champs permettant la recherche
    search_fields = ('title',)
    # Ajout de filtres pour la date de création et la date de mise à jour
    list_filter = ('created', 'updated')

@admin.register(VideoFormation)
class VideoFormationAdmin(admin.ModelAdmin):
    # Champs affichés dans la liste admin
    list_display = ('title', 'formation', 'created', 'updated')
    # Champs par lesquels l'admin peut trier les objets
    ordering = ('created', 'updated')
    # Champs permettant la recherche
    search_fields = ('title', 'formation__title')
    # Ajout de filtres pour la formation associée
    list_filter = ('formation', 'created', 'updated')


# Personnalisation de l'affichage du modèle UserFormationPurchase dans l'admin
class UserFormationPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'formation', 'achat_date')  # Colonnes à afficher dans la liste
    list_filter = ('user', 'formation')  # Filtres disponibles dans la barre latérale
    search_fields = ('user__username', 'formation__title')  # Champs de recherche
    ordering = ('-achat_date',)  # Trier par date d'achat, du plus récent au plus ancien
    date_hierarchy = 'achat_date'  # Permet d'ajouter une hiérarchie de date (par mois, année...)

# Enregistrer le modèle UserFormationPurchase dans l'admin
admin.site.register(UserFormationPurchase, UserFormationPurchaseAdmin)
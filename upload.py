import os
import requests
from urllib.parse import quote_plus
import logging

# Exemple de configuration dynamique
# Peut être défini dans la config de l'application
bucket_name = "karine-academy-bucket-karine"
logging.basicConfig(level=logging.DEBUG)

# Extraire le nom du fichier à partir du chemin local
file_path = "./A1-INTRO DE LA CRYPTO SIMPLEMENT.mp4"
filename = "a1intro-de-la-crypto-simplement_274773d9-158b-4009-91bf-7ff9dddb2b5e.mp4"
# Générer un nom d'objet basé sur le répertoire et le nom du fichier
object_name = f"media/videos/{quote_plus(os.path.basename(filename))}"

# URL présignée pour l'upload
presigned_url = "https://karine-academy-bucket-karine.hegely.easypanel.host/media/videos/a1intro-de-la-crypto-simplement_e4a3667b-d269-417a-a2ec-57d9bef622b4.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=O8xlRP5wdXGKp3GmtL0j%2F20241117%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241117T113330Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=4e95cdc52533586319c1c1c9acb2a2cdb29a270e003384b3a6069a86fbb972eb"


def upload_file(presigned_url, file_path):
    # Ouverture du fichier à uploader
    with open(file_path, 'rb') as f:
        # Lire le contenu entier du fichier
        file_data = f.read()

        # Effectuer la requête PUT pour envoyer le fichier entier
        response = requests.put(presigned_url, data=file_data, headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(len(file_data))
        }
        )

        if response.status_code == 200:
            print("Téléchargement terminé avec succès.")
        else:
            print(
                f"Erreur lors de l'upload : {response.status_code} - {response.text}")

    # Construction de l'URL du fichier une fois l'upload terminé
    file_url = f"https://karine-academy-bucket-karine.hegely.easypanel.host/{object_name}"

    return file_url


# Lancer l'upload du fichier
file_url = upload_file(presigned_url, file_path)

# Afficher l'URL du fichier
print("URL du fichier téléchargé:", file_url)

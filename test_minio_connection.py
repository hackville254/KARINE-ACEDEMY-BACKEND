from minio import Minio
from minio.error import S3Error

def test_minio_connection():
    # Configuration de connexion MinIO
    minio_client = Minio(
        endpoint="karine-academy-bucket-karine.hegely.easypanel.host",
        access_key="O8xlRP5wdXGKp3GmtL0j",
        secret_key="ynz3HrJKTWwrBpfog5wwoVi31sZsHinNPVc86tGQ",
        secure=True
    )

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

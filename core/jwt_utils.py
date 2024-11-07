import jwt
from datetime import datetime, timedelta
from django.conf import settings
from jwt import ExpiredSignatureError, InvalidTokenError

# Configuration pour le JWT
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION = timedelta(hours=1)  # Durée de validité du token d'accès

# Fonction pour créer un token JWT
def create_token(data: dict) -> str:
    payload = {
        **data,
        "exp": datetime.utcnow() + ACCESS_TOKEN_EXPIRATION,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Fonction pour vérifier et décoder un token JWT
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise ExpiredSignatureError("Le token a expiré")
    except InvalidTokenError:
        raise InvalidTokenError("Token invalide")

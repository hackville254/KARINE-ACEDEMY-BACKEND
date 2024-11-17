from uuid import UUID
from ninja import Field, Schema
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

class RegisterSchema(Schema):
    username: str
    email: EmailStr
    password: str

class LoginSchema(Schema):
    email: EmailStr
    password: str

class TokenResponse(Schema):
    access_token: str
    token_type: str = "bearer"

class FormationSchema(Schema):
    id:UUID
    title: str
    price: str
    lessons: str  # Leçons (nombre de vidéos)
    description: str
    image: str  
    
    
class ModuleSchema(Schema):
    content: str

class FormationResponseSchema(Schema):
    id:UUID
    title: str
    price: str
    promoPrice: str
    promoDuration: float | None = None  # Optional
    imageUrl: str
    modules: list[ModuleSchema]
    
class FormationDetailSchema(Schema):
    id:UUID
    title: str
    image_url: str
    
    
    
class PaymentSchema(BaseModel):
    formation_id: UUID  # Identifiant de la formation acheter
    name: str  # Nom de l'utilisateur
    email: Optional[EmailStr] = Field(default=None)
    country: Optional[str] = Field(default=None, description="Pays de l'utilisateur")
    mobile_number: Optional[str]
    otp: Optional[str] = Field(default=None)
    orderId: str  # ID de commande (generer sur le front-end)
    operator: int # Identifiant de l'operateur
    montant: float  # Montant
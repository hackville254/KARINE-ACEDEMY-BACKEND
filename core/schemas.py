from ninja import Schema
from pydantic import EmailStr, HttpUrl
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
    id:int
    title: str
    price: str
    lessons: str  # Leçons (nombre de vidéos)
    description: str
    image: str  
    
    
class ModuleSchema(Schema):
    content: str

class FormationResponseSchema(Schema):
    title: str
    price: str
    promoPrice: str
    promoDuration: float | None = None  # Optional
    imageUrl: str
    modules: list[ModuleSchema]
    
class FormationDetailSchema(Schema):
    id:int
    title: str
    image_url: str
from ninja import NinjaAPI
from core.views import router as Karine
api = NinjaAPI()

api.add_router("/" , Karine , tags=["KARINE ACADEMY"])
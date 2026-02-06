from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import settings

client = AsyncIOMotorClient(settings.MONGO_URI, server_api=ServerApi('1'))
db = client[settings.MONGO_DB_NAME]

async def init_db():
    # Create indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.predictions.create_index("patient_id")
    await db.predictions.create_index("consultation_id")
    await db.models.create_index("is_production")
    await db.datasets.create_index("uploaded_by")

def get_db():
    return db
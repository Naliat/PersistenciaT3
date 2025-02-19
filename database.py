from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import os

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
engine = AIOEngine(client=client, database="farmacia_db")

def get_engine():
    return engine
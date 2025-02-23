import os
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from dotenv import load_dotenv

# Carregar as variáveis do .env (certifique-se que o .env está na raiz)
load_dotenv() 

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("A variável MONGODB_URI não está definida no .env")

client = AsyncIOMotorClient(MONGODB_URI)
engine = AIOEngine(client=client, database="farmacia_db")

def get_engine():
    return engine

async def aggregate(pipeline, collection_name):
    db = client["farmacia_db"]
    cursor = db[collection_name].aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result
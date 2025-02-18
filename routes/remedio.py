# routes/remedio.py
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from models.remedio import Remedio

# Conexão com MongoDB
uri = "mongodb+srv://tailanoliveira584:1412@cluster0.mjmek.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["meubanco"]
collection = db["remedios"]

router = APIRouter()

@router.post("/remedios/")
async def create_remedio(remedio: Remedio):
    remedio_dict = remedio.dict()
    result = collection.insert_one(remedio_dict)
    if result.inserted_id:
        return {"id": str(result.inserted_id)}
    raise HTTPException(status_code=400, detail="Erro ao criar o remédio")

@router.get("/remedios/")
async def read_remedios():
    remedios = list(collection.find({}, {"_id": 0}))
    return {"remedios": remedios}

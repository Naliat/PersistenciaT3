# models/remedio.py
from pydantic import BaseModel

class Remedio(BaseModel):
    name: str
    description: str
    price: float

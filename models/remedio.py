from bson import ObjectId  # Importe ObjectId do módulo bson
from odmantic import Model, Field
from datetime import datetime

class Remedio(Model):
    nome: str
    descricao: str
    preco: float = Field(gt=0)
    validade: datetime
    fornecedor_id: ObjectId  # Use ObjectId em vez de str
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "remedios"}
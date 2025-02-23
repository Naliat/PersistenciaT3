from bson import ObjectId
from odmantic import Model, Field, Reference
from datetime import datetime
from .fornecedor import Fornecedor  # Importe o modelo Fornecedor

class Remedio(Model):
    nome: str
    descricao: str
    preco: float = Field(gt=0)
    validade: datetime
    fornecedor: Fornecedor = Reference()  # Referência ao modelo Fornecedor
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "remedios"}
from odmantic import Model, Reference, Field
from datetime import datetime, date
from .fornecedor import Fornecedor

class Remedio(Model):
    nome: str
    descricao: str
    preco: float = Field(gt=0)
    validade: date
    fornecedor: Fornecedor = Reference()
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "remedios"}

from odmantic import Model, Reference
from datetime import date, datetime
from pydantic import Field
from typing import ClassVar
from models.fornecedor import Fornecedor

class Remedio(Model):
    nome: str
    descricao: str
    preco: float = Field(gt=0)
    validade: date
    fornecedor: Fornecedor = Reference()
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection: ClassVar[str] = "remedios"
        indexes: ClassVar[list] = [
            ("nome", "text"),
            ("validade",),
            ("fornecedor",)
        ]
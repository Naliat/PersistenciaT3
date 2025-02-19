from odmantic import Model, Reference
from datetime import datetime
from typing import ClassVar
from models.remedio import Remedio
from odmantic import Field

class Estoque(Model):
    remedio: Remedio = Reference()
    quantidade: int = Field(gt=0)
    data_entrada: datetime = Field(default_factory=datetime.utcnow)
    validade: datetime
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection: ClassVar[str] = "estoques"
        indexes: ClassVar[list] = [
            ("remedio",),
            ("validade",),
            ("data_entrada", "validade")
        ]
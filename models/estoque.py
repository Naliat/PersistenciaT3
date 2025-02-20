from odmantic import Model, Reference, Field
from datetime import datetime
from .remedio import Remedio

class Estoque(Model):
    remedio: Remedio = Reference()
    quantidade: int = Field(gt=0)
    data_entrada: datetime = Field(default_factory=datetime.utcnow)
    validade: datetime
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "estoques"}

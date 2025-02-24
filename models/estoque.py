from odmantic import Model, Reference, Field
from datetime import datetime, timezone
from .remedio import Remedio

class Estoque(Model):
    remedio: Remedio = Reference()  # Referência para o modelo Remedio
    quantidade: int = Field(gt=0)
    data_entrada: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validade: datetime
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"collection": "estoques"}

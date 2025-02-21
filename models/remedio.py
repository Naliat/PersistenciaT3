from odmantic import Model, Field
from datetime import datetime, date

class Remedio(Model):
    nome: str
    descricao: str
    preco: float = Field(gt=0)
    validade: date
    fornecedor_id: str  # Apenas o ID do fornecedor
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "remedios"}

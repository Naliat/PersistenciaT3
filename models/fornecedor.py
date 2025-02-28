from odmantic import Model, Field
from datetime import datetime

class Fornecedor(Model):
    nome: str
    cnpj: str = Field(unique=True)
    telefone: str
    endereco: str
    criado_em: datetime = Field(default_factory=datetime)
    atualizado_em: datetime = Field(default_factory=datetime)

    model_config = {"collection": "fornecedores"}

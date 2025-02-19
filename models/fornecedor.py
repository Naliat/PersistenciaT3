from odmantic import Model, Field
from pydantic import validator
from typing import Optional, ClassVar
from datetime import datetime

class Fornecedor(Model):
    nome: str
    cnpj: str = Field(unique=True)
    telefone: str
    endereco: str
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    # Configurações do ODMantic
    class Config:
        collection: ClassVar[str] = "fornecedores"
        indexes: ClassVar[list] = [
            ("nome", "text"),
            ("cnpj",)
        ]

    @validator('cnpj')
    def validar_cnpj(cls, v):
        if len(v) != 14 or not v.isdigit():
            raise ValueError("CNPJ deve conter 14 dígitos numéricos")
        return v
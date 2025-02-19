from fastapi import APIRouter, HTTPException, Query
from models.fornecedor import Fornecedor
from odmantic import ObjectId
from database import engine
from typing import Optional

router = APIRouter(
    prefix="/fornecedores",
    tags=["Fornecedores"]
)

@router.get("/", response_model=dict)
async def listar_fornecedores(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    nome: Optional[str] = Query(None),
    cnpj: Optional[str] = Query(None)
):
    skip = (pagina - 1) * limite
    query = {}
    
    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}
    if cnpj:
        query["cnpj"] = cnpj

    total = await engine.count(Fornecedor, query)
    fornecedores = await engine.find(
        Fornecedor,
        query,
        skip=skip,
        limit=limite,
        sort=Fornecedor.nome
    )

    return {
        "data": fornecedores,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }
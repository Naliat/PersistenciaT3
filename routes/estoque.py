from fastapi import APIRouter, Query
from models.estoque import Estoque
from database import engine
from datetime import datetime
from typing import Optional

router = APIRouter(
    prefix="/estoque",
    tags=["Estoque"]
)

@router.get("/", response_model=dict)
async def listar_estoque(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    quantidade_min: Optional[int] = Query(None, ge=0),
    ano_validade: Optional[int] = Query(None),
    mes_validade: Optional[int] = Query(None, ge=1, le=12)
):
    skip = (pagina - 1) * limite
    query = {}
    
    if quantidade_min:
        query["quantidade"] = {"$gte": quantidade_min}

    total = await engine.count(Estoque, query)
    itens = await engine.find(
        Estoque,
        query,
        skip=skip,
        limit=limite,
        sort=Estoque.validade
    )

    return {
        "data": itens,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

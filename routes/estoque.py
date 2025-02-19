from fastapi import APIRouter, HTTPException, Query
from models.estoque import Estoque
from models.remedio import Remedio
from odmantic import ObjectId
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
    remedio_id: Optional[ObjectId] = Query(None),
    quantidade_min: Optional[int] = Query(None, ge=0),
    ano_validade: Optional[int] = Query(None),
    mes_validade: Optional[int] = Query(None, ge=1, le=12)
):
    skip = (pagina - 1) * limite
    query = {}
    
    if remedio_id:
        query["remedio"] = remedio_id
    if quantidade_min:
        query["quantidade"] = {"$gte": quantidade_min}
    
    # Filtro por data usando operadores do MongoDB
    date_query = {}
    if ano_validade:
        date_query["year"] = ano_validade
    if mes_validade:
        date_query["month"] = mes_validade
    
    if date_query:
        query["validade"] = {
            "$expr": {"$and": [
                {f"${k}": {"$eq": v}} for k, v in date_query.items()
            ]}
        }

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

@router.get("/validade", response_model=dict)
async def estoque_por_validade(
    data_inicio: datetime = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: datetime = Query(..., description="Data final (YYYY-MM-DD)"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    skip = (pagina - 1) * limite
    query = {
        "validade": {
            "$gte": data_inicio,
            "$lte": data_fim
        }
    }

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
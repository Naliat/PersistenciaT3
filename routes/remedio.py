from fastapi import APIRouter, HTTPException, Query
from models.remedio import Remedio
from models.fornecedor import Fornecedor
from odmantic import ObjectId
from database import engine
from datetime import date, timedelta, datetime, timezone
from typing import Optional

router = APIRouter(
    prefix="/remedios",
    tags=["Remédios"]
)

@router.get("/", response_model=dict)
async def listar_remedios(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    nome: Optional[str] = Query(None),
    fornecedor_id: Optional[ObjectId] = Query(None),
    preco_min: Optional[float] = Query(None, ge=0),
    preco_max: Optional[float] = Query(None, ge=0),
    validade_inicio: Optional[date] = Query(None),
    validade_fim: Optional[date] = Query(None)
):
    skip = (pagina - 1) * limite
    query = {}
    
    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}
    if fornecedor_id:
        query["fornecedor"] = fornecedor_id
    if preco_min or preco_max:
        query["preco"] = {}
        if preco_min:
            query["preco"]["$gte"] = preco_min
        if preco_max:
            query["preco"]["$lte"] = preco_max
    if validade_inicio and validade_fim:
        query["validade"] = {
            "$gte": validade_inicio,
            "$lte": validade_fim
        }

    total = await engine.count(Remedio, query)
    remedios = await engine.find(
        Remedio,
        query,
        skip=skip,
        limit=limite,
        sort=Remedio.nome
    )

    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/validade/proxima", response_model=dict)
async def remedios_proxima_validade(
    dias: int = Query(7, ge=1, description="Dias a partir de hoje"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    skip = (pagina - 1) * limite
    hoje = datetime.now(timezone.utc).date()
    data_limite = hoje + timedelta(days=dias)
    
    query = {
        "validade": {
            "$gte": hoje,
            "$lte": data_limite
        }
    }

    total = await engine.count(Remedio, query)
    remedios = await engine.find(
        Remedio,
        query,
        skip=skip,
        limit=limite,
        sort=Remedio.validade
    )

    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

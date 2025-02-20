from fastapi import APIRouter, Query
from models.remedio import Remedio
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
    validade_inicio: Optional[date] = Query(None),
    validade_fim: Optional[date] = Query(None)
):
    skip = (pagina - 1) * limite
    query = {}
    
    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}
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
        sort=Remedio.validade
    )

    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

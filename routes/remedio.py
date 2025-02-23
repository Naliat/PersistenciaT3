import logging
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Path
from models.remedio import Remedio
from models.fornecedor import Fornecedor
from database import engine, aggregate
from typing import Optional
from datetime import date, datetime, timezone

logger = logging.getLogger("remedios")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(
    prefix="/remedios",
    tags=["Remédios"]
)

# CREATE: Criar um novo remédio
@router.post("/", response_model=Remedio, status_code=201)
async def criar_remedio(remedio: Remedio):
    logger.info("Iniciando criação do remédio: %s", remedio.nome)

    # Verifica se o fornecedor existe
    fornecedor = await engine.find_one(Fornecedor, Fornecedor.id == remedio.fornecedor.id)
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado para o remédio: %s", remedio.fornecedor.id, remedio.nome)
        raise HTTPException(status_code=400, detail="Fornecedor não encontrado.")

    # Salva o remédio no banco de dados
    novo_remedio = await engine.save(remedio)
    logger.info("Remédio criado com ID: %s", novo_remedio.id)
    return novo_remedio

# READ: Listar remédios com filtros (paginação)
@router.get("/", response_model=dict)
async def listar_remedios(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    nome: Optional[str] = Query(None),
    validade_inicio: Optional[date] = Query(None),
    validade_fim: Optional[date] = Query(None)
):
    logger.info("Listando remédios - Página: %s, Limite: %s", pagina, limite)
    skip = (pagina - 1) * limite
    query = {}

    # Filtro por nome
    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}

    # Filtro por validade
    if validade_inicio and validade_fim:
        try:
            validade_inicio_dt = datetime.combine(validade_inicio, datetime.min.time())
            validade_fim_dt = datetime.combine(validade_fim, datetime.max.time())
            query["validade"] = {"$gte": validade_inicio_dt, "$lte": validade_fim_dt}
        except Exception as e:
            logger.error("Erro ao processar datas de validade: %s", str(e))
            raise HTTPException(status_code=400, detail="Datas de validade inválidas")

    # Consulta ao banco de dados
    try:
        total = await engine.count(Remedio, query)
        remedios = await engine.find(Remedio, query, skip=skip, limit=limite, sort=Remedio.validade)
    except Exception as e:
        logger.error("Erro ao consultar o banco de dados: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao listar remédios")

    logger.info("Remédios listados: %s itens encontrados", total)
    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/contagem", response_model=dict)
async def contar_remedios():
    total = await engine.count(Remedio, {})
    logger.info("Contagem total de remédios: %s", total)
    return {"total_remedios": total}

# READ: Obter remédio por ID
@router.get("/{remedio_id}", response_model=Remedio)
async def obter_remedio_por_id(
    remedio_id: str = Path(..., description="ID do remédio")
):
    logger.info("Obtendo remédio por ID: %s", remedio_id)

    try:
        remedio_id = ObjectId(remedio_id)
    except Exception as e:
        logger.error("ID do remédio inválido: %s", remedio_id)
        raise HTTPException(status_code=400, detail="ID do remédio inválido")
    
    remedio = await engine.find_one(Remedio, {"_id": remedio_id})
    if not remedio:
        logger.error("Remédio com ID %s não encontrado", remedio_id)
        raise HTTPException(status_code=404, detail="Remédio não encontrado")
    
    logger.info("Remédio com ID %s obtido com sucesso", remedio_id)
    return remedio

# UPDATE: Atualizar um remédio existente
@router.put("/{remedio_id}", response_model=Remedio)
async def atualizar_remedio(
    remedio_id: str = Path(..., description="ID do remédio a ser atualizado"),
    remedio_update: Remedio = None
):
    logger.info("Atualizando remédio com ID: %s", remedio_id)

    try:
        remedio_id = ObjectId(remedio_id)
    except Exception as e:
        logger.error("ID do remédio inválido: %s", remedio_id)
        raise HTTPException(status_code=400, detail="ID do remédio inválido")
    
    remedio_existente = await engine.find_one(Remedio, Remedio.id == remedio_id)
    if not remedio_existente:
        logger.error("Remédio com ID %s não encontrado para atualização", remedio_id)
        raise HTTPException(status_code=404, detail="Remédio não encontrado")
    
    update_data = remedio_update.dict(exclude_unset=True)

    update_data.pop("id", None)

    for key, value in update_data.items():
        setattr(remedio_existente, key, value)
        
    remedio_existente.atualizado_em = datetime.utcnow()

    updated_remedio = await engine.save(remedio_existente)

    return updated_remedio

# DELETE: Remover um remédio
@router.delete("/{remedio_id}", response_model=dict)
async def deletar_remedio(
    remedio_id: str = Path(..., description="ID do remédio a ser deletado")
):
    
    try:
        remedio_id = ObjectId(remedio_id)
    except Exception as e:
        logger.error("ID do remédio inválido: %s", remedio_id)
        raise HTTPException(status_code=400, detail="ID do remédio inválido")

    logger.info("Deletando remédio com ID: %s", remedio_id)

    remedio = await engine.find_one(Remedio, {"_id": remedio_id})
    if not remedio:
        logger.error("Remédio com ID %s não encontrado para deleção", remedio_id)
        raise HTTPException(status_code=404, detail="Remédio não encontrado")
    
    await engine.delete(remedio)
    logger.info("Remédio com ID %s deletado com sucesso", remedio_id)
    return {"message": "Remédio deletado com sucesso"}

# ----------------- Endpoints de Busca (GET) -----------------

@router.get("/fornecedor/{fornecedor_id}", response_model=dict)
async def listar_remedios_por_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    logger.info("Listando remédios do fornecedor ID: %s", fornecedor_id)
    try:
        fornecedor_id = ObjectId(fornecedor_id)
    except Exception as e:
        logger.error("ID do fornecedor inválido: %s", fornecedor_id)
        raise HTTPException(status_code=400, detail="ID do fornecedor inválido")
    
    skip = (pagina - 1) * limite
    query = {"fornecedor.id": fornecedor_id}  # Ajuste aqui
    total = await engine.count(Remedio, query)
    remedios = await engine.find(Remedio, query, skip=skip, limit=limite, sort=Remedio.nome)
    logger.info("Remédios encontrados para fornecedor %s: %s", fornecedor_id, total)
    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/buscar/preco/maior", response_model=dict)
async def buscar_remedios_preco_maior(
    preco: float = Query(..., description="Preço mínimo")
):
    logger.info("Buscando remédios com preço maior que: %s", preco)
    query = {"preco": {"$gt": preco}}
    remedios = await engine.find(Remedio, query, sort=Remedio.preco)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/preco/menor", response_model=dict)
async def buscar_remedios_preco_menor(
    preco: float = Query(..., description="Preço máximo")
):
    logger.info("Buscando remédios com preço menor que: %s", preco)
    query = {"preco": {"$lte": preco}}
    remedios = await engine.find(Remedio, query, sort=Remedio.preco)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/criados", response_model=dict)
async def buscar_remedios_criados(
    inicio: datetime = Query(..., description="Data inicial (YYYY-MM-DDTHH:MM:SS)"),
    fim: datetime = Query(..., description="Data final (YYYY-MM-DDTHH:MM:SS)")
):
    logger.info("Buscando remédios criados entre %s e %s", inicio, fim)
    query = {"criado_em": {"$gte": inicio, "$lte": fim}}
    remedios = await engine.find(Remedio, query, sort=Remedio.criado_em)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/prefixo", response_model=dict)
async def buscar_remedios_por_prefixo(
    prefixo: str = Query(..., description="Prefixo do nome do remédio")
):
    logger.info("Buscando remédios cujo nome inicia com: %s", prefixo)
    query = {"nome": {"$regex": f"^{prefixo}", "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/sufixo", response_model=dict)
async def buscar_remedios_por_sufixo(
    sufixo: str = Query(..., description="Sufixo do nome do remédio")
):
    logger.info("Buscando remédios cujo nome termina com: %s", sufixo)
    query = {"nome": {"$regex": f"{sufixo}$", "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/descricao", response_model=dict)
async def buscar_remedios_por_descricao(
    descricao: str = Query(..., description="Parte da descrição do remédio")
):
    logger.info("Buscando remédios com descrição contendo: %s", descricao)
    query = {"descricao": {"$regex": descricao, "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

# ----------------- Endpoints de Busca Agregada (GET) -----------------

# Agregação: Quantidade de remédios por fornecedor
@router.get("/agregar/quantidade-por-fornecedor", response_model=dict)
async def quantidade_remedios_por_fornecedor():
    logger.info("Agregando quantidade de remédios por fornecedor")
    
    pipeline = [
        {
            "$group": {
                "_id": "$fornecedor_id",
                "total_remedios": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "fornecedor",
                "localField": "_id",
                "foreignField": "_id",
                "as": "fornecedor"
            }
        },
        {
            "$unwind": "$fornecedor"
        },
        {
            "$project": {
                "fornecedor_nome": "$fornecedor.nome",
                "total_remedios": 1
            }
        }
    ]
    
    try:
        result = await aggregate(pipeline, Remedio.__collection__)
        logger.info("Agregação concluída")
        return {"data": result}
    except Exception as e:
        logger.error(f"Erro durante a agregação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante a agregação: {str(e)}")


# Agregação: Média de preço dos remédios por fornecedor
@router.get("/agregar/media-preco-por-fornecedor", response_model=dict)
async def media_preco_remedios_por_fornecedor():
    logger.info("Calculando média de preço dos remédios por fornecedor")
    
    pipeline = [
        {
            "$group": {
                "_id": "$fornecedor_id",
                "media_preco": {"$avg": "$preco"}
            }
        },
        {
            "$lookup": {
                "from": "fornecedor",
                "localField": "_id",
                "foreignField": "_id",
                "as": "fornecedor"
            }
        },
        {
            "$unwind": "$fornecedor"
        },
        {
            "$project": {
                "fornecedor_nome": "$fornecedor.nome",
                "media_preco": 1
            }
        }
    ]
    
    try:
        result = await aggregate(pipeline, Remedio.__collection__)
        logger.info("Agregação concluída")
        return {"data": result}
    except Exception as e:
        logger.error(f"Erro durante a agregação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante a agregação: {str(e)}")

# Agregação: Remédio mais caro por fornecedor
@router.get("/agregar/remedio-mais-caro-por-fornecedor", response_model=dict)
async def remedio_mais_caro_por_fornecedor():
    logger.info("Buscando remédio mais caro por fornecedor")
    
    pipeline = [
        {
            "$sort": {"preco": -1}
        },
        {
            "$group": {
                "_id": "$fornecedor_id",
                "remedio_mais_caro": {"$first": "$$ROOT"}
            }
        },
        {
            "$lookup": {
                "from": "fornecedor",
                "localField": "_id",
                "foreignField": "_id",
                "as": "fornecedor"
            }
        },
        {
            "$unwind": "$fornecedor"
        },
        {
            "$project": {
                "fornecedor_nome": "$fornecedor.nome",
                "remedio_mais_caro": {
                    "nome": "$remedio_mais_caro.nome",
                    "preco": "$remedio_mais_caro.preco"
                }
            }
        }
    ]
    
    try:
        result = await aggregate(pipeline, Remedio.__collection__)
        logger.info("Agregação concluída")
        return {"data": result}
    except Exception as e:
        logger.error(f"Erro durante a agregação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante a agregação: {str(e)}")

# Agregação: Remédio mais barato por fornecedor
@router.get("/agregar/remedio-mais-barato-por-fornecedor", response_model=dict)
async def remedio_mais_barato_por_fornecedor():
    logger.info("Buscando remédio mais barato por fornecedor")
    
    pipeline = [
        {
            "$sort": {"preco": 1}
        },
        {
            "$group": {
                "_id": "$fornecedor_id",
                "remedio_mais_barato": {"$first": "$$ROOT"}
            }
        },
        {
            "$lookup": {
                "from": "fornecedor",
                "localField": "_id",
                "foreignField": "_id",
                "as": "fornecedor"
            }
        },
        {
            "$unwind": "$fornecedor"
        },
        {
            "$project": {
                "fornecedor_nome": "$fornecedor.nome",
                "remedio_mais_barato": {
                    "nome": "$remedio_mais_barato.nome",
                    "preco": "$remedio_mais_barato.preco"
                }
            }
        }
    ]
    
    try:
        result = await aggregate(pipeline, Remedio.__collection__)
        logger.info("Agregação concluída")
        return {"data": result}
    except Exception as e:
        logger.error(f"Erro durante a agregação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante a agregação: {str(e)}")
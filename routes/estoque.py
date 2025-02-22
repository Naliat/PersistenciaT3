import logging
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Path
from models.estoque import Estoque
from models.remedio import Remedio
from database import engine
from typing import Optional
from datetime import datetime

logger = logging.getLogger("estoques")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(
    prefix="/estoques",
    tags=["Estoques"]
)

# CREATE: Criar um novo estoque
@router.post("/", response_model=Estoque, status_code=201)
async def criar_estoque(estoque: Estoque):
    logger.info("Iniciando criação do estoque para o remédio: %s", estoque.remedio)
    
    # Verifique se o ID do remédio é uma string ou ObjectId e busque o remédio
    if estoque.remedio and estoque.remedio.id:
        # Se o ID for uma string, converta para ObjectId para buscar corretamente no banco
        try:
            remedio_id = ObjectId(estoque.remedio.id)
        except Exception as e:
            logger.error(f"Erro ao tentar converter ID do remédio: {e}")
            raise HTTPException(status_code=400, detail="ID do remédio inválido")
        
        # Busque o remédio no banco de dados com o ObjectId
        remedio = await engine.find_one(Remedio, {"_id": remedio_id})
        
        if not remedio:
            logger.error("Remédio não encontrado para o estoque")
            raise HTTPException(status_code=400, detail="Remédio não encontrado")
        
        # Atualize a referência para o objeto Remedio completo
        estoque.remedio = remedio
    
    # Salve o estoque no banco de dados
    novo_estoque = await engine.save(estoque)
    logger.info("Estoque criado com ID: %s", novo_estoque.id)
    
    return novo_estoque
# READ: Listar estoques com filtro (paginação)
@router.get("/", response_model=dict)
async def listar_estoques(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    quantidade_min: Optional[int] = Query(None, description="Quantidade mínima")
):
    logger.info("Listando estoques - Página: %s, Limite: %s", pagina, limite)
    skip = (pagina - 1) * limite
    query = {}
    if quantidade_min is not None:
        query["quantidade"] = {"$gte": quantidade_min}
    total = await engine.count(Estoque, query)
    itens = await engine.find(Estoque, query, skip=skip, limit=limite, sort=Estoque.validade)
    logger.info("Estoques listados: %s itens encontrados", total)
    return {
        "data": itens,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

# READ: Obter estoque por ID
@router.get("/{estoque_id}", response_model=Estoque)
async def obter_estoque_por_id(
    estoque_id: int = Path(..., description="ID do estoque")
):
    logger.info("Obtendo estoque por ID: %s", estoque_id)
    estoque = await engine.find_one(Estoque, {"id": estoque_id})
    if not estoque:
        logger.error("Estoque com ID %s não encontrado", estoque_id)
        raise HTTPException(status_code=404, detail="Estoque não encontrado")
    logger.info("Estoque com ID %s obtido com sucesso", estoque_id)
    return estoque

# UPDATE: Atualizar um estoque existente
@router.put("/{estoque_id}", response_model=Estoque)
async def atualizar_estoque(
    estoque_id: int = Path(..., description="ID do estoque a ser atualizado"),
    estoque_update: Estoque = None
):
    logger.info("Atualizando estoque com ID: %s", estoque_id)
    estoque_existente = await engine.find_one(Estoque, {"id": estoque_id})
    if not estoque_existente:
        logger.error("Estoque com ID %s não encontrado para atualização", estoque_id)
        raise HTTPException(status_code=404, detail="Estoque não encontrado")
    update_data = estoque_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(estoque_existente, key, value)
    estoque_existente.atualizado_em = datetime.utcnow()
    updated_estoque = await engine.save(estoque_existente)
    logger.info("Estoque com ID %s atualizado com sucesso", estoque_id)
    return updated_estoque

# DELETE: Remover um estoque
@router.delete("/{estoque_id}", response_model=dict)
async def deletar_estoque(
    estoque_id: int = Path(..., description="ID do estoque a ser deletado")
):
    logger.info("Deletando estoque com ID: %s", estoque_id)
    estoque = await engine.find_one(Estoque, {"id": estoque_id})
    if not estoque:
        logger.error("Estoque com ID %s não encontrado para deleção", estoque_id)
        raise HTTPException(status_code=404, detail="Estoque não encontrado")
    await engine.delete(estoque)
    logger.info("Estoque com ID %s deletado com sucesso", estoque_id)
    return {"message": "Estoque deletado com sucesso"}

# ----------------- Endpoints de Busca (GET) -----------------

@router.get("/remedio/{remedio_id}", response_model=dict)
async def listar_estoques_por_remedio(
    remedio_id: int = Path(..., description="ID do remédio"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    logger.info("Listando estoques para o remédio com ID: %s", remedio_id)
    skip = (pagina - 1) * limite
    query = {"remedio.id": remedio_id}
    total = await engine.count(Estoque, query)
    itens = await engine.find(Estoque, query, skip=skip, limit=limite, sort=Estoque.data_entrada)
    logger.info("Estoques encontrados para o remédio %s: %s", remedio_id, total)
    return {
        "data": itens,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/buscar/validade", response_model=dict)
async def buscar_estoques_por_validade(
    inicio: datetime = Query(..., description="Data inicial (YYYY-MM-DDTHH:MM:SS)"),
    fim: datetime = Query(..., description="Data final (YYYY-MM-DDTHH:MM:SS)")
):
    logger.info("Buscando estoques com validade entre %s e %s", inicio, fim)
    query = {"validade": {"$gte": inicio, "$lte": fim}}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    logger.info("Estoques encontrados: %s", total)
    return {"data": itens, "total": total}

@router.get("/ordenar/entrada", response_model=dict)
async def listar_estoques_ordenados_por_entrada():
    logger.info("Listando estoques ordenados por data de entrada")
    query = {}
    itens = await engine.find(Estoque, query, sort=Estoque.data_entrada)
    total = await engine.count(Estoque, query)
    logger.info("Total de estoques: %s", total)
    return {"data": itens, "total": total}

@router.get("/buscar/mes_validade", response_model=dict)
async def buscar_estoques_por_mes_validade(
    ano: int = Query(..., description="Ano da validade"),
    mes: int = Query(..., ge=1, le=12, description="Mês da validade")
):
    logger.info("Buscando estoques com validade para %s/%s", mes, ano)
    inicio = datetime(ano, mes, 1)
    fim = datetime(ano, mes % 12 + 1, 1) if mes != 12 else datetime(ano + 1, 1, 1)
    query = {"validade": {"$gte": inicio, "$lt": fim}}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    logger.info("Estoques encontrados: %s", total)
    return {"data": itens, "total": total}

@router.get("/contagem", response_model=dict)
async def contar_estoques():
    total = await engine.count(Estoque, {})
    logger.info("Contagem total de estoques: %s", total)
    return {"total_estoques": total}

@router.get("/buscar/quantidade", response_model=dict)
async def buscar_estoques_por_quantidade(
    quantidade: int = Query(..., description="Quantidade exata")
):
    logger.info("Buscando estoques com quantidade exata: %s", quantidade)
    query = {"quantidade": quantidade}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    logger.info("Estoques encontrados: %s", total)
    return {"data": itens, "total": total}

@router.get("/buscar/entrada/apos", response_model=dict)
async def buscar_estoques_entrada_apos(
    data: datetime = Query(..., description="Data limite (YYYY-MM-DDTHH:MM:SS)")
):
    logger.info("Buscando estoques com data de entrada posterior a: %s", data)
    query = {"data_entrada": {"$gte": data}}
    itens = await engine.find(Estoque, query, sort=Estoque.data_entrada)
    total = await engine.count(Estoque, query)
    logger.info("Estoques encontrados: %s", total)
    return {"data": itens, "total": total}

@router.get("/buscar/entrada/antes", response_model=dict)
async def buscar_estoques_entrada_antes(
    data: datetime = Query(..., description="Data limite (YYYY-MM-DDTHH:MM:SS)")
):
    logger.info("Buscando estoques com data de entrada anterior a: %s", data)
    query = {"data_entrada": {"$lte": data}}
    itens = await engine.find(Estoque, query, sort=Estoque.data_entrada)
    total = await engine.count(Estoque, query)
    logger.info("Estoques encontrados: %s", total)
    return {"data": itens, "total": total}

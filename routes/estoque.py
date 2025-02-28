import logging
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Path, Body
from models.estoque import Estoque
from models.remedio import Remedio
from database import engine
from typing import Optional, Any, Dict
from datetime import datetime, timezone

# Configuração do logger para os estoques
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
    """
    Cria um novo estoque associado a um remédio.
    
    Parâmetros:
    - estoque: Um objeto Estoque contendo os dados do estoque a ser criado.
    
    Retorna:
    - O estoque recém-criado.
    
    Levanta:
    - HTTPException com erro 400 se o ID do remédio for inválido ou o remédio não for encontrado.
    """
    logger.info("Iniciando criação do estoque para o remédio: %s", estoque.remedio)
    
    if estoque.remedio and estoque.remedio.id:
        try:
            remedio_id = ObjectId(estoque.remedio.id)
        except Exception as e:
            logger.error(f"Erro ao tentar converter ID do remédio: {e}")
            raise HTTPException(status_code=400, detail="ID do remédio inválido")
        
        remedio = await engine.find_one(Remedio, {"_id": remedio_id})
        
        if not remedio:
            logger.error("Remédio não encontrado para o estoque")
            raise HTTPException(status_code=400, detail="Remédio não encontrado")
        
        estoque.remedio = remedio
    
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
    """
    Lista os estoques de medicamentos com suporte a filtros e paginação.
    
    Parâmetros:
    - pagina: Número da página para a paginação (default: 1).
    - limite: Número de itens por página (default: 10, máximo: 100).
    - quantidade_min: Filtra estoques com quantidade mínima especificada.
    
    Retorna:
    - Dicionário com os dados dos estoques, incluindo o número da página, total de itens, etc.
    """
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
    estoque_id: str = Path(..., description="ID do estoque")
):
    """
    Obtém um estoque específico pelo seu ID.
    
    Parâmetros:
    - estoque_id: ID do estoque a ser recuperado.
    
    Retorna:
    - O estoque encontrado.
    
    Levanta:
    - HTTPException com erro 400 se o ID do estoque for inválido.
    - HTTPException com erro 404 se o estoque não for encontrado.
    """
    logger.info("Obtendo estoque por ID: %s", estoque_id)

    try:
        estoque_id = ObjectId(estoque_id)
    except Exception:
        logger.error("ID do estoque inválido: %s", estoque_id)
        raise HTTPException(status_code=400, detail="ID do estoque inválido")

    estoque = await engine.find_one(Estoque, {"_id": estoque_id})
    if not estoque:
        logger.error("Estoque com ID %s não encontrado", estoque_id)
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    logger.info("Estoque com ID %s obtido com sucesso", estoque_id)
    return estoque

# UPDATE: Atualizar um estoque existente
@router.put("/{estoque_id}", response_model=Estoque)
async def atualizar_estoque(
    estoque_id: str = Path(description="ID do estoque a ser atualizado"),
    estoque_update: Estoque = Body()
):
    """
    Atualiza um estoque existente baseado no ID.
    
    Parâmetros:
    - estoque_id: ID do estoque a ser atualizado.
    - estoque_update: Dados para atualização do estoque.
    
    Retorna:
    - O estoque atualizado.
    
    Levanta:
    - HTTPException com erro 400 se o ID for inválido.
    - HTTPException com erro 404 se o estoque não for encontrado.
    """
    try:
        estoque_object_id = ObjectId(estoque_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    estoque_existente = await engine.find_one(Estoque, Estoque.id == estoque_object_id)

    if not estoque_existente:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    update_data = estoque_update.model_dump(exclude_unset=True)
    update_data.pop("id", None)

    for key, value in update_data.items():
        setattr(estoque_existente, key, value)

    estoque_existente.atualizado_em = datetime.now(timezone.utc)

    updated_estoque = await engine.save(estoque_existente)

    return updated_estoque

# DELETE: Deletar um estoque
@router.delete("/{estoque_id}", response_model=dict)
async def deletar_estoque(
    estoque_id: str = Path(..., description="ID do estoque a ser deletado")
):
    """
    Deleta um estoque específico pelo seu ID.
    
    Parâmetros:
    - estoque_id: ID do estoque a ser deletado.
    
    Retorna:
    - Mensagem indicando que o estoque foi deletado.
    
    Levanta:
    - HTTPException com erro 400 se o ID for inválido.
    - HTTPException com erro 404 se o estoque não for encontrado.
    """
    logger.info("Deletando estoque com ID: %s", estoque_id)
    
    try:
        estoque_object_id = ObjectId(estoque_id)
    except Exception:
        logger.error("ID de estoque inválido: %s", estoque_id)
        raise HTTPException(status_code=400, detail="ID do estoque inválido")
    
    estoque = await engine.find_one(Estoque, {"_id": estoque_object_id})
    if not estoque:
        logger.error("Estoque com ID %s não encontrado para deleção", estoque_id)
        raise HTTPException(status_code=404, detail="Estoque não encontrado")
    
    await engine.delete(estoque)
    logger.info("Estoque com ID %s deletado com sucesso", estoque_id)
    return {"message": "Estoque deletado com sucesso"}

# READ: Listar estoques para um remédio
@router.get("/remedio/{remedio_id}", response_model=dict)
async def listar_estoques_por_remedio(
    remedio_id: str = Path(..., description="ID do remédio"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100)
):
    """
    Lista os estoques de um remédio específico.
    
    Parâmetros:
    - remedio_id: ID do remédio cujos estoques serão listados.
    - pagina: Número da página para a paginação.
    - limite: Número de itens por página.
    
    Retorna:
    - Dicionário com os estoques encontrados, incluindo a paginação.
    
    Levanta:
    - HTTPException com erro 400 se o ID do remédio for inválido.
    """
    logger.info("Listando estoques para o remédio com ID: %s", remedio_id)
    try:
        remedio_id = ObjectId(remedio_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID do remédio inválido")
    skip = (pagina - 1) * limite
    query = {"remedio": remedio_id}
    total = await engine.count(Estoque, query)
    itens = await engine.find(Estoque, query, skip=skip, limit=limite, sort=Estoque.validade)
    return {
        "data": itens,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

# READ: Buscar estoques por validade
@router.get("/buscar/validade", response_model=dict)
async def buscar_estoques_por_validade(
    inicio: datetime = Query(..., description="Data inicial (YYYY-MM-DDTHH:MM:SS)"),
    fim: datetime = Query(..., description="Data final (YYYY-MM-DDTHH:MM:SS)")
):
    """
    Busca estoques com validade entre duas datas.
    
    Parâmetros:
    - inicio: Data inicial para a busca.
    - fim: Data final para a busca.
    
    Retorna:
    - Dicionário com os estoques encontrados e o total.
    """
    logger.info("Buscando estoques com validade entre %s e %s", inicio, fim)
    query = {"validade": {"$gte": inicio, "$lte": fim}}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    return {"data": itens, "total": total}

# READ: Listar estoques ordenados por data de entrada
@router.get("/ordenar/entrada", response_model=dict)
async def listar_estoques_ordenados_por_entrada():
    """
    Lista estoques ordenados pela data de entrada.
    
    Retorna:
    - Dicionário com os estoques ordenados e o total.
    """
    logger.info("Listando estoques ordenados por data de entrada")
    query = {}
    itens = await engine.find(Estoque, query, sort=Estoque.data_entrada)
    total = await engine.count(Estoque, query)
    return {"data": itens, "total": total}

# READ: Buscar estoques por mês de validade
@router.get("/buscar/mes_validade", response_model=dict)
async def buscar_estoques_por_mes_validade(
    ano: int = Query(..., description="Ano da validade"),
    mes: int = Query(..., ge=1, le=12, description="Mês da validade")
):
    """
    Busca estoques com validade dentro de um mês específico.
    
    Parâmetros:
    - ano: Ano da validade.
    - mes: Mês da validade.
    
    Retorna:
    - Dicionário com os estoques encontrados e o total.
    """
    logger.info("Buscando estoques com validade para %s/%s", mes, ano)
    inicio = datetime(ano, mes, 1)
    fim = datetime(ano, mes % 12 + 1, 1) if mes != 12 else datetime(ano + 1, 1, 1)
    query = {"validade": {"$gte": inicio, "$lt": fim}}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    return {"data": itens, "total": total}

# READ: Buscar estoques por quantidade
@router.get("/buscar/quantidade", response_model=dict)
async def buscar_estoques_por_quantidade(
    quantidade: int = Query(..., description="Quantidade exata")
):
    """
    Busca estoques com uma quantidade exata.
    
    Parâmetros:
    - quantidade: Quantidade exata do estoque.
    
    Retorna:
    - Dicionário com os estoques encontrados e o total.
    """
    query = {"quantidade": quantidade}
    itens = await engine.find(Estoque, query, sort=Estoque.validade)
    total = await engine.count(Estoque, query)
    return {"data": itens, "total": total}



@router.get("/agregado/estoque", response_model=Dict[str, Any])
async def obter_estoque(
    remedio_nome: Optional[str] = Query(None, description="Filtrar pelo nome do remédio")
):
    """
    Retorna a quantidade total de um remédio no estoque e os detalhes dos estoques onde ele está armazenado.
    - Se `remedio_nome` for informado, retorna a quantidade total e os estoques relacionados.
    """

    if not remedio_nome:
        return {"erro": "Informe um nome de remédio para buscar os dados."}

    pipeline = [
        # Faz um JOIN entre Estoque e Remedio pelo campo `remedio`
        {
            "$lookup": {
                "from": "remedios",  # Nome da coleção de remédios
                "localField": "remedio",
                "foreignField": "_id",
                "as": "remedio"
            }
        },
        {"$unwind": "$remedio"},  # Converte o array de remédio em objeto único

        # Filtra pelo nome do remédio (busca parcial, case-insensitive)
        {
            "$match": {
                "remedio.nome": {"$regex": remedio_nome, "$options": "i"}
            }
        },

        # Agrupa por nome do remédio e soma a quantidade total em todos os estoques
        {
            "$group": {
                "_id": "$remedio.nome",
                "quantidade_total": {"$sum": "$quantidade"},
                "estoques": {
                    "$push": {
                        "estoque_id": "$_id",
                        "quantidade": "$quantidade",
                        "data_entrada": "$data_entrada"
                    }
                }
            }
        }
    ]

    collection = engine.get_collection(Estoque)
    resultados = await collection.aggregate(pipeline).to_list(length=None)

    if not resultados:
        return {"mensagem": "Nenhum estoque encontrado para esse remédio."}

    resultado = resultados[0]
    
    # Converter ObjectId para string
    for estoque in resultado["estoques"]:
        estoque["estoque_id"] = str(estoque["estoque_id"])

    return {
        "remedio": resultado["_id"],  # Nome do remédio
        "quantidade_total": resultado["quantidade_total"],
        "estoques": resultado["estoques"]
    }

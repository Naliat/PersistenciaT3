from odmantic import ObjectId
import logging
import re
from fastapi import APIRouter, Query, HTTPException, Path, Body
from models.fornecedor import Fornecedor
from database import engine
from typing import Optional, Dict
from datetime import datetime, timezone

# Configuração do logger para o módulo de fornecedores.
logger = logging.getLogger("fornecedores")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(
    prefix="/fornecedores",
    tags=["Fornecedores"]
)

# ------------------------------------------------------------------------------
# CRUD de Fornecedores
# ------------------------------------------------------------------------------

@router.post("/", response_model=Fornecedor, status_code=201)
async def criar_fornecedor(fornecedor: Fornecedor) -> Fornecedor:
    """
    Cria um novo fornecedor.

    Valida se já existe um fornecedor com o mesmo CNPJ antes de criar.
    
    Parâmetros:
      - fornecedor (Fornecedor): Objeto com os dados do fornecedor a ser criado.
    
    Retorna:
      - Fornecedor: O fornecedor criado com o seu ID gerado.
    
    Lança:
      - HTTPException 400 se o CNPJ já existir.
    """
    logger.info("Iniciando criação de fornecedor com CNPJ: %s", fornecedor.cnpj)
    existente = await engine.find_one(Fornecedor, {"cnpj": fornecedor.cnpj})
    if existente:
        logger.warning("Tentativa de criação de fornecedor com CNPJ duplicado: %s", fornecedor.cnpj)
        raise HTTPException(status_code=400, detail="Fornecedor com este CNPJ já existe.")
    novo_fornecedor = await engine.save(fornecedor)
    logger.info("Fornecedor criado com ID: %s", novo_fornecedor.id)
    return novo_fornecedor

@router.get("/", response_model=dict)
async def listar_fornecedores(
    pagina: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    limite: int = Query(10, ge=1, le=100, description="Número de itens por página"),
    nome: Optional[str] = Query(None, description="Filtro para busca parcial no nome do fornecedor"),
    cnpj: Optional[str] = Query(None, description="Filtro para busca exata no CNPJ")
) -> dict:
    """
    Lista os fornecedores com suporte a filtros e paginação.

    Parâmetros:
      - pagina (int): Página atual.
      - limite (int): Número de itens por página.
      - nome (str, opcional): Busca parcial pelo nome do fornecedor.
      - cnpj (str, opcional): Busca exata pelo CNPJ do fornecedor.
    
    Retorna:
      - dict: Dicionário contendo os fornecedores listados, página atual, total de itens, número de páginas e o limite.
    """
    logger.info("Listando fornecedores - Página: %s, Limite: %s", pagina, limite)
    skip = (pagina - 1) * limite
    query = {}
    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}
    if cnpj:
        query["cnpj"] = cnpj
    total = await engine.count(Fornecedor, query)
    fornecedores = await engine.find(Fornecedor, query, skip=skip, limit=limite, sort=Fornecedor.nome)
    logger.info("Fornecedores listados: %s itens encontrados", total)
    return {
        "data": fornecedores,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/{fornecedor_id}", response_model=Fornecedor)
async def obter_fornecedor_por_id(
    fornecedor_id: str = Path(..., description="ID do fornecedor")
) -> Fornecedor:
    """
    Obtém os detalhes de um fornecedor específico pelo seu ID.

    Parâmetros:
      - fornecedor_id (str): ID do fornecedor a ser buscado.
    
    Retorna:
      - Fornecedor: Objeto do fornecedor encontrado.
    
    Lança:
      - HTTPException 404 se o fornecedor não for encontrado.
    """
    logger.info("Obtendo fornecedor por ID: %s", fornecedor_id)
    fornecedor = await engine.find_one(Fornecedor, Fornecedor.id == ObjectId(fornecedor_id))
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    logger.info("Fornecedor com ID %s obtido com sucesso", fornecedor_id)
    return fornecedor

@router.put("/{fornecedor_id}", response_model=Fornecedor)
async def atualizar_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor a ser atualizado"),
    fornecedor_update: Fornecedor = Body(..., description="Dados para atualizar o fornecedor")
) -> Fornecedor:
    """
    Atualiza um fornecedor existente com os dados fornecidos.

    Parâmetros:
      - fornecedor_id (str): ID do fornecedor.
      - fornecedor_update (Fornecedor): Dados atualizados para o fornecedor.
    
    Retorna:
      - Fornecedor: Objeto do fornecedor atualizado.
    
    Lança:
      - HTTPException 404 se o fornecedor não for encontrado.
      - HTTPException 500 em caso de erro interno.
    """
    try:
        fornecedor_existente = await engine.find_one(Fornecedor, Fornecedor.id == ObjectId(fornecedor_id))
        if not fornecedor_existente:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
        
        update_data = fornecedor_update.model_dump(exclude_unset=True)
        update_data.pop('criado_em', None)
        update_data.pop('id', None)
        update_data['atualizado_em'] = datetime.now(timezone.utc)
        for key, value in update_data.items():
            setattr(fornecedor_existente, key, value)
        updated_fornecedor = await engine.save(fornecedor_existente)
        return updated_fornecedor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao atualizar fornecedor: {str(e)}")

@router.delete("/{fornecedor_id}", response_model=Dict[str, str])
async def deletar_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor a ser deletado")
) -> Dict[str, str]:
    """
    Deleta um fornecedor com base no seu ID.

    Parâmetros:
      - fornecedor_id (str): ID do fornecedor a ser removido.
    
    Retorna:
      - dict: Mensagem de confirmação da deleção.
    
    Lança:
      - HTTPException 400 se o ID for inválido.
      - HTTPException 404 se o fornecedor não for encontrado.
    """
    logger.info("Deletando fornecedor com ID: %s", fornecedor_id)
    try:
        fornecedor_object_id = ObjectId(fornecedor_id)
        fornecedor = await engine.find_one(Fornecedor, {"_id": fornecedor_object_id})
    except Exception as e:
        logger.error(f"Erro ao tentar converter o ID: {str(e)}")
        raise HTTPException(status_code=400, detail="ID de fornecedor inválido")
    
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado para deleção", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    
    await engine.delete(fornecedor)
    logger.info("Fornecedor com ID %s deletado com sucesso", fornecedor_id)
    return {"message": "Fornecedor deletado com sucesso"}

# ------------------------------------------------------------------------------
# Endpoints de Busca (GET) para Fornecedores
# ------------------------------------------------------------------------------

def normalizar_cnpj(cnpj: str) -> str:
    """
    Remove caracteres especiais do CNPJ, retornando apenas os dígitos.

    Parâmetros:
      - cnpj (str): CNPJ a ser normalizado.
    
    Retorna:
      - str: CNPJ normalizado contendo apenas dígitos.
    """
    return re.sub(r'[^0-9]', '', cnpj)

@router.get("/buscar/cnpj/{cnpj}", response_model=Fornecedor)
async def buscar_fornecedor_por_cnpj(
    cnpj: str = Path(..., description="CNPJ exato do fornecedor")
) -> Fornecedor:
    """
    Busca um fornecedor com base no CNPJ informado.

    Parâmetros:
      - cnpj (str): CNPJ do fornecedor.
    
    Retorna:
      - Fornecedor: Objeto do fornecedor encontrado.
    
    Lança:
      - HTTPException 404 se o fornecedor não for encontrado.
    """
    cnpj_normalizado = normalizar_cnpj(cnpj)
    logger.info("Buscando fornecedor com CNPJ: %s", cnpj_normalizado)
    fornecedor = await engine.find_one(Fornecedor, {"cnpj": cnpj_normalizado})
    if not fornecedor:
        logger.error("Fornecedor com CNPJ %s não encontrado", cnpj_normalizado)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    logger.info("Fornecedor com CNPJ %s encontrado", cnpj_normalizado)
    return fornecedor

@router.get("/buscar/prefixo", response_model=dict)
async def buscar_fornecedores_por_prefixo(
    prefixo: str = Query(..., description="Prefixo do nome do fornecedor")
) -> dict:
    """
    Busca fornecedores cujo nome inicia com o prefixo informado.

    Parâmetros:
      - prefixo (str): Prefixo para busca.
    
    Retorna:
      - dict: Dicionário com os fornecedores encontrados e o total.
    """
    logger.info("Buscando fornecedores com nome iniciando com: %s", prefixo)
    query = {"nome": {"$regex": f"^{prefixo}", "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/sufixo", response_model=dict)
async def buscar_fornecedores_por_sufixo(
    sufixo: str = Query(..., description="Sufixo do nome do fornecedor")
) -> dict:
    """
    Busca fornecedores cujo nome termina com o sufixo informado.

    Parâmetros:
      - sufixo (str): Sufixo para busca.
    
    Retorna:
      - dict: Dicionário com os fornecedores encontrados e o total.
    """
    logger.info("Buscando fornecedores com nome terminando com: %s", sufixo)
    query = {"nome": {"$regex": f"{sufixo}$", "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/ordenar/cnpj", response_model=dict)
async def listar_fornecedores_ordenados_por_cnpj() -> dict:
    """
    Lista todos os fornecedores ordenados pelo CNPJ.

    Retorna:
      - dict: Dicionário com os fornecedores ordenados e o total.
    """
    logger.info("Listando fornecedores ordenados por CNPJ")
    query = {}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.cnpj)
    total = await engine.count(Fornecedor, query)
    logger.info("Total de fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/endereco", response_model=dict)
async def buscar_fornecedores_por_endereco(
    endereco: str = Query(..., description="Parte do endereço para busca")
) -> dict:
    """
    Busca fornecedores que possuam a parte do endereço informado (busca parcial).

    Parâmetros:
      - endereco (str): Texto a ser buscado no endereço.
    
    Retorna:
      - dict: Dicionário com os fornecedores encontrados e o total.
    """
    logger.info("Buscando fornecedores com endereço contendo: %s", endereco)
    query = {"endereco": {"$regex": endereco, "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.endereco)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/criacao/apos", response_model=dict)
async def buscar_fornecedores_criados_apos(
    data: datetime = Query(..., description="Data limite (YYYY-MM-DDTHH:MM:SS)")
) -> dict:
    """
    Busca fornecedores criados após a data informada.

    Parâmetros:
      - data (datetime): Data limite para a busca.
    
    Retorna:
      - dict: Dicionário com os fornecedores encontrados e o total.
    """
    logger.info("Buscando fornecedores criados após: %s", data)
    query = {"criado_em": {"$gte": data}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

# ------------------------------------------------------------------------------
# Endpoint de Agregação: Fornecedores por Endereço
# ------------------------------------------------------------------------------

@router.get("/agregado/fornecedores-por-endereco", response_model=dict)
async def fornecedores_por_endereco(
    endereco: str = Query(..., description="Filtrar fornecedores por endereço (pode ser parcial)")
) -> dict:
    """
    Busca fornecedores cujo endereço contenha o termo informado e retorna:
      - A contagem total de fornecedores encontrados.
      - Os dados dos fornecedores (ID, nome, CNPJ, telefone, endereço, datas de criação e atualização).

    Parâmetros:
      - endereco (str): Texto a ser buscado no endereço do fornecedor.
    
    Retorna:
      - dict: Dicionário contendo:
          - quantidade (int): Número total de fornecedores encontrados.
          - fornecedores (List[dict]): Lista de fornecedores com os dados selecionados.
    """
    logger.info("Buscando fornecedores com endereço contendo: %s", endereco)
    pipeline = [
        {"$match": {"endereco": {"$regex": endereco, "$options": "i"}}},
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "nome": 1,
                "cnpj": 1,
                "telefone": 1,
                "endereco": 1,
                "criado_em": 1,
                "atualizado_em": 1
            }
        }
    ]
    collection = engine.get_collection(Fornecedor)
    fornecedores = await collection.aggregate(pipeline).to_list(length=None)
    quantidade = len(fornecedores)
    logger.info("Fornecedores encontrados: %s", quantidade)
    return {
        "quantidade": quantidade,
        "fornecedores": fornecedores
    }

import logging
from fastapi import APIRouter, Query, HTTPException, Path
from models.fornecedor import Fornecedor
from database import engine
from typing import Optional
from datetime import datetime

# Configurar o logger
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

# CREATE: Criar um novo fornecedor
@router.post("/", response_model=Fornecedor, status_code=201)
async def criar_fornecedor(fornecedor: Fornecedor):
    logger.info("Iniciando criação de fornecedor com CNPJ: %s", fornecedor.cnpj)
    existente = await engine.find_one(Fornecedor, {"cnpj": fornecedor.cnpj})
    if existente:
        logger.warning("Tentativa de criação de fornecedor com CNPJ duplicado: %s", fornecedor.cnpj)
        raise HTTPException(status_code=400, detail="Fornecedor com este CNPJ já existe.")
    novo_fornecedor = await engine.save(fornecedor)
    logger.info("Fornecedor criado com ID: %s", novo_fornecedor.id)
    return novo_fornecedor

# READ: Listar fornecedores com filtros (paginação)
@router.get("/", response_model=dict)
async def listar_fornecedores(
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    nome: Optional[str] = Query(None),
    cnpj: Optional[str] = Query(None)
):
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

# READ: Obter fornecedor por ID
@router.get("/{fornecedor_id}", response_model=Fornecedor)
async def obter_fornecedor_por_id(
    fornecedor_id: int = Path(..., description="ID do fornecedor")
):
    logger.info("Obtendo fornecedor por ID: %s", fornecedor_id)
    fornecedor = await engine.find_one(Fornecedor, {"id": fornecedor_id})
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    logger.info("Fornecedor com ID %s obtido com sucesso", fornecedor_id)
    return fornecedor

# UPDATE: Atualizar um fornecedor existente
@router.put("/{fornecedor_id}", response_model=Fornecedor)
async def atualizar_fornecedor(
    fornecedor_id: int = Path(..., description="ID do fornecedor a ser atualizado"),
    fornecedor_update: Fornecedor = None
):
    logger.info("Atualizando fornecedor com ID: %s", fornecedor_id)
    fornecedor_existente = await engine.find_one(Fornecedor, {"id": fornecedor_id})
    if not fornecedor_existente:
        logger.error("Fornecedor com ID %s não encontrado para atualização", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    update_data = fornecedor_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(fornecedor_existente, key, value)
    fornecedor_existente.atualizado_em = datetime.utcnow()
    updated_fornecedor = await engine.save(fornecedor_existente)
    logger.info("Fornecedor com ID %s atualizado", fornecedor_id)
    return updated_fornecedor

# DELETE: Remover um fornecedor
@router.delete("/{fornecedor_id}", response_model=dict)
async def deletar_fornecedor(
    fornecedor_id: int = Path(..., description="ID do fornecedor a ser deletado")
):
    logger.info("Deletando fornecedor com ID: %s", fornecedor_id)
    fornecedor = await engine.find_one(Fornecedor, {"id": fornecedor_id})
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado para deleção", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    await engine.delete(fornecedor)
    logger.info("Fornecedor com ID %s deletado com sucesso", fornecedor_id)
    return {"message": "Fornecedor deletado com sucesso"}

# ----------------- Endpoints de Busca (GET) -----------------

@router.get("/buscar/cnpj/{cnpj}", response_model=Fornecedor)
async def buscar_fornecedor_por_cnpj(
    cnpj: str = Path(..., description="CNPJ exato")
):
    logger.info("Buscando fornecedor com CNPJ: %s", cnpj)
    fornecedor = await engine.find_one(Fornecedor, {"cnpj": cnpj})
    if not fornecedor:
        logger.error("Fornecedor com CNPJ %s não encontrado", cnpj)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    logger.info("Fornecedor com CNPJ %s encontrado", cnpj)
    return fornecedor

@router.get("/buscar/prefixo", response_model=dict)
async def buscar_fornecedores_por_prefixo(
    prefixo: str = Query(..., description="Prefixo do nome")
):
    logger.info("Buscando fornecedores com nome iniciando com: %s", prefixo)
    query = {"nome": {"$regex": f"^{prefixo}", "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/sufixo", response_model=dict)
async def buscar_fornecedores_por_sufixo(
    sufixo: str = Query(..., description="Sufixo do nome")
):
    logger.info("Buscando fornecedores com nome terminando com: %s", sufixo)
    query = {"nome": {"$regex": f"{sufixo}$", "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/ordenar/cnpj", response_model=dict)
async def listar_fornecedores_ordenados_por_cnpj():
    logger.info("Listando fornecedores ordenados por CNPJ")
    query = {}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.cnpj)
    total = await engine.count(Fornecedor, query)
    logger.info("Total de fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/telefone", response_model=dict)
async def buscar_fornecedores_por_telefone(
    telefone: str = Query(..., description="Parte do telefone")
):
    logger.info("Buscando fornecedores com telefone contendo: %s", telefone)
    query = {"telefone": {"$regex": telefone, "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.telefone)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/endereco", response_model=dict)
async def buscar_fornecedores_por_endereco(
    endereco: str = Query(..., description="Parte do endereço")
):
    logger.info("Buscando fornecedores com endereço contendo: %s", endereco)
    query = {"endereco": {"$regex": endereco, "$options": "i"}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.endereco)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/buscar/criacao/apos", response_model=dict)
async def buscar_fornecedores_criados_apos(
    data: datetime = Query(..., description="Data limite (YYYY-MM-DDTHH:MM:SS)")
):
    logger.info("Buscando fornecedores criados após: %s", data)
    query = {"criado_em": {"$gte": data}}
    fornecedores = await engine.find(Fornecedor, query, sort=Fornecedor.nome)
    total = await engine.count(Fornecedor, query)
    logger.info("Fornecedores encontrados: %s", total)
    return {"data": fornecedores, "total": total}

@router.get("/contagem", response_model=dict)
async def contar_fornecedores():
    total = await engine.count(Fornecedor, {})
    logger.info("Contagem total de fornecedores: %s", total)
    return {"total_fornecedores": total}

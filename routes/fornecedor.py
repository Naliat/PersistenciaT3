from odmantic import ObjectId
import logging
import re
from fastapi import APIRouter, Query, HTTPException, Path, Body
from models.fornecedor import Fornecedor
from database import engine
from typing import Optional, Dict
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
    fornecedor_id: str  = Path(..., description="ID do fornecedor")
):
    logger.info("Obtendo fornecedor por ID: %s", fornecedor_id)
    fornecedor = await engine.find_one(Fornecedor, Fornecedor.id == ObjectId(fornecedor_id))
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    logger.info("Fornecedor com ID %s obtido com sucesso", fornecedor_id)
    return fornecedor
# UPDATE: Atualizar um fornecedor existente
@router.put("/{fornecedor_id}", response_model=Fornecedor)
async def atualizar_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor a ser atualizado"),
    fornecedor_update: Fornecedor = Body(...)
):
    try:
        # Buscar o fornecedor existente pelo ID
        fornecedor_existente = await engine.find_one(Fornecedor, Fornecedor.id == ObjectId(fornecedor_id))

        if not fornecedor_existente:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

        # Excluir campos que não devem ser atualizados
        update_data = fornecedor_update.dict(exclude_unset=True)
        update_data.pop('criado_em', None)  # Não deve ser atualizado
        update_data.pop('id', None)  # Não deve ser atualizado diretamente

        # Atualizar o campo 'atualizado_em'
        update_data['atualizado_em'] = datetime.utcnow()

        # Atualizar os campos do fornecedor
        for key, value in update_data.items():
            setattr(fornecedor_existente, key, value)

        # Salvar as alterações
        updated_fornecedor = await engine.save(fornecedor_existente)

        return updated_fornecedor
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar fornecedor")

@router.delete("/{fornecedor_id}", response_model=Dict[str, str])
async def deletar_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor a ser deletado")
):
    logger.info("Deletando fornecedor com ID: %s", fornecedor_id)
    
    try:
        # Convertendo o fornecedor_id para ObjectId se necessário
        fornecedor_object_id = ObjectId(fornecedor_id)  # Se for um ObjectId do MongoDB

        # Buscar o fornecedor com o ID fornecido
        fornecedor = await engine.find_one(Fornecedor, {"_id": fornecedor_object_id})
        
    except Exception as e:
        logger.error(f"Erro ao tentar converter o ID: {str(e)}")
        raise HTTPException(status_code=400, detail="ID de fornecedor inválido")
    
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado para deleção", fornecedor_id)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    
    # Deletar o fornecedor
    await engine.delete(fornecedor)
    
    logger.info("Fornecedor com ID %s deletado com sucesso", fornecedor_id)
    
    # Retornar mensagem de sucesso
    return {"message": "Fornecedor deletado com sucesso"}
# ----------------- Endpoints de Busca (GET) -----------------
# Função para normalizar o CNPJ (remover caracteres especiais)
def normalizar_cnpj(cnpj: str) -> str:
    return re.sub(r'[^0-9]', '', cnpj)

# Buscar fornecedor pelo CNPJ
@router.get("/buscar/cnpj/{cnpj}", response_model=Fornecedor)
async def buscar_fornecedor_por_cnpj(
    cnpj: str = Path(..., description="CNPJ exato")
):
    cnpj_normalizado = normalizar_cnpj(cnpj)  # Normalizando o CNPJ
    logger.info("Buscando fornecedor com CNPJ: %s", cnpj_normalizado)
    
    fornecedor = await engine.find_one(Fornecedor, {"cnpj": cnpj_normalizado})
    
    if not fornecedor:
        logger.error("Fornecedor com CNPJ %s não encontrado", cnpj_normalizado)
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    
    logger.info("Fornecedor com CNPJ %s encontrado", cnpj_normalizado)
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

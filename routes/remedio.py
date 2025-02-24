import logging
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Path, Body
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timezone

from models.remedio import Remedio
from models.fornecedor import Fornecedor
from database import engine

# Configuração do logger para o módulo de remédios.
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

# =========================
# CRUD de Remédios
# =========================

@router.post("/", response_model=Remedio, status_code=201)
async def criar_remedio(remedio: Remedio) -> Remedio:
    """
    Cria um novo remédio.

    Valida o 'fornecedor_id' (deve ser um ObjectId válido) e verifica se o fornecedor existe.
    Em seguida, salva o remédio no banco de dados.

    Parâmetros:
      - remedio (Remedio): Objeto Remedio contendo os dados do remédio a ser criado.

    Retorna:
      - Remedio: O remédio criado com seu ID gerado.
    """
    logger.info("Iniciando criação do remédio: %s", remedio.nome)

    # Verifica se o fornecedor_id é válido antes de converter para ObjectId
    if not ObjectId.is_valid(remedio.fornecedor_id):
        logger.error("ID do fornecedor inválido: %s", remedio.fornecedor_id)
        raise HTTPException(status_code=400, detail="ID do fornecedor inválido.")

    fornecedor_id = ObjectId(remedio.fornecedor_id)

    # Consulta o fornecedor no banco de dados
    fornecedor = await engine.find_one(Fornecedor, Fornecedor.id == fornecedor_id)
    if not fornecedor:
        logger.error("Fornecedor com ID %s não encontrado para o remédio: %s", fornecedor_id, remedio.nome)
        raise HTTPException(status_code=400, detail="Fornecedor não encontrado.")

    # Salva o remédio no banco de dados
    novo_remedio = await engine.save(remedio)
    logger.info("Remédio criado com ID: %s", novo_remedio.id)
    return novo_remedio

@router.get("/", response_model=dict)
async def listar_remedios(
    pagina: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    limite: int = Query(10, ge=1, le=100, description="Número de itens por página"),
    nome: Optional[str] = Query(None, description="Filtro pelo nome do remédio (busca parcial)"),
    validade_inicio: Optional[date] = Query(None, description="Data inicial da validade (YYYY-MM-DD)"),
    validade_fim: Optional[date] = Query(None, description="Data final da validade (YYYY-MM-DD)")
) -> dict:
    """
    Lista os remédios com filtros e paginação.

    Parâmetros de Consulta:
      - pagina (int): Número da página.
      - limite (int): Número de itens por página.
      - nome (str, opcional): Filtro para busca parcial no nome do remédio.
      - validade_inicio (date, opcional): Data inicial para filtro de validade.
      - validade_fim (date, opcional): Data final para filtro de validade.

    Retorna:
      - dict: Um dicionário contendo a lista de remédios, paginação e total de itens.
    """
    logger.info("Listando remédios - Página: %s, Limite: %s", pagina, limite)
    skip = (pagina - 1) * limite
    query = {}

    if nome:
        query["nome"] = {"$regex": nome, "$options": "i"}
    if validade_inicio and validade_fim:
        # Converte as datas para datetime, definindo os limites do dia
        validade_inicio = datetime.combine(validade_inicio, datetime.min.time())
        validade_fim = datetime.combine(validade_fim, datetime.max.time())
        query["validade"] = {"$gte": validade_inicio, "$lte": validade_fim}

    total = await engine.count(Remedio, query)
    remedios = await engine.find(Remedio, query, skip=skip, limit=limite, sort=Remedio.validade)
    logger.info("Remédios listados: %s itens encontrados", total)
    return {
        "data": remedios,
        "pagina": pagina,
        "total": total,
        "paginas": (total + limite - 1) // limite,
        "limite": limite
    }

@router.get("/contagem", response_model=dict)
async def contar_remedios() -> dict:
    """
    Retorna a contagem total de remédios armazenados.

    Retorna:
      - dict: Dicionário com a chave 'total_remedios'.
    """
    total = await engine.count(Remedio, {})
    logger.info("Contagem total de remédios: %s", total)
    return {"total_remedios": total}

@router.get("/{remedio_id}", response_model=Remedio)
async def obter_remedio_por_id(
    remedio_id: str = Path(..., description="ID do remédio")
) -> Remedio:
    """
    Retorna os detalhes de um remédio específico com base no seu ID.

    Parâmetros:
      - remedio_id (str): ID do remédio a ser buscado.

    Retorna:
      - Remedio: O objeto Remedio encontrado.

    Lança HTTPException caso o ID seja inválido ou o remédio não seja encontrado.
    """
    logger.info("Obtendo remédio por ID: %s", remedio_id)

    try:
        remedio_id = ObjectId(remedio_id)
    except Exception:
        logger.error("ID do remédio inválido: %s", remedio_id)
        raise HTTPException(status_code=400, detail="ID do remédio inválido")
    
    remedio = await engine.find_one(Remedio, {"_id": remedio_id})
    if not remedio:
        logger.error("Remédio com ID %s não encontrado", remedio_id)
        raise HTTPException(status_code=404, detail="Remédio não encontrado")
    
    logger.info("Remédio com ID %s obtido com sucesso", remedio_id)
    return remedio

@router.put("/{remedio_id}", response_model=Remedio)
async def atualizar_remedio(
    remedio_id: str = Path(..., description="ID do remédio a ser atualizado"),
    remedio_update: Remedio = Body(..., description="Dados para atualizar o remédio")
) -> Remedio:
    """
    Atualiza um remédio existente com os novos dados fornecidos.

    Parâmetros:
      - remedio_id (str): ID do remédio a ser atualizado.
      - remedio_update (Remedio): Dados para atualizar o remédio.

    Retorna:
      - Remedio: O remédio atualizado.

    Lança HTTPException se o ID for inválido ou se o remédio não for encontrado.
    """
    logger.info("Iniciando atualização do remédio com ID: %s", remedio_id)

    try:
        remedio_id = ObjectId(remedio_id)
    except Exception:
        logger.error("ID inválido: %s", remedio_id)
        raise HTTPException(status_code=400, detail="ID do remédio inválido")
    
    remedio_existente = await engine.find_one(Remedio, Remedio.id == remedio_id)
    if not remedio_existente:
        logger.error("Remédio com ID %s não encontrado para atualização", remedio_id)
        raise HTTPException(status_code=404, detail="Remédio não encontrado")
    
    update_data = remedio_update.model_dump(exclude_unset=True)
    update_data.pop("id", None)  # Evita atualização do ID

    for key, value in update_data.items():
        setattr(remedio_existente, key, value)

    remedio_existente.atualizado_em = datetime.now(timezone.utc)
    updated_remedio = await engine.save(remedio_existente)
    logger.info("Remédio com ID %s atualizado com sucesso", remedio_id)
    return updated_remedio

@router.delete("/{remedio_id}", response_model=dict)
async def deletar_remedio(
    remedio_id: str = Path(..., description="ID do remédio a ser deletado")
) -> dict:
    """
    Deleta um remédio com base no seu ID.

    Parâmetros:
      - remedio_id (str): ID do remédio a ser removido.

    Retorna:
      - dict: Mensagem de confirmação da deleção.

    Lança HTTPException se o ID for inválido ou se o remédio não for encontrado.
    """
    try:
        remedio_id = ObjectId(remedio_id)
    except Exception:
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

# =========================
# Endpoints de Busca (GET)
# =========================

@router.get("/fornecedor/{fornecedor_id}", response_model=dict)
async def listar_remedios_por_fornecedor(
    fornecedor_id: str = Path(..., description="ID do fornecedor"),
    pagina: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    limite: int = Query(10, ge=1, le=100, description="Número de itens por página")
) -> dict:
    """
    Lista os remédios de um determinado fornecedor, usando seu ID, com suporte à paginação.

    Parâmetros:
      - fornecedor_id (str): ID do fornecedor.
      - pagina (int): Página atual.
      - limite (int): Número de itens por página.

    Retorna:
      - dict: Contendo os remédios do fornecedor, informações de paginação e total de itens.
    """
    logger.info("Listando remédios do fornecedor ID: %s", fornecedor_id)
    try:
        fornecedor_id = ObjectId(fornecedor_id)
    except Exception:
        logger.error("ID do fornecedor inválido: %s", fornecedor_id)
        raise HTTPException(status_code=400, detail="ID do fornecedor inválido")
    
    skip = (pagina - 1) * limite
    query = {"fornecedor_id": fornecedor_id}
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
) -> dict:
    """
    Busca remédios cujo preço seja maior ou igual ao valor informado.

    Parâmetros:
      - preco (float): Preço mínimo.

    Retorna:
      - dict: Lista de remédios encontrados e o total.
    """
    logger.info("Buscando remédios com preço maior que: %s", preco)
    query = {"preco": {"$gte": preco}}
    remedios = await engine.find(Remedio, query, sort=Remedio.preco)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/preco/menor", response_model=dict)
async def buscar_remedios_preco_menor(
    preco: float = Query(..., description="Preço máximo")
) -> dict:
    """
    Busca remédios cujo preço seja menor ou igual ao valor informado.

    Parâmetros:
      - preco (float): Preço máximo.

    Retorna:
      - dict: Lista de remédios encontrados e o total.
    """
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
) -> dict:
    """
    Busca remédios criados entre duas datas.

    Parâmetros:
      - inicio (datetime): Data e hora inicial.
      - fim (datetime): Data e hora final.

    Retorna:
      - dict: Lista de remédios e o total encontrados no período.
    """
    logger.info("Buscando remédios criados entre %s e %s", inicio, fim)
    query = {"criado_em": {"$gte": inicio, "$lte": fim}}
    remedios = await engine.find(Remedio, query, sort=Remedio.criado_em)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/prefixo", response_model=dict)
async def buscar_remedios_por_prefixo(
    prefixo: str = Query(..., description="Prefixo do nome do remédio")
) -> dict:
    """
    Busca remédios cujo nome inicie com o prefixo informado.

    Parâmetros:
      - prefixo (str): Prefixo para busca.

    Retorna:
      - dict: Lista de remédios e o total encontrados.
    """
    logger.info("Buscando remédios cujo nome inicia com: %s", prefixo)
    query = {"nome": {"$regex": f"^{prefixo}", "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/sufixo", response_model=dict)
async def buscar_remedios_por_sufixo(
    sufixo: str = Query(..., description="Sufixo do nome do remédio")
) -> dict:
    """
    Busca remédios cujo nome termine com o sufixo informado.

    Parâmetros:
      - sufixo (str): Sufixo para busca.

    Retorna:
      - dict: Lista de remédios e o total encontrados.
    """
    logger.info("Buscando remédios cujo nome termina com: %s", sufixo)
    query = {"nome": {"$regex": f"{sufixo}$", "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

@router.get("/buscar/descricao", response_model=dict)
async def buscar_remedios_por_descricao(
    descricao: str = Query(..., description="Parte da descrição do remédio")
) -> dict:
    """
    Busca remédios cuja descrição contenha o termo informado.

    Parâmetros:
      - descricao (str): Termo para busca na descrição.

    Retorna:
      - dict: Lista de remédios e o total encontrados.
    """
    logger.info("Buscando remédios com descrição contendo: %s", descricao)
    query = {"descricao": {"$regex": descricao, "$options": "i"}}
    remedios = await engine.find(Remedio, query, sort=Remedio.nome)
    total = await engine.count(Remedio, query)
    logger.info("Remédios encontrados: %s", total)
    return {"data": remedios, "total": total}

# =========================
# Endpoint de Agregação
# =========================

@router.get("/agregado/remedios-por-fornecedor", response_model=Dict[str, Any])
async def remedios_por_fornecedor(
    fornecedor_nome: str = Query(..., description="Filtrar remédios pelo nome do fornecedor (busca parcial)")
) -> Dict[str, Any]:
    """
    Agrupa os remédios por fornecedor utilizando o campo 'fornecedor_id' presente em cada remédio.

    O pipeline realiza os seguintes passos:
      1. $addFields: Converte o campo 'fornecedor_id' (armazenado como string) para ObjectId,
         criando o campo auxiliar 'fornecedor_id_obj'.
      2. $lookup: Junta os dados do fornecedor da coleção 'fornecedores' utilizando o campo 'fornecedor_id_obj'.
      3. $unwind: Converte o array resultante do lookup em um objeto único.
      4. $match: Filtra os documentos onde o nome do fornecedor contém o termo informado (busca parcial, case-insensitive).
      5. $group: Agrupa os remédios pelo ID do fornecedor, acumulando em um array e extraindo os dados do fornecedor.
      6. $project: Formata a saída final, convertendo os ObjectIds para string e retornando os campos desejados.

    Parâmetros:
      - fornecedor_nome (str): Termo para busca parcial no nome do fornecedor.

    Retorna:
      - dict: Um dicionário com a chave 'data' contendo uma lista de fornecedores. Cada fornecedor possui:
          - fornecedor_id (str): ID do fornecedor.
          - fornecedor_nome (str): Nome do fornecedor.
          - fornecedor_cnpj (str): CNPJ do fornecedor.
          - remedios (List[dict]): Lista de remédios associados, contendo:
                - remedio_id (str): ID do remédio.
                - nome (str): Nome do remédio.
                - descricao (str): Descrição do remédio.
                - preco (float): Preço do remédio.
                - validade (datetime): Data de validade.
                - criado_em (datetime): Data de criação.
                - atualizado_em (datetime): Data de atualização.

    Caso nenhum remédio seja encontrado para o filtro informado, retorna uma mensagem informando que nenhum resultado foi encontrado.
    """
    pipeline = [
        # 1. Converter o campo 'fornecedor_id' (string) para ObjectId e criar um campo auxiliar.
        {
            "$addFields": {
                "fornecedor_id_obj": {"$toObjectId": "$fornecedor_id"}
            }
        },
        # 2. Lookup: junta os dados do fornecedor a partir do campo auxiliar.
        {
            "$lookup": {
                "from": "fornecedores",
                "localField": "fornecedor_id_obj",
                "foreignField": "_id",
                "as": "fornecedor"
            }
        },
        # 3. Unwind: transforma o array 'fornecedor' em um objeto único.
        {"$unwind": "$fornecedor"},
        # 4. Match: filtra os documentos onde o nome do fornecedor contém o termo informado.
        {
            "$match": {
                "fornecedor.nome": {"$regex": fornecedor_nome, "$options": "i"}
            }
        },
        # 5. Group: agrupa os remédios pelo ID do fornecedor e acumula os remédios em um array.
        {
            "$group": {
                "_id": "$fornecedor._id",
                "fornecedor_nome": {"$first": "$fornecedor.nome"},
                "fornecedor_cnpj": {"$first": "$fornecedor.cnpj"},
                "remedios": {"$push": {
                    "remedio_id": {"$toString": "$_id"},
                    "nome": "$nome",
                    "descricao": "$descricao",
                    "preco": "$preco",
                    "validade": "$validade",
                    "criado_em": "$criado_em",
                    "atualizado_em": "$atualizado_em"
                }}
            }
        },
        # 6. Project: formata a saída final, convertendo o _id do fornecedor para string.
        {
            "$project": {
                "_id": 0,
                "fornecedor_id": {"$toString": "$_id"},
                "fornecedor_nome": 1,
                "fornecedor_cnpj": 1,
                "remedios": 1
            }
        }
    ]

    collection = engine.get_collection(Remedio)
    resultados: List[Dict[str, Any]] = await collection.aggregate(pipeline).to_list(length=None)

    if not resultados:
        return {"mensagem": "Nenhum remédio referenciado nessa busca."}

    return {"data": resultados}

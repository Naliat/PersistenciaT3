from fastapi import APIRouter
import logging

# Configuração do logger para a Home
logger = logging.getLogger("home")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(
    prefix="",
    tags=["Home"]
)

@router.get("/", summary="Página Inicial", description="Página inicial do Sistema Farmácia com informações e links úteis para navegação.")
async def home():
    logger.info("Acessada a página inicial da API do Sistema Farmácia")
    return {
        "message": "Bem-vindo ao Sistema Farmácia!",
        "description": (
            "Esta API permite gerenciar informações de fornecedores, remédios e estoques. "
            "Utilize os endpoints disponíveis para consultar, criar, atualizar ou remover dados conforme necessário. "
            "Acompanhe os logs para monitoramento de todas as operações realizadas na API."
        ),
        "version": "1.0.0",
        "documentation": {
            "Swagger UI": "/docs",
            "OpenAPI": "/openapi.json",
            "Redoc": "/redoc"
        },
        "endpoints": {
            "Fornecedores": "/fornecedores",
            "Remédios": "/remedios",
            "Estoques": "/estoques"
        }
    }



from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["Home"]
)

@router.get("/")
async def home():
    return {
        "message": "Bem-vindo ao Sistema Farmácia",
        "endpoints": {
            "documentação": "/docs",
            "fornecedores": "/fornecedores",
            "remedios": "/remedios",
            "estoque": "/estoque"
        }
    }

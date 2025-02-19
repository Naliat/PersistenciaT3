from fastapi import FastAPI
from routes import home, fornecedor, remedio, estoque
from database import engine
import logging

app = FastAPI(
    title="Sistema Farmácia",
    description="API para gestão de fornecedores, remédios e estoque",
    version="1.0.0"
)

# Registrar rotas
app.include_router(home.router)
app.include_router(fornecedor.router)
app.include_router(remedio.router)
app.include_router(estoque.router)

@app.on_event("startup")
async def startup():
    logging.info("Conectando ao MongoDB...")
    await engine.client.admin.command('ping')
    logging.info("Conexão com MongoDB estabelecida com sucesso!")
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

async def startup():
    logging.info("Conectando ao MongoDB Atlas...")
    await engine.client.admin.command('ping')
    logging.info("Conexão com MongoDB Atlas estabelecida com sucesso!")

async def shutdown():
    logging.info("Desconectando do MongoDB Atlas...")
    await engine.client.close()
    logging.info("Conexão com MongoDB Atlas encerrada com sucesso!")


async def startup():
    logging.info("Conectando ao MongoDB Atlas...")
    await engine.client.admin.command('ping')
    logging.info("Conexão com MongoDB Atlas estabelecida com sucesso!")

async def shutdown():
    logging.info("Desconectando do MongoDB Atlas...")
    await engine.client.close()
    logging.info("Conexão com MongoDB Atlas encerrada com sucesso!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

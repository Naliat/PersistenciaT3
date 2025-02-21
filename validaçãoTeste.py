import pytest
from fastapi.testclient import TestClient
from main import app  # Assumindo que sua aplicação FastAPI está em main.py

client = TestClient(app)

# Teste para criar fornecedor
def test_criar_fornecedor():
    response = client.post(
        "/fornecedores/",
        json={
            "nome": "Teste Farma",
            "cnpj": "12.345.678/0011-22",
            "telefone": "(11) 99999-1234",
            "endereco": "Rua Teste, 100 - São Paulo, SP"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["nome"] == "Teste Farma"
    assert data["cnpj"] == "12.345.678/0011-22"

# Teste para listar fornecedores
def test_listar_fornecedores():
    response = client.get("/fornecedores/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert data["total"] > 0

# Teste para obter fornecedor por ID
def test_obter_fornecedor_por_id():
    # Criação de um fornecedor para testar
    response = client.post(
        "/fornecedores/",
        json={
            "nome": "Fornecedor de Teste",
            "cnpj": "12.345.678/0022-33",
            "telefone": "(11) 99999-5678",
            "endereco": "Rua Teste, 200 - São Paulo, SP"
        }
    )
    fornecedor_id = response.json()["id"]

    # Teste de consulta por ID
    response = client.get(f"/fornecedores/{fornecedor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fornecedor_id
    assert data["nome"] == "Fornecedor de Teste"

# Teste para buscar fornecedor por CNPJ
def test_buscar_fornecedor_por_cnpj():
    response = client.get("/fornecedores/buscar/cnpj/12.345.678/0009-11")
    assert response.status_code == 200
    data = response.json()
    assert data["cnpj"] == "12.345.678/0009-11"

# Teste para atualizar fornecedor
def test_atualizar_fornecedor():
    # Criação de um fornecedor para atualizar
    response = client.post(
        "/fornecedores/",
        json={
            "nome": "Fornecedor Atualizável",
            "cnpj": "12.345.678/0033-44",
            "telefone": "(11) 99999-7890",
            "endereco": "Rua Atualização, 300 - São Paulo, SP"
        }
    )
    fornecedor_id = response.json()["id"]

    # Atualizando fornecedor
    response = client.put(
        f"/fornecedores/{fornecedor_id}",
        json={"nome": "Fornecedor Atualizado", "telefone": "(11) 99999-0000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Fornecedor Atualizado"
    assert data["telefone"] == "(11) 99999-0000"

# Teste para deletar fornecedor
def test_deletar_fornecedor():
    # Criação de um fornecedor para deletar
    response = client.post(
        "/fornecedores/",
        json={
            "nome": "Fornecedor a Deletar",
            "cnpj": "12.345.678/0044-55",
            "telefone": "(11) 99999-2345",
            "endereco": "Rua Deleção, 400 - São Paulo, SP"
        }
    )
    fornecedor_id = response.json()["id"]

    # Deletando fornecedor
    response = client.delete(f"/fornecedores/{fornecedor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Fornecedor deletado com sucesso"

# Teste de contagem de fornecedores
def test_contar_fornecedores():
    response = client.get("/fornecedores/contagem")
    assert response.status_code == 200
    data = response.json()
    assert "total_fornecedores" in data
    assert data["total_fornecedores"] > 0

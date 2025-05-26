# API Lu Estilo - Teste de Codificação Backend

Este projeto implementa uma API RESTful para gerenciar clientes, produtos e pedidos, conforme especificado no teste de codificação.

## Tecnologias Utilizadas

*   Python 3.11+
*   FastAPI
*   SQLAlchemy (com SQLite para testes, configurável para PostgreSQL)
*   Pydantic
*   Pytest
*   Alembic (configuração inicial não incluída, mas dependência presente)
*   Passlib (para hashing de senhas)
*   Python-JOSE (para JWT)

## Estrutura do Projeto

```
lu_estilo_api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py             # Agregador de rotas v1
│   │       └── endpoints/         # Endpoints específicos (auth, clients, etc.)
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── clients.py
│   │           ├── orders.py
│   │           └── products.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configurações (variáveis de ambiente)
│   │   └── security.py        # Funções de segurança (JWT, senha)
│   ├── database.py            # Configuração da sessão do banco de dados
│   ├── models/
│   │   ├── __init__.py        # Torna models um pacote e importa todos
│   │   └── base.py            # Definições dos modelos SQLAlchemy
│   ├── schemas/
│   │   ├── __init__.py        # Torna schemas um pacote e importa todos
│   │   ├── client.py
│   │   ├── message.py         # Schemas para mensagens/respostas simples
│   │   ├── order.py
│   │   ├── product.py
│   │   ├── token.py
│   │   └── user.py            # Schemas Pydantic para validação e serialização
│   ├── services/
│   │   ├── __init__.py        # Torna services um pacote e importa todos
│   │   ├── auth.py
│   │   ├── client.py
│   │   ├── order.py
│   │   └── product.py         # Lógica de negócio e interação com o DB
│   └── main.py                # Ponto de entrada da aplicação FastAPI
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures e configuração do Pytest
│   ├── test_auth.py
│   ├── test_clients.py
│   ├── test_orders.py
│   └── test_products.py       # Testes automatizados para os endpoints
├── .env.example             # Exemplo de arquivo de variáveis de ambiente
├── requirements.txt         # Dependências Python
├── todo.md                  # Checklist de desenvolvimento (interno)
└── README.md                # Este arquivo
```

## Configuração e Execução

1.  **Clone o repositório (ou extraia o .zip).**
2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **(Opcional) Crie um arquivo `.env`** na raiz do projeto (`lu_estilo_api/`) baseado no `.env.example` para configurar variáveis de ambiente, como `SECRET_KEY` e `DATABASE_URL` (se for usar um banco diferente do SQLite de teste).
    *   Para a execução padrão com Uvicorn e testes, as configurações padrão (SQLite em memória para testes, segredo fixo) serão usadas se `.env` não existir.

5.  **Execute a API com Uvicorn:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    A API estará disponível em `http://localhost:8000` e a documentação interativa (Swagger UI) em `http://localhost:8000/docs`.

6.  **Execute os testes:**
    ```bash
    pytest -v
    ```
    Os testes usarão um banco de dados SQLite em arquivo (`./test_db.db`) que é criado e destruído automaticamente.

## Funcionalidades Principais

*   Autenticação de usuários (registro e login com JWT).
*   CRUD completo para Clientes (requer superusuário para criar/atualizar/deletar).
*   CRUD completo para Produtos (requer superusuário para criar/atualizar/deletar).
*   Criação e consulta de Pedidos (usuários autenticados podem criar, superusuários podem deletar).
*   Validação de dados com Pydantic.
*   Interação com banco de dados via SQLAlchemy ORM.
*   Estrutura organizada em camadas (endpoints, services, models, schemas).
*   Testes automatizados abrangentes.


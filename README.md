# API de Monitoramento de Usinas Fotovoltaicas

API para monitoramento de usinas fotovoltaicas, permitindo ingestão, armazenamento e análise de dados operacionais.

## Visão Geral

Este projeto implementa uma API REST para:
- Gerenciar usinas fotovoltaicas e seus inversores
- Ingerir dados de medições dos inversores (potência ativa, temperatura)
- Calcular métricas de geração de energia
- Fornecer insights operacionais através de agregações e análises

## Estrutura do Projeto

```
backend/
├── app/                      # Código principal da aplicação
│   ├── api/                  # Endpoints da API
│   ├── core/                 # Configurações centrais
│   ├── crud/                 # Operações CRUD
│   ├── models/               # Modelos do banco de dados
│   ├── schemas/              # Schemas Pydantic
│   └── workers/              # Processamento assíncrono
├── scripts/                  # Scripts utilitários
└── requirements.txt          # Dependências

frontend/                     # Interface de usuário
```

## Decisões Arquiteturais

### API REST com FastAPI
- Escolhido pela alta performance e facilidade de desenvolvimento
- Documentação automática com OpenAPI
- Validação com Pydantic

### Processamento Assíncrono
- RabbitMQ para enfileiramento de tarefas
- Worker para processamento em background das agregações e análises
- Adequado para cálculos complexos que não devem bloquear as respostas HTTP

### Banco de Dados
- SQLAlchemy como ORM
- Modelos relacionais para usinas, inversores e medições
- Persistência em SQLite para facilidade de implantação (configurável para outros SGBD)

### Agregações
- Processamento assíncrono para cálculos intensivos
- Resultados armazenados em formato JSON para consultas rápidas
- Endpoints para consulta de resultados já processados

## Requisitos

- Python 3.8+
- RabbitMQ
- Dependências listadas em requirements.txt

## Instruções de Execução

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repositório>
cd desafio-back-end-STEMIS

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r backend/requirements.txt
```

### 2. Configuração do RabbitMQ

Certifique-se que o RabbitMQ está instalado e em execução:

```bash
# Em sistemas baseados em Debian/Ubuntu
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server

# No Windows, baixe e instale de https://www.rabbitmq.com/download.html
```

### 3. Populando o Banco de Dados

```bash
# Execute o script para popular o banco com dados de amostra
cd backend
python -m scripts.popula_banco
```

### 4. Iniciando o Worker

```bash
# Em um terminal separado
cd backend
python -m app.workers.worker
```

### 5. Iniciando a API

```bash
# Em outro terminal
cd backend
uvicorn app.main:app --reload
```

A API estará disponível em: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs

## Fluxos Sugeridos

### 1. Visualização Básica dos Dados

1. Consulte a lista de usinas: `GET /usinas`
2. Visualize os inversores de uma usina: `GET /inversores?usina_id=1`
3. Consulte medições de um inversor: `GET /medicoes?inversor_id=1&limit=10`

### 2. Ingestão de Novos Dados

1. Faça upload de um arquivo JSON com novas medições: `POST /ingestao/arquivo`
2. Aguarde o processamento assíncrono
3. Verifique as novas medições: `GET /medicoes?limit=10`

### 3. Análise de Desempenho

1. Solicite cálculo de potência máxima: 
   ```
   POST /agregacao/potencia_maxima
   {
     "inversor_id": 1,
     "data_inicio": "2023-01-01T00:00:00",
     "data_fim": "2023-01-31T23:59:59"
   }
   ```
2. Solicite cálculo de geração da usina:
   ```
   POST /agregacao/geracao_usina
   {
     "usina_id": 1,
     "data_inicio": "2023-01-01T00:00:00",
     "data_fim": "2023-01-31T23:59:59"
   }
   ```
3. Consulte os resultados: `GET /agregacao/resultados`

### 4. Geração do Dashboard Completo

1. Solicite geração de dashboard para período específico:
   ```
   POST /agregacao/gerar_dash
   {
     "data_inicio": "2023-01-01T00:00:00",
     "data_fim": "2023-01-31T23:59:59"
   }
   ```
2. Consulte o dashboard gerado: `GET /agregacao/dash`

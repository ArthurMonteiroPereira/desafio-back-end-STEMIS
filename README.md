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
- Persistência em PostgreSQL para robustez e escalabilidade

### Agregações
- Processamento assíncrono para cálculos intensivos
- Resultados armazenados em formato JSON para consultas rápidas
- Endpoints para consulta de resultados já processados

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- RabbitMQ
- Dependências listadas em requirements.txt

## Instruções de Execução

### 1. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repositório>
cd desafio-back-end-STEMIS

# Crie e ative um ambiente virtual
conda create -n usinas_fotovoltaicas python=3.13.2
conda activate usinas_fotovoltaicas  # Mesmo comando para Windows e Linux/Mac

# Instale as dependências
pip install -r backend/requirements.txt
```

### 2. Configuração do PostgreSQL

1. Instale o PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # Windows: Baixe e instale de https://www.postgresql.org/download/windows/
   ```

2. Crie um banco de dados para o projeto:
   ```bash
   sudo -u postgres psql
   
   # No console do PostgreSQL
   CREATE DATABASE usinas_db;

   ```

3. Configure as variáveis de ambiente de acesso ao banco:
    se criou um banco padrao postgreSQL utilize o .env de exemplo

### 3. Configuração do RabbitMQ

Certifique-se que o RabbitMQ está instalado e em execução:

```bash
# Em sistemas baseados em Debian/Ubuntu
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server

# No Windows, baixe e instale de https://www.rabbitmq.com/download.html
```

### 4. Populando o Banco de Dados
Use a interface front para popular com json desejado ou o script para popular com json de amostra fornecido no desafio
```bash
# Execute o script para popular o banco com dados de amostra
cd backend
python -m scripts.popula_banco
```

### 5. Iniciando o Worker

```bash
# Em um terminal separado
cd backend
python -m app.workers.worker
```

### 6. Iniciando a API

```bash
# Em outro terminal
cd backend
uvicorn app.main:app --reload
```

A API estará disponível em: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs

### 6. Iniciando o Front

```bash
streamlit run .\frontend\app.py
```
acesse:  http://localhost:8501 para vizualizar o dashboard

## Dicas

1. A pasta scripts contem um arquivo chamado gera_metrics_sintetico.py que pode ser executado separadamente para gerar um arquivo de medições factivel para melhorar o teste das soluções de analises baseadas em modelos de IA
2. Arquivos de mestricas gerados e fornecidos no desafio estão na pasta sample
3. Analises geradas estao nas pastas backend/workers/results_*
4. Modelos de IA gerados e treinados estao na pasta backend/workers/models
5. Para executar e testar tudo mantenha 3 terminais abertos:
    - um para executar o worker
    - um para executar a API
    - um para executar o front


## Considerações Finais e desenvolvimentos complementares futuros

1. Dockerizar tudo para facilitar a execução e teste do projeto.
2. Criar testes unitarios para validar o funcionamento das funcoes e endpoints da API
3. Criar um sistema de logging para facilitar a debugagem e monitoramento do projeto
## Fluxos Sugeridos
4. Front lento, usei o strealit so para testar tudo de maneira mais pratica, mas esta longe de ser o ideal.

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

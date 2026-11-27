# IAEmpreendedora

Site educativo sobre o uso da Inteligência Artificial na gestão e organização financeira.

## Objetivo

Promover educação financeira e conscientizar a comunidade sobre o uso da Inteligência Artificial nas finanças pessoais e na tomada de decisões.

O projeto contará com conteúdo educativo, formulário de participação, indicadores apresentados em gráficos e espaço para feedback dos visitantes.

## Tecnologias

- Frontend: React
- Backend: Python e Django
- Banco de dados: SQLite

## Executar o backend

Requisitos: Python 3.11 ou superior.

1. Acesse a pasta do backend:

   ```bash
   cd backend
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   ```

   Windows (PowerShell):

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. (Opcional) Crie o arquivo de variáveis de ambiente a partir do exemplo,
   caso precise alterar alguma configuração local:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Aplique as migrações e inicie o servidor:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

A API ficará disponível em http://127.0.0.1:8000.

## Testes

Na pasta `backend`, execute:

```bash
python manage.py test
```

O teste inicial verifica a rota de status da API em `/api/status/`.

## Estrutura do backend

```text
backend/
├── config/          # Configurações e rotas do projeto Django
├── formularios/     # Aplicativo responsável pelos formulários
├── manage.py
└── requirements.txt
```

O projeto utiliza SQLite em todos os ambientes. Por padrão, o banco fica em `backend/db.sqlite3`; em produção, o caminho é definido pela variável `SQLITE_DB_PATH`.

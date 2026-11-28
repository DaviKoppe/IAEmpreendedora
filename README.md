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

Requisitos: Python 3.11 ou superior e Git.

1. Clone o repositório e acesse a pasta do backend:

   ```bash
   git clone https://github.com/DaviKoppe/IAEmpreendedora.git
   cd IAEmpreendedora/backend
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
   caso precise alterar alguma configuração local. Sem ele, o projeto usa
   os valores de desenvolvimento.

   Windows (PowerShell):

   ```powershell
   Copy-Item .env.example .env
   ```

   Linux/macOS:

   ```bash
   cp .env.example .env
   ```

5. Aplique as migrações (cria o banco `backend/db.sqlite3`) e inicie o
   servidor:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

A API ficará disponível em http://127.0.0.1:8000.

## Testes

Na pasta `backend`, com o ambiente virtual ativado, execute:

```bash
python manage.py test
```

São 54 testes. Eles usam um banco temporário, criado e apagado a cada
execução, e não alteram o `db.sqlite3`.

| Arquivo | O que verifica |
|---|---|
| `formularios/tests.py` | rota de status, validação do questionário e CORS |
| `formularios/test_persistencia.py` | gravação das respostas, restrições de integridade, atomicidade e Django Admin |
| `formularios/test_consultas_r5.py` | consultas para o dashboard documentadas em `BANCO_DE_DADOS.md` |

## Estrutura do backend

```text
backend/
├── config/          # Configurações e rotas do projeto Django
├── formularios/     # Aplicativo do questionário: validação, modelos e gravação
├── API.md           # Contrato da API
├── BANCO_DE_DADOS.md
├── manage.py
└── requirements.txt
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [`backend/API.md`](backend/API.md) | endpoints, campos, alternativas aceitas e respostas da API |
| [`backend/BANCO_DE_DADOS.md`](backend/BANCO_DE_DADOS.md) | configuração do SQLite, modelo entidade-relacionamento, dicionário de dados, regras de integridade, gravação, consultas para o dashboard e hospedagem no Render |

O projeto utiliza SQLite em todos os ambientes. Por padrão, o banco fica em
`backend/db.sqlite3`; em produção, o caminho é definido pela variável
`SQLITE_DB_PATH`.

## Pendências de integração e produção

- **CSRF (frontend e API):** o Django exige token CSRF em requisições
  `POST`. Os testes automatizados não aplicam essa verificação, mas, com o
  servidor em execução, o envio do questionário feito pelo navegador sem o
  token recebe HTTP `403` e não é gravado. A solução precisa ser definida
  na integração entre o formulário e a API.
- **Armazenamento persistente:** no Render, o banco precisa ficar em um
  disco persistente, que só existe nos planos pagos. No plano gratuito,
  todas as respostas são perdidas a cada deploy ou reinício.
- **Configurações de produção:** servidor de aplicação, arquivos estáticos
  do Django Admin, HTTPS, variáveis de ambiente, criação do usuário
  administrativo e backup. Veja "Produção no Render" em
  `BANCO_DE_DADOS.md`.


## Executar o frontend

Requisitos: Node.js 18 ou superior e npm.

```bash
cd frontend
npm install
npm run dev
```

O frontend React/Vite apresenta as seções Início, Sobre, Conteúdo, Questionário (reserva para a etapa R3) e Resultados (reserva para os gráficos da etapa R5). A preferência entre tema claro e escuro é salva no navegador.

Consulte [frontend/README.md](frontend/README.md) para mais detalhes. O formulário e os gráficos ainda dependem da integração com a API e com os dados da pesquisa.

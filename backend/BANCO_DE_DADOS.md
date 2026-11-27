# Banco de dados

O IAEmpreendedora utiliza **SQLite** em todos os ambientes (desenvolvimento local e produção), por meio do Django ORM.

## Configuração

O caminho do arquivo do banco é definido pela variável de ambiente `SQLITE_DB_PATH`.

| Ambiente | `SQLITE_DB_PATH` | Arquivo utilizado |
|---|---|---|
| Desenvolvimento local | não definida | `backend/db.sqlite3` |
| Produção (Render) | **obrigatória**, por exemplo `/var/data/db.sqlite3` | arquivo no disco persistente |

- No Render (detectado pela variável `RENDER=true`, que a plataforma sempre define), a ausência de `SQLITE_DB_PATH` interrompe a inicialização com a mensagem `A variável SQLITE_DB_PATH não foi definida...`. Isso evita que o banco seja criado silenciosamente no armazenamento temporário do serviço.
- Caminhos relativos são resolvidos a partir da pasta `backend/`.
- A pasta indicada precisa existir; o Django cria apenas o arquivo do banco.
- As variáveis podem ser definidas no ambiente ou no arquivo `backend/.env` (veja `backend/.env.example`). Variáveis do ambiente têm prioridade sobre o `.env`.
- `backend/.env`, `db.sqlite3` e os arquivos auxiliares do SQLite (`db.sqlite3-journal`, `db.sqlite3-wal` e `db.sqlite3-shm`) são ignorados pelo Git e não devem ser versionados.

## Produção no Render

### Disco persistente (obrigatório)

O sistema de arquivos de um serviço do Render é **temporário**: tudo o que é gravado fora de um disco persistente é apagado a cada deploy ou reinício do serviço. Como o SQLite é um arquivo, o banco precisa ficar em um **Persistent Disk**.

- **Plano gratuito:** não oferece disco persistente. Nele, **todas as respostas do questionário serão perdidas** a cada deploy, reinício ou hibernação do serviço. O plano gratuito serve apenas para demonstração, nunca para coletar respostas reais. Para uma demonstração consciente dessa perda, defina explicitamente `SQLITE_DB_PATH=db.sqlite3`.
- **Plano pago:** adicione um disco ao Web Service (por exemplo, *Mount Path* `/var/data`) e defina `SQLITE_DB_PATH=/var/data/db.sqlite3`.
- Um serviço com disco roda em uma única instância e tem uma breve indisponibilidade durante cada deploy.

### Migrations

O disco persistente **não está acessível** durante o *Build Command* nem durante o *Pre-Deploy Command*, apenas quando o serviço é iniciado. Por isso, as migrations devem ser executadas no *Start Command*, antes de iniciar o servidor:

```bash
python manage.py migrate --noinput && <comando que inicia o servidor>
```

Se as migrations forem executadas no build, o Django criará as tabelas em um arquivo temporário, e o banco real no disco ficará sem elas.

### Variáveis de ambiente em produção

| Variável | Valor |
|---|---|
| `SQLITE_DB_PATH` | caminho do banco no disco persistente, por exemplo `/var/data/db.sqlite3` |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | chave longa e aleatória, exclusiva de produção |
| `DJANGO_ALLOWED_HOSTS` | domínio do serviço, por exemplo `iaempreendedora.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | endereço público do frontend |

As demais configurações gerais de produção do Django (servidor de aplicação, arquivos estáticos e HTTPS) são de responsabilidade de quem realizar o deploy.

### Cópia de segurança

Para preservar os dados, baixe periodicamente uma cópia do arquivo do banco a partir do disco persistente, preferencialmente com o serviço parado ou sem envios em andamento.

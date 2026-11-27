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

## Modelagem

As respostas ficam em duas tabelas, criadas pela migration `formularios/migrations/0001_initial.py`. Os modelos estão em `formularios/models.py`.

```text
formularios_respostaquestionario (1) ──< (N) formularios_beneficioresposta
```

Cada questionário enviado gera **uma** linha em `formularios_respostaquestionario` e **uma linha por benefício selecionado** em `formularios_beneficioresposta`. Não são armazenados dados pessoais (nome, e-mail ou IP).

### Dicionário de dados

**`formularios_respostaquestionario`** (modelo `RespostaQuestionario`)

| Coluna | Tipo no SQLite | Nulo | Regra |
|---|---|---|---|
| `id` | `integer`, chave primária | não | gerado automaticamente |
| `faixa_etaria` | `varchar(50)` | não | uma das alternativas de `OPCOES["faixa_etaria"]` |
| `conhecimento_financeiro` | `varchar(50)` | não | uma das alternativas de `OPCOES["conhecimento_financeiro"]` |
| `ferramenta_financeira` | `varchar(50)` | não | uma das alternativas de `OPCOES["ferramenta_financeira"]` |
| `uso_ia` | `varchar(50)` | não | uma das alternativas de `OPCOES["uso_ia"]` |
| `uso_ia_financas` | `varchar(50)` | não | uma das alternativas de `OPCOES["uso_ia_financas"]` |
| `confianca_ia` | `varchar(50)` | não | uma das alternativas de `OPCOES["confianca_ia"]` |
| `interesse_ia` | `varchar(50)` | não | uma das alternativas de `OPCOES["interesse_ia"]` |
| `feedback` | `text` | não | opcional na API; gravado como `""` quando omitido; até 1000 caracteres |
| `criado_em` | `datetime` (UTC), com índice | não | data e hora do envio, preenchida automaticamente |

**`formularios_beneficioresposta`** (modelo `BeneficioResposta`)

| Coluna | Tipo no SQLite | Nulo | Regra |
|---|---|---|---|
| `id` | `integer`, chave primária | não | gerado automaticamente |
| `resposta_id` | `bigint`, chave estrangeira, com índice | não | referencia `formularios_respostaquestionario.id` |
| `beneficio` | `varchar(50)` | não | uma das alternativas de `OPCOES["beneficios_ia"]` |

Os nomes das colunas são os mesmos do contrato da API (`API.md`), e as respostas são gravadas com o texto exato da alternativa escolhida.

### Restrições de integridade

As alternativas válidas vêm do dicionário `OPCOES` de `formularios/validators.py`, que é a fonte única de verdade. Os modelos as utilizam tanto nos `choices` quanto nas restrições do banco. Como o SQLite não aplica o tamanho de `varchar`, as regras abaixo são as que de fato protegem os dados, independentemente de a gravação vir da API, do shell do Django ou de um script. O Django Admin não grava nem exclui dados, pois é somente leitura.

| Restrição | Tabela | Garante |
|---|---|---|
| `formularios_<campo>_valido` (`CHECK ... IN (...)`), uma por campo | respostas | só alternativas válidas, com acentos e maiúsculas exatos; texto vazio é recusado |
| `formularios_feedback_tamanho_maximo` (`CHECK LENGTH(feedback) <= 1000`) | respostas | feedback com no máximo 1000 caracteres |
| `formularios_beneficio_valido` (`CHECK ... IN (...)`) | benefícios | só benefícios válidos |
| `formularios_beneficio_unico_por_resposta` (`UNIQUE (resposta_id, beneficio)`) | benefícios | o mesmo benefício não se repete na mesma resposta |
| chave estrangeira `resposta_id` | benefícios | não existe benefício sem resposta |
| `NOT NULL` em todas as colunas | ambas | nenhum campo fica sem valor |

Duas regras ficam **apenas na aplicação**, no validador do R3, porque no banco exigiriam *triggers*: pelo menos um benefício por resposta e a exclusividade da opção `Não vejo benefícios`. A gravação atômica garante que uma resposta nunca fique salva sem os benefícios enviados.

### Gravação atômica

A função `salvar_respostas` (`formularios/persistencia.py`) é chamada pelo endpoint `POST /api/questionario/` somente depois da validação. Ela grava a resposta e os benefícios dentro de `transaction.atomic()`: se qualquer gravação falhar, tudo é desfeito e nenhuma linha fica no banco.

### Exclusão em cascata: Django × SQL

O modelo usa `on_delete=models.CASCADE`, mas **essa cascata é feita pelo Django, não pelo banco**:

- **Pelo Django ORM** (`resposta.delete()`, `QuerySet.delete()`, shell do Django): o Django apaga primeiro os benefícios relacionados e depois a resposta.
- **Por SQL direto** (`DELETE FROM formularios_respostaquestionario ...`): a chave estrangeira criada no banco **não** tem `ON DELETE CASCADE` (a regra é `NO ACTION`). Se a resposta tiver benefícios, o SQLite recusa a exclusão com erro de chave estrangeira. Para excluir por SQL, apague antes as linhas de `formularios_beneficioresposta`.

A verificação de chaves estrangeiras do SQLite é ativada por conexão. O Django a ativa automaticamente, mas ferramentas externas (o programa `sqlite3`, o DB Browser for SQLite etc.) começam com ela desligada. Antes de alterar dados por fora do Django, execute `PRAGMA foreign_keys = ON;`.

### Consulta pelo Django Admin

As respostas podem ser consultadas em `/admin/` por um usuário da equipe (crie um com `python manage.py createsuperuser`). O admin é **somente leitura**: lista as respostas com filtros por alternativa, benefício e data, e mostra o feedback e os benefícios apenas na página de detalhe de cada resposta. Não é possível incluir, alterar nem excluir respostas por ele.

### Como alterar alternativas sem comprometer o histórico

As alternativas válidas ficam gravadas nas restrições do banco. Por isso, **toda mudança em `OPCOES` exige uma nova migration** (`python manage.py makemigrations formularios`), e o teste `test_nao_ha_migrations_pendentes` falha enquanto ela não for criada.

| Mudança | O que fazer |
|---|---|
| **Incluir** uma alternativa | Alterar `OPCOES`, gerar a migration e aplicar. Os dados antigos não são afetados. |
| **Corrigir o texto** de uma alternativa | Seguir o procedimento abaixo. |
| **Remover** uma alternativa | Decidir antes, com a equipe, o destino das respostas antigas. Para convertê-las em outra alternativa, seguir o procedimento abaixo, com o `UPDATE` apontando para a alternativa escolhida. Manter a alternativa válida só para o histórico exigiria separar a lista do formulário da lista do banco, o que é uma mudança de modelagem. |

#### Procedimento para corrigir o texto de uma alternativa

Exemplo: trocar `Talvez` por `Talvez futuramente` em `interesse_ia`. Há duas armadilhas:

- **Atualizar os dados antes** não funciona: a restrição antiga só aceita `Talvez`, então o `UPDATE` para o texto novo é recusado (`CHECK constraint failed`).
- **Aplicar a nova restrição antes** também não funciona: ao recriar a tabela, o SQLite copia as linhas antigas com `Talvez`, que violam a nova regra, e a migration falha.

A sequência correta, dentro de **uma única migration**, é:

1. Alterar o texto em `OPCOES` (`validators.py`) e executar `python manage.py makemigrations formularios -n renomeia_talvez`. O Django gera, nesta ordem: `RemoveConstraint` (remove a restrição antiga), `AlterField` (atualiza os `choices`) e `AddConstraint` (cria a restrição nova).
2. Editar a migration gerada e inserir um `RunSQL` **entre o `AlterField` e o `AddConstraint`**, de modo que os dados sejam convertidos quando nenhuma restrição está ativa:

   ```python
   migrations.RunSQL(
       sql=(
           "UPDATE formularios_respostaquestionario "
           "SET interesse_ia = 'Talvez futuramente' "
           "WHERE interesse_ia = 'Talvez'"
       ),
       reverse_sql=(
           "UPDATE formularios_respostaquestionario "
           "SET interesse_ia = 'Talvez' "
           "WHERE interesse_ia = 'Talvez futuramente'"
       ),
   ),
   ```

   Para benefícios, a tabela é `formularios_beneficioresposta` e a coluna é `beneficio`. Se o texto novo já existir na mesma resposta, o `UPDATE` violaria `formularios_beneficio_unico_por_resposta`; nesse caso, apague antes a linha duplicada.
3. Testar em uma cópia do banco e só então executar `python manage.py migrate`. A migration é atômica: se qualquer passo falhar, nada é alterado. O `reverse_sql` permite desfazê-la com `python manage.py migrate formularios <migration anterior>`.

Esse procedimento foi validado em uma cópia isolada do banco: o `UPDATE` com a restrição antiga foi recusado, a migration sem o `RunSQL` falhou, e a migration com o `RunSQL` foi aplicada e revertida com sucesso.

Essas mudanças afetam o R3 (formulário e validação), o R4 (banco) e o R5 (dashboard), e devem ser combinadas entre os três. Ao alterar alternativas, atualize também `API.md` e os testes.

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

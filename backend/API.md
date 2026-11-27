# Documentação da API

Esta documentação descreve os endpoints disponíveis no backend Django do IAEmpreendedora.

## Endereço local

Com o servidor Django em execução, a API fica disponível em:

```text
http://127.0.0.1:8000
```

Para iniciar o servidor, na pasta `backend`:

```powershell
python manage.py runserver
```

## Endpoints

### 1. Verificar o status da API

- **Método:** `GET`
- **Rota:** `/api/status/`
- **Descrição:** verifica se a API está respondendo.

Exemplo de resposta — HTTP `200`:

```json
{
  "status": "ok",
  "mensagem": "API do IAEmpreendedora funcionando."
}
```

### 2. Enviar respostas do questionário

- **Método:** `POST`
- **Rota:** `/api/questionario/`
- **Tipo de conteúdo:** `application/json`
- **Descrição:** recebe e valida as respostas do questionário.

Cabeçalho necessário:

```http
Content-Type: application/json
```

#### Corpo da requisição

Envie um objeto JSON com os campos abaixo. Os textos das alternativas devem corresponder exatamente aos valores aceitos pela API.

```json
{
  "faixa_etaria": "18 a 24 anos",
  "conhecimento_financeiro": "Moderado",
  "ferramenta_financeira": "Planilhas",
  "uso_ia": "Algumas vezes",
  "uso_ia_financas": "Tirar dúvidas financeiras",
  "beneficios_ia": [
    "Organização de gastos",
    "Planejamento financeiro"
  ],
  "confianca_ia": "Confiança moderada",
  "interesse_ia": "Sim",
  "feedback": "Gostei da iniciativa."
}
```

#### Campos e alternativas aceitas

| Campo | Tipo | Valores aceitos |
|---|---|---|
| `faixa_etaria` | Texto | Menos de 18 anos; 18 a 24 anos; 25 a 34 anos; 35 a 44 anos; 45 a 59 anos; 60 anos ou mais |
| `conhecimento_financeiro` | Texto | Muito baixo; Baixo; Moderado; Alto; Muito alto |
| `ferramenta_financeira` | Texto | Aplicativos financeiros; Planilhas; Anotações ou caderno; Não utilizo nenhuma ferramenta |
| `uso_ia` | Texto | Frequentemente; Algumas vezes; Já testei, mas quase não utilizo; Nunca utilizei |
| `uso_ia_financas` | Texto | Organizar gastos; Planejamento financeiro; Tirar dúvidas financeiras; Outras atividades; Nunca utilizei |
| `beneficios_ia` | Lista de textos | Organização de gastos; Planejamento financeiro; Identificação de desperdícios; Auxílio na tomada de decisões; Educação financeira; Não vejo benefícios |
| `confianca_ia` | Texto | Nenhuma confiança; Pouca confiança; Confiança moderada; Muita confiança; Confio totalmente |
| `interesse_ia` | Texto | Sim; Talvez; Não |
| `feedback` | Texto (opcional) | Até 1000 caracteres |

**Regras importantes:**
- Todos os campos, exceto `feedback`, são obrigatórios.
- `beneficios_ia` deve ser uma lista com pelo menos uma opção válida, sem itens repetidos.
- A opção `Não vejo benefícios` não pode ser enviada junto com outros benefícios.
- `feedback` pode ser omitido ou enviado como texto vazio.

#### Resposta de sucesso

Quando todas as respostas são válidas, a API retorna HTTP `201`:

```json
{
  "status": "ok",
  "mensagem": "Respostas validadas com sucesso."
}
```

#### Resposta de erro

Quando o JSON é inválido ou há campos/respostas inválidos, a API retorna HTTP `400`.

Exemplo:

```json
{
  "status": "erro",
  "mensagem": "Existem respostas inválidas.",
  "erros": {
    "faixa_etaria": "Selecione uma das opções válidas.",
    "feedback": "O feedback deve ter no máximo 1000 caracteres."
  }
}
```

O objeto `erros` identifica os campos que precisam ser corrigidos. Se o corpo não for um JSON válido, a resposta será:

```json
{
  "status": "erro",
  "mensagem": "O corpo da requisição deve conter um JSON válido."
}
```

Se o endpoint for chamado com outro método que não seja `POST`, a API retorna HTTP `405`.

## Integração com o frontend (Vite)

Durante o desenvolvimento local, o backend permite requisições originadas de:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

Exemplo de envio usando `fetch` no React:

```javascript
const resposta = await fetch("http://127.0.0.1:8000/api/questionario/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(respostas),
});

const resultado = await resposta.json();

if (!resposta.ok) {
  console.error("Erro ao enviar questionário:", resultado);
} else {
  console.log("Questionário validado:", resultado);
}
```

## Observação sobre o armazenamento

As respostas válidas são armazenadas no banco de dados SQLite. A gravação acontece somente depois da validação e é atômica: o questionário e os benefícios selecionados são salvos juntos, ou nada é salvo. Respostas inválidas (HTTP `400`) não são armazenadas.

O formato das requisições e das respostas da API não mudou. A estrutura das tabelas está descrita em `BANCO_DE_DADOS.md`.

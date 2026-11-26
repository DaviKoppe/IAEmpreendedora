"""Validação das respostas do questionário de participação."""

OPCOES = {
    "faixa_etaria": [
        "Menos de 18 anos",
        "18 a 24 anos",
        "25 a 34 anos",
        "35 a 44 anos",
        "45 a 59 anos",
        "60 anos ou mais",
    ],
    "conhecimento_financeiro": [
        "Muito baixo",
        "Baixo",
        "Moderado",
        "Alto",
        "Muito alto",
    ],
    "ferramenta_financeira": [
        "Aplicativos financeiros",
        "Planilhas",
        "Anotações ou caderno",
        "Não utilizo nenhuma ferramenta",
    ],
    "uso_ia": [
        "Frequentemente",
        "Algumas vezes",
        "Já testei, mas quase não utilizo",
        "Nunca utilizei",
    ],
    "uso_ia_financas": [
        "Organizar gastos",
        "Planejamento financeiro",
        "Tirar dúvidas financeiras",
        "Outras atividades",
        "Nunca utilizei",
    ],
    "beneficios_ia": [
        "Organização de gastos",
        "Planejamento financeiro",
        "Identificação de desperdícios",
        "Auxílio na tomada de decisões",
        "Educação financeira",
        "Não vejo benefícios",
    ],
    "confianca_ia": [
        "Nenhuma confiança",
        "Pouca confiança",
        "Confiança moderada",
        "Muita confiança",
        "Confio totalmente",
    ],
    "interesse_ia": [
        "Sim",
        "Talvez",
        "Não",
    ],
}

CAMPOS_OBRIGATORIOS = tuple(OPCOES)


def validar_respostas(dados):
    """Retorna um dicionário de erros; vazio quando todas as respostas são válidas."""
    erros = {}

    if not isinstance(dados, dict):
        return {"formulario": "O corpo da requisição deve ser um objeto JSON."}

    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            erros[campo] = "Este campo é obrigatório."
            continue

        valor = dados[campo]

        if campo == "beneficios_ia":
            if not isinstance(valor, list) or not valor:
                erros[campo] = "Selecione pelo menos um benefício."
                continue

            if any(not isinstance(item, str) or item not in OPCOES[campo] for item in valor):
                erros[campo] = "Uma ou mais opções selecionadas são inválidas."
                continue

            if len(valor) != len(set(valor)):
                erros[campo] = "Não repita opções."
            elif "Não vejo benefícios" in valor and len(valor) > 1:
                erros[campo] = "A opção 'Não vejo benefícios' não pode ser combinada."
        elif not isinstance(valor, str) or valor not in OPCOES[campo]:
            erros[campo] = "Selecione uma das opções válidas."

    feedback = dados.get("feedback", "")
    if not isinstance(feedback, str):
        erros["feedback"] = "O feedback deve ser um texto."
    elif len(feedback) > 1000:
        erros["feedback"] = "O feedback deve ter no máximo 1000 caracteres."

    return erros

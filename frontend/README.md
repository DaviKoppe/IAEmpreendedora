# Frontend — IA Empreendedora

Interface educativa em React + Vite para o projeto IA Empreendedora.

## Requisitos
- Node.js 18 ou superior
- npm

## Executar localmente
```bash
cd frontend
npm install
npm run dev
```

Para gerar a versão de produção:
```bash
npm run build
npm run preview
```

## Estrutura atual
- **Início:** apresentação do projeto.
- **Sobre:** objetivo e proposta educativa.
- **Conteúdo:** usos da IA na organização e educação financeira.
- **Questionário:** espaço reservado para integração do formulário da etapa R3.
- **Resultados:** espaço reservado para os gráficos da etapa R5.

O seletor de tema claro/escuro salva a preferência no navegador. O formulário e os gráficos são áreas de integração visual; ainda não estão conectados à API ou aos dados da pesquisa.

## Integração futura
A API Django existente está na pasta `backend/`. A integração do formulário deverá seguir o contrato documentado em `backend/API.md`, incluindo a estratégia de CSRF. Os gráficos deverão consumir as consultas documentadas em `backend/BANCO_DE_DADOS.md`.

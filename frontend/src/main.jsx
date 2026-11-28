import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Erro ao renderizar a aplicação:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main style={{ padding: 24, fontFamily: 'Arial, sans-serif', color: '#8b1e1e' }}>
          <h1>Erro ao carregar a aplicação</h1>
          <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
            {String(this.state.error?.stack || this.state.error)}
          </pre>
          <p>Envie uma captura desta mensagem para identificar a correção.</p>
        </main>
      );
    }

    return this.props.children;
  }
}

const rootElement = document.getElementById('root');

if (!rootElement) {
  document.body.innerHTML = '<pre style="padding:24px;color:#8b1e1e">Erro: elemento #root não encontrado em index.html.</pre>';
} else {
  window.addEventListener('error', (event) => {
    console.error('Erro JavaScript:', event.message, event.filename, event.lineno);
  });

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Promise rejeitada:', event.reason);
  });

  createRoot(rootElement).render(
    <AppErrorBoundary>
      <React.StrictMode><App /></React.StrictMode>
    </AppErrorBoundary>
  );
}

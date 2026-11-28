import { useEffect, useState } from 'react';
import {
  ArrowDown, ArrowRight, ArrowUpRight, BarChart3, BrainCircuit, Check,
  ChevronRight, CircleDollarSign, GraduationCap, Lightbulb, Menu, Moon,
  ShieldCheck, Sparkles, Sun, Wallet, X
} from 'lucide-react';

const navItems = [
  ['Início', '#inicio'], ['Sobre', '#sobre'], ['Conteúdo', '#conteudo'],
  ['Questionário', '#questionario'], ['Resultados', '#resultados']
];

function App() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('ia-empreendedora-theme') || 'light'; }
    catch { return 'light'; }
  });
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('ia-empreendedora-theme', theme); } catch {}
  }, [theme]);

  const toggleTheme = () => setTheme(current => current === 'light' ? 'dark' : 'light');

  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="IA Empreendedora - início">
          <span className="brand-mark"><BrainCircuit size={23} /></span>
          <span>IA <b>Empreendedora</b></span>
        </a>
        <button className="mobile-menu icon-button" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}>
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <nav className={menuOpen ? 'navigation navigation-open' : 'navigation'} aria-label="Navegação principal">
          {navItems.map(([label, href]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}</a>)}
        </nav>
        <button className="theme-toggle" onClick={toggleTheme} aria-label={theme === 'light' ? 'Ativar modo escuro' : 'Ativar modo claro'}>
          {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
          <span>{theme === 'light' ? 'Modo escuro' : 'Modo claro'}</span>
        </button>
      </header>

      <main>
        <section className="hero section-wrap" id="inicio">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-dot" /> EDUCAÇÃO FINANCEIRA + INTELIGÊNCIA ARTIFICIAL</div>
            <h1>Suas finanças mais <span>inteligentes.</span></h1>
            <p className="hero-lead">Descubra como a inteligência artificial pode transformar a maneira como você organiza seu dinheiro e toma decisões no dia a dia.</p>
            <div className="hero-actions">
              <a className="button button-primary" href="#conteudo">Explore o conteúdo <ArrowRight size={17} /></a>
              <a className="text-link" href="#sobre">Conheça o projeto <ArrowUpRight size={16} /></a>
            </div>
            <div className="hero-note"><ShieldCheck size={17} /> Informação para escolhas mais conscientes.</div>
          </div>
          <div className="hero-art" aria-label="Ilustração de organização financeira com inteligência artificial">
            <div className="art-glow" />
            <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
            <div className="finance-card">
              <div className="finance-card-top"><span className="mini-icon"><Wallet size={17} /></span><span className="card-label">VISÃO FINANCEIRA</span><span className="status-dot" /></div>
              <div className="card-title">Organize. Entenda. Evolua.</div>
              <div className="chart-bars"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
              <div className="chart-caption"><span>Planejamento</span><span className="chart-caption-value">Passo a passo</span></div>
            </div>
            <div className="floating-chip chip-ai"><Sparkles size={16} /><span>IA como aliada</span></div>
            <div className="floating-chip chip-money"><CircleDollarSign size={17} /><span>Decisões conscientes</span></div>
            <div className="art-caption">Tecnologia a favor da sua vida financeira</div>
          </div>
          <a href="#sobre" className="scroll-cue" aria-label="Rolar para sobre"><ArrowDown size={17} /></a>
        </section>

        <section className="intro-section section-wrap" id="sobre">
          <div className="section-kicker">01 / SOBRE O PROJETO</div>
          <div className="intro-grid">
            <div><h2>Conhecimento financeiro para um <span>futuro melhor.</span></h2></div>
            <div className="intro-text"><p>O IA Empreendedora é um projeto educativo que busca aproximar a inteligência artificial da educação financeira, mostrando como essas ferramentas podem apoiar a organização das finanças pessoais e a tomada de decisões.</p><p>Nosso objetivo é incentivar o uso consciente da tecnologia, tornando o conhecimento mais acessível e útil para a comunidade.</p></div>
          </div>
          <div className="values-grid">
            <article className="value-card"><span className="value-icon"><GraduationCap /></span><h3>Aprender</h3><p>Conceitos explicados de forma simples e acessível.</p></article>
            <article className="value-card"><span className="value-icon"><ShieldCheck /></span><h3>Usar com consciência</h3><p>Entenda possibilidades, limites e cuidados ao usar IA.</p></article>
            <article className="value-card"><span className="value-icon"><Lightbulb /></span><h3>Decidir melhor</h3><p>Transforme informação em escolhas mais conscientes.</p></article>
          </div>
        </section>

        <section className="content-section" id="conteudo">
          <div className="section-wrap">
            <div className="section-kicker">02 / CONTEÚDO</div>
            <div className="section-heading-row"><div><h2>Inteligência artificial no <span>seu dia a dia.</span></h2><p>Conheça formas práticas de usar a tecnologia como apoio à sua organização financeira.</p></div><span className="heading-decoration"><BrainCircuit size={35} /></span></div>
            <div className="topic-grid">
              <article className="topic-card topic-featured"><div className="topic-top"><span className="topic-icon"><Wallet /></span><span className="topic-number">01</span></div><h3>Organização financeira</h3><p>Use ferramentas digitais para categorizar despesas, visualizar hábitos de consumo e estruturar um orçamento.</p><span className="topic-tag">Planejamento</span></article>
              <article className="topic-card"><div className="topic-top"><span className="topic-icon"><BarChart3 /></span><span className="topic-number">02</span></div><h3>Análise de gastos</h3><p>Aprenda a interpretar informações financeiras e identificar oportunidades de melhorar seu planejamento.</p><span className="topic-tag">Análise</span></article>
              <article className="topic-card"><div className="topic-top"><span className="topic-icon"><BrainCircuit /></span><span className="topic-number">03</span></div><h3>IA como assistente</h3><p>Descubra como fazer perguntas melhores e utilizar assistentes de IA como apoio à educação financeira.</p><span className="topic-tag">Inteligência artificial</span></article>
            </div>
            <div className="notice"><ShieldCheck size={19} /><p><b>Importante:</b> a IA pode apoiar seu aprendizado, mas não substitui análise crítica nem orientação profissional. Nunca compartilhe senhas ou dados bancários sensíveis.</p></div>
          </div>
        </section>

        <section className="survey-section section-wrap" id="questionario">
          <div className="section-kicker">03 / PARTICIPE</div>
          <div className="survey-panel">
            <div className="survey-icon"><GraduationCap size={28} /></div>
            <div className="survey-copy"><span className="panel-label">SUA PARTICIPAÇÃO É IMPORTANTE</span><h2>Queremos conhecer sua experiência.</h2><p>Esta área será dedicada ao questionário do projeto. Em breve, você poderá compartilhar suas percepções sobre educação financeira e inteligência artificial.</p><span className="coming-soon"><span /> Formulário da etapa R3 será integrado aqui</span></div>
            <div className="survey-side"><span className="survey-outline">R3</span><span className="survey-side-label">QUESTIONÁRIO</span></div>
          </div>
        </section>

        <section className="results-section section-wrap" id="resultados">
          <div className="section-kicker">04 / RESULTADOS</div>
          <div className="results-panel">
            <div className="results-copy"><span className="panel-label">DADOS E DESCOBERTAS</span><h2>O que os dados nos mostram?</h2><p>Os resultados da pesquisa serão apresentados aqui de forma visual e acessível, com gráficos e indicadores para facilitar a compreensão das respostas.</p><span className="coming-soon"><span /> Gráficos da etapa R5 serão adicionados aqui</span></div>
            <div className="placeholder-chart"><div className="placeholder-chart-head"><span>VISUALIZAÇÃO DOS RESULTADOS</span><BarChart3 size={18} /></div><div className="placeholder-chart-body"><div className="chart-y-labels"><span>100%</span><span>75%</span><span>50%</span><span>25%</span></div><div className="placeholder-plot"><div className="plot-grid"><i /><i /><i /><i /></div><div className="plot-bars"><i /><i /><i /><i /><i /></div></div></div><div className="placeholder-x-labels"><span>Categoria 1</span><span>Categoria 2</span><span>Categoria 3</span><span>Categoria 4</span><span>Categoria 5</span></div><div className="chart-overlay">Os dados da pesquisa aparecerão aqui</div></div>
          </div>
        </section>

        <section className="closing-section section-wrap"><div className="closing-mark"><Sparkles size={20} /></div><h2>O primeiro passo para mudar é <span>aprender.</span></h2><p>Explore, questione e descubra novas possibilidades para cuidar melhor das suas finanças.</p><a className="button button-light" href="#inicio">Voltar ao início <ArrowUpRight size={16} /></a></section>
      </main>

      <footer className="footer"><a className="brand footer-brand" href="#inicio"><span className="brand-mark"><BrainCircuit size={20} /></span><span>IA <b>Empreendedora</b></span></a><span>Educação financeira e tecnologia para todos.</span><a href="#inicio">Voltar ao topo ↑</a></footer>
    </div>
  );
}

export default App;
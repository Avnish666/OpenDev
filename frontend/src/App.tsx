import { PublicExpensePage } from './components/Transparency';
import { FundingHistory, FundingReturn } from './pages/Funding';
import { lazy, Suspense, useEffect, useState } from 'react';
import GitHubLogin from './components/auth/GithubLogin';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/theme';
import { ProjectForm, ProjectList, ProjectPage } from './pages/Projects';
import Icon from './components/Icon';
import './App.css';
import './design/product.css';

const links = [['#/explore', 'Explore Projects'], ['#/analytics', 'Analytics'], ['#/my', 'My Projects'], ['#/history', 'My Funding & Rewards']];
const MaintainerProfile = lazy(() => import('./pages/Maintainer'));
export default function App() {
  const [path, setPath] = useState(window.location.hash || '#/explore');
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, loading } = useAuth();
  const { theme, toggleTheme } = useTheme();
  useEffect(() => { const change = () => { setPath(window.location.hash || '#/explore'); setMenuOpen(false); }; window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change); }, []);
  useEffect(() => {
    if (!menuOpen) return;
    document.querySelector<HTMLAnchorElement>('#main-navigation a')?.focus();
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') { setMenuOpen(false); document.querySelector<HTMLButtonElement>('.menu-toggle')?.focus(); } };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [menuOpen]);
  const route = path.split('?')[0];
  const maintainer = route.match(/^#\/maintainers\/(\d+)$/);
  const expense = route.match(/^#\/projects\/(\d+)\/expenses\/(\d+)$/);
  const match = route.match(/^#\/projects\/(\d+)(?:\/(?:roadmap|analytics))?$/);
  return <div className="app-shell">
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a>
    <header className="site-header"><div className="header-inner">
      <a href="#/explore" className="brand" aria-label="OpenDev home"><span className="brand-mark"><Icon name="code" size={25} /></span>OpenDev<span className="brand-dot">.</span></a>
      <nav id="main-navigation" className={`main-nav ${menuOpen ? 'is-open' : ''}`} aria-label="Main navigation">{links.map(([href, label]) => <a key={href} href={href} aria-current={route === href || (href === '#/analytics' && route.endsWith('/analytics')) || (href === '#/explore' && !!match && !route.endsWith('/analytics')) ? 'page' : undefined}>{label}</a>)}<a href="#/create" className="mobile-create" aria-current={route === '#/create' ? 'page' : undefined}>Create Project <span aria-hidden="true">+</span></a></nav>
      <div className="header-actions"><button className="theme-toggle secondary" type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} aria-pressed={theme === 'dark'} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}><span className="theme-glyph" key={theme}><Icon name={theme === 'light' ? 'moon' : 'sun'} /></span></button><GitHubLogin /><a className="button create-link" href="#/create" aria-current={route === '#/create' ? 'page' : undefined}>Create Project <span aria-hidden="true">+</span></a><button className="menu-toggle secondary" type="button" aria-expanded={menuOpen} aria-controls="main-navigation" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setMenuOpen(!menuOpen)}><Icon name={menuOpen ? 'close' : 'menu'} /></button></div>
    </div></header>
    <main id="main-content" className="page-container" tabIndex={-1}>
      {loading ? <div className="empty-state" role="status"><span className="loading-dot" />Checking session…</div> : (route === '#/my' || route === '#/create' || route === '#/history' || route.startsWith('#/funding-')) && !user ? <section className="sign-in-panel"><span className="feature-icon"><Icon name="github" size={30} /></span><p className="eyebrow">YOUR OPEN-SOURCE JOURNEY</p><h1>Good things start<br />with a connection.</h1><p>Sign in with GitHub to manage projects.</p><p className="muted">Create a campaign, back a maintainer, and keep track of your rewards.</p><GitHubLogin /><a href="#/explore">Explore public projects <Icon name="arrow" size={16} /></a></section> : route === '#/history' ? <FundingHistory /> : route.startsWith('#/funding-') ? <FundingReturn key={path} cancelled={route === '#/funding-cancel'} /> : route === '#/create' ? <ProjectForm done={id => { window.location.hash = `/projects/${id}`; }} /> : maintainer ? <Suspense fallback={<p role="status">Loading maintainer profile…</p>}><MaintainerProfile key={maintainer[1]} userId={Number(maintainer[1])} /></Suspense> : expense ? <PublicExpensePage projectId={Number(expense[1])} expenseId={Number(expense[2])} /> : match ? <ProjectPage key={`${match[1]}-${user?.id ?? 'public'}`} id={Number(match[1])} /> : route === '#/analytics' ? <section><div className="page-heading"><p className="eyebrow">THE BIGGER PICTURE</p><h1>Clarity in every contribution.</h1><p className="muted">Select an active project to inspect its public financial and development records.</p></div><ProjectList analytics /></section> : <ProjectList key={`${route}-${user?.id ?? 'public'}`} mine={route === '#/my'} />}
    </main>
    <footer className="site-footer"><div><a href="#/explore" className="brand"><span className="brand-mark"><Icon name="code" /></span>OpenDev<span className="brand-dot">.</span></a><p>Open source. Open books. A better way forward.</p></div><div><span className="sandbox-label"><span />PAYPAL SANDBOX</span><p>Demo payments only. No real funds are collected.</p><a href="https://github.com/Avnish666/OpenDev" target="_blank" rel="noreferrer">Built in the open ↗</a></div></footer>
  </div>;
}

import { FundingHistory, FundingReturn } from './pages/Funding';
import { useEffect, useState } from 'react';
import GitHubLogin from './components/auth/GithubLogin';
import { useAuth } from './context/AuthContext';
import { ProjectForm, ProjectList, ProjectPage } from './pages/Projects';
import './App.css';

export default function App() {
  const [path, setPath] = useState(window.location.hash || '#/explore');
  const { user, loading } = useAuth();
  useEffect(() => { const change = () => setPath(window.location.hash || '#/explore'); window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change); }, []);
  const match = path.match(/^#\/projects\/(\d+)$/);
  return <main><header><h1>Open Source Funding</h1><p>Fund open source. Reward backers. Prove progress.</p><nav><a href="#/explore">Explore Projects</a><a href="#/my">My Projects</a><a href="#/create">Create Project</a><a href="#/history">My Funding & Rewards</a></nav><GitHubLogin /></header>
    {loading ? <p role="status">Checking session…</p> : (path === '#/my' || path === '#/create' || path === '#/history' || path.startsWith('#/funding-')) && !user ? <p>Sign in with GitHub to manage projects.</p> : path === '#/history' ? <FundingHistory /> : path.startsWith('#/funding-') ? <FundingReturn key={path} cancelled={path === '#/funding-cancel'} /> : path === '#/create' ? <ProjectForm done={id => { window.location.hash = `/projects/${id}`; }} /> : match ? <ProjectPage key={`${match[1]}-${user?.id ?? 'public'}`} id={Number(match[1])} /> : <ProjectList key={`${path}-${user?.id ?? 'public'}`} mine={path === '#/my'} />}
  </main>;
}

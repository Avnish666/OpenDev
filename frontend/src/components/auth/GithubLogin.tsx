import { useAuth } from '../../context/AuthContext';
import Icon from '../Icon';

export default function GitHubLogin() {
  const { user, loading, error, login, logout } = useAuth();
  if (loading) return <span className="muted" role="status">Checking authentication…</span>;
  if (!user) return <div className="auth-control"><button className="auth-login secondary" onClick={login}><Icon name="github" size={18} /><span>Sign in with GitHub</span></button>{error && <span className="auth-error" role="alert">{error}</span>}</div>;
  return <details className="account-menu"><summary>{user.avatar_url ? <img src={user.avatar_url} alt="" width={32} height={32} referrerPolicy="no-referrer" /> : <span className="avatar-fallback">{user.username[0]}</span>}<span>{user.username}</span><span aria-hidden="true">⌄</span></summary><div className="account-dropdown"><strong>{user.username}</strong><a href={`#/maintainers/${user.id}`}>Public profile</a><a href="#/my">My projects</a><a href="#/history">Funding & rewards</a><button className="secondary" onClick={() => { void logout().catch(console.error); }}>Log out</button></div></details>;
}

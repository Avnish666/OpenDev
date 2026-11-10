import Icon from './Icon';
import { StatusBadge } from './UI';

type DirectoryProject = { id: number; title: string; description: string; github_repo_url: string; funding_goal_cents: number; currency: string; status: string; owner_id: number };

/** Uses only directory fields. No inferred funding, verification or maintainer identity. */
export default function ProjectListing({ project: p, featured = false, analytics = false }: { project: DirectoryProject; featured?: boolean; analytics?: boolean }) {
  const href = `#/projects/${p.id}${analytics ? '/analytics' : ''}`;
  const repo = p.github_repo_url?.replace('https://github.com/', '') ?? '';
  return <article className={`project-card directory-record${featured ? ' directory-featured' : ''}`}>
    <div className="directory-identity">{featured && <p className="directory-caption">From the public directory</p>}<div className="directory-title"><h3><a href={href}>{p.title}</a></h3><StatusBadge status={p.status} /></div><p className="card-description">{p.description}</p>{p.github_repo_url ? <a className="repo-link" href={p.github_repo_url} target="_blank" rel="noreferrer"><Icon name="github" size={15} />{repo}<Icon name="arrow" size={12} /></a> : <span className="muted">Repository unavailable</span>}</div>
    <dl className="directory-facts"><div><dt>Repository owner</dt><dd>{p.github_repo_url ? repo.split('/')[0] : 'Unavailable'}</dd></div><div><dt>Funding goal</dt><dd className="directory-goal">{new Intl.NumberFormat(undefined, { style: 'currency', currency: p.currency }).format(p.funding_goal_cents / 100)}</dd></div></dl>
    <a className="card-action" href={href}>{analytics ? 'View analytics' : 'Explore project'}<Icon name="arrow" size={18} /></a>
  </article>;
}

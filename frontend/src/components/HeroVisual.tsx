import Icon from './Icon';

/** Original, data-free product illustration. All numbers are workflow steps. */
export default function HeroVisual() {
  return <div className="hero-art workflow-art" role="img" aria-label="Illustrative OpenDev workflow: back a project, follow development milestones, and inspect public spending and progress. No live financial data.">
    <div className="workflow-orbit orbit-one" /><div className="workflow-orbit orbit-two" />
    <div className="workflow-topline"><span className="workflow-brand"><Icon name="code" size={18} />THE OPENDEV WAY</span><span className="workflow-live"><span />BUILT IN THE OPEN</span></div>
    <div className="workflow-project"><div className="workflow-project-icon"><Icon name="code" size={28} /></div><div><small>FROM A REPOSITORY</small><strong>To something worth backing.</strong><span>Good ideas deserve a way forward.</span></div><Icon name="arrow" size={24} /></div>
    <div className="workflow-stages">
      <div className="workflow-stage"><span className="workflow-step-number">01</span><div className="workflow-stage-icon"><Icon name="wallet" size={23} /></div><strong>Fund the work</strong><p>Support a project<br />through Sandbox.</p></div>
      <div className="workflow-stage"><span className="workflow-step-number">02</span><div className="workflow-stage-icon"><Icon name="timeline" size={23} /></div><strong>Follow the build</strong><p>See milestones<br />connected to GitHub.</p></div>
      <div className="workflow-stage"><span className="workflow-step-number">03</span><div className="workflow-stage-icon"><Icon name="shield" size={23} /></div><strong>See the evidence</strong><p>Inspect reported spending<br />and public progress.</p></div>
    </div>
    <div className="workflow-bottom"><span><Icon name="check" size={16} />A clearer connection between funding and progress.</span><small>WORKFLOW ILLUSTRATION</small></div>
  </div>;
}

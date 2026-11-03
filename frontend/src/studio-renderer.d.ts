declare module '@opendev/studio-renderer' {
 import type { ComponentType } from 'react';
 const Renderer: ComponentType<{data:import('./api/analytics').AnalyticsOverview;view?:'financial'|'development'}>;
 export default Renderer;
}

declare module '@opendev/studio-renderer' {
 import type { ComponentType } from 'react';
 const Renderer: ComponentType<{data:import('./api/analytics').AnalyticsOverview}>;
 export default Renderer;
}
